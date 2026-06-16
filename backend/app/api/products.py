import sys
sys.path.insert(0, "/opt/woommo/logic")

import requests as _req
from requests.auth import HTTPBasicAuth
from fastapi import APIRouter, Depends, Query
from app.models.database import User, get_db
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.config import WC_URL, WC_USERNAME, WC_APP_PASSWORD
from woocommerce_api import WooCommerceAPI

router = APIRouter(prefix="/api/products", tags=["products"])


def _get_wc_config(user: User, store_id: int = 0):
    from app.models.database import SessionLocal, UserStore, Store as StoreModel
    db = SessionLocal()
    try:
        target_store = None
        wp_user = ""
        wp_pass = ""
        print(f"[DEBUG _get_wc_config] user_id={user.id} store_id={store_id}")
        if store_id > 0:
            us = db.query(UserStore).filter_by(user_id=user.id, store_id=store_id).first()
            if us:
                target_store = us.store
                wp_user = us.wp_username or us.store.wp_username or WC_USERNAME
                wp_pass = us.wp_app_password or us.store.wp_app_password or WC_APP_PASSWORD
            else:
                target_store = db.query(StoreModel).filter_by(id=store_id).first()
                if target_store:
                    wp_user = target_store.wp_username or WC_USERNAME
                    wp_pass = target_store.wp_app_password or WC_APP_PASSWORD
        if not target_store and user.store:
            target_store = user.store
            wp_user = user.wp_username or user.store.wp_username or WC_USERNAME
            wp_pass = user.wp_app_password or user.store.wp_app_password or WC_APP_PASSWORD
        if not target_store:
            return WC_URL, WC_USERNAME, WC_APP_PASSWORD
        return target_store.wc_url, wp_user, wp_pass
    finally:
        db.close()


def _get_api(user: User):
    wc_url, wp_user, wp_pass = _get_wc_config(user)
    return WooCommerceAPI(wc_url, wp_user, wp_pass)


def _build_product_url(p: dict, store_url: str) -> str:
    import re
    base = store_url.rstrip("/")
    slug = p.get("slug", "").strip()
    if slug: return f"{base}/product/{slug}/"
    gen = p.get("generated_slug", "").strip()
    if gen: return f"{base}/product/{gen}/"
    link = p.get("permalink", "").strip()
    if link and "?" not in link: return link
    name = p.get("name", "")
    if name:
        s = name.lower().strip()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"\s+", "-", s).strip("-")
        if s: return f"{base}/product/{s}/"
    pid = p.get("id")
    if pid: return f"{base}/?p={pid}"
    return ""


@router.get("/")
def list_products(
    page:     int = Query(1, ge=1),
    per_page: int = Query(50, le=100),
    search:   str = Query(""),
    status:   str = Query("any"),
    store_id: int = Query(0),
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    wc_url, wp_u, wp_p = _get_wc_config(user, store_id)
    print(f"[DEBUG list_products] wc_url={wc_url} wp_user={wp_u}")
    api = WooCommerceAPI(wc_url, wp_u, wp_p)
    result = api.get_products(page=page, per_page=per_page, status=status, search=search)
    if not result.get("success"):
        return {"products": [], "total": 0, "error": result.get("error")}
    products = []
    for p in result["products"]:
        slug = p.get("slug", "").strip()
        url  = f"{wc_url.rstrip('/')}/product/{slug}/" if slug else ""
        products.append({
            "id":       p.get("id"),
            "name":     p.get("name"),
            "status":   p.get("status"),
            "has_desc": len((p.get("description") or "").strip()) > 100,
            "url":      url,
        })
    return {"products": products, "total": result.get("total", 0)}


@router.get("/categories")
def list_categories(
    store_id: int = Query(0),
    db: Session   = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    wc_url, wp_user, wp_pass = _get_wc_config(user, store_id)
    print(f"[DEBUG categories] user={user.username} wc_url={wc_url}")
    api = WooCommerceAPI(wc_url, wp_user, wp_pass)
    all_cats = []
    page = 1
    while True:
        result = api.get_categories(per_page=100, page=page)
        if not result.get("success"): break
        batch = result["categories"]
        if not batch: break
        all_cats.extend(batch)
        if len(batch) < 100: break
        page += 1

    wp_cats = {}

    # Lấy URL thật từ WP REST API (1 request duy nhất)
    wp_cat_urls = {}
    try:
        auth = HTTPBasicAuth(wp_user, wp_pass)
        r = _req.get(
            f"{wc_url.rstrip('/')}/wp-json/wp/v2/product_cat",
            auth=auth, params={"per_page": 100}, timeout=10
        )
        if r.status_code == 200:
            for c in r.json():
                wp_cat_urls[c["id"]] = c.get("link", "")
    except Exception:
        pass

    result_cats = []
    for c in all_cats:
        slug = c.get("slug", "")
        # Lấy URL thật qua WP REST API /wp-json/wp/v2/product_cat
        cat_url = wp_cat_urls.get(c.get("id"), f"{wc_url.rstrip('/')}/product-category/{slug}/")
        result_cats.append({
            "id":     c.get("id"),
            "name":   c.get("name"),
            "slug":   slug,
            "parent": c.get("parent", 0),
            "count":  c.get("count", 0),
            "url":    cat_url,
        })
    return result_cats


@router.get("/brands")
def list_brands(
    store_id: int = Query(0),
    db: Session   = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    wc_url, wp_user, wp_pass = _get_wc_config(user, store_id)
    auth = HTTPBasicAuth(wp_user, wp_pass)
    all_brands = []
    page = 1
    while True:
        try:
            r = _req.get(
                f"{wc_url.rstrip('/')}/wp-json/wp/v2/pwb-brand",
                auth=auth, params={"per_page": 100, "page": page}, timeout=10
            )
            if r.status_code != 200: break
            batch = r.json()
            if not batch: break
            all_brands.extend(batch)
            if len(batch) < 100: break
            page += 1
        except Exception:
            break
    return [{"id": b["id"], "name": b["name"], "slug": b["slug"]} for b in all_brands]


@router.get("/wcpa-forms")
def list_wcpa_forms(
    store_id: int = Query(0),
    db: Session   = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    wc_url, wp_user, wp_pass = _get_wc_config(user, store_id)
    auth = HTTPBasicAuth(wp_user, wp_pass)
    try:
        r = _req.get(
            f"{wc_url.rstrip('/')}/wp-json/woommo/v1/wcpa-forms",
            auth=auth, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            forms = data.get('forms', data) if isinstance(data, dict) else data
            print(f"[WCPA] Loaded {len(forms)} forms via woommo/v1/wcpa-forms")
            return forms
    except Exception:
        pass
    return []

@router.get("/review-counts")
def get_review_counts(
    ids:      str = Query(""),
    store_id: int = Query(0),
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    if not ids:
        return {}
    wc_url, wp_user, wp_pass = _get_wc_config(user, store_id)
    import requests as _req
    from requests.auth import HTTPBasicAuth
    auth = HTTPBasicAuth(wp_user, wp_pass)
    id_list = [i.strip() for i in ids.split(',') if i.strip()]
    result = {}
    try:
        r = _req.get(
            f"{wc_url.rstrip('/')}/wp-json/wc/v3/products/reviews",
            auth=auth,
            params={"per_page": 100, "product": ','.join(id_list)},
            timeout=10,
        )
        if r.status_code == 200:
            reviews = r.json()
            for rev in reviews:
                pid = str(rev.get("product_id", ""))
                result[pid] = result.get(pid, 0) + 1
    except Exception:
        pass
    return result

@router.get("/review-counts")
def get_review_counts(
    ids:      str = Query(""),
    store_id: int = Query(0),
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    if not ids:
        return {}
    wc_url, wp_user, wp_pass = _get_wc_config(user, store_id)
    import requests as _req
    from requests.auth import HTTPBasicAuth
    auth = HTTPBasicAuth(wp_user, wp_pass)
    id_list = [i.strip() for i in ids.split(',') if i.strip()]
    result = {}
    try:
        r = _req.get(
            f"{wc_url.rstrip('/')}/wp-json/wc/v3/products/reviews",
            auth=auth,
            params={"per_page": 100, "product": ','.join(id_list)},
            timeout=10,
        )
        if r.status_code == 200:
            reviews = r.json()
            for rev in reviews:
                pid = str(rev.get("product_id", ""))
                result[pid] = result.get(pid, 0) + 1
    except Exception:
        pass
    return result

@router.get("/export-urls")
def export_urls(
    store_id:    int = Query(0),
    status:      str = Query("publish"),
    date_after:  str = Query(""),
    date_before: str = Query(""),
    target_user_id: int = Query(0),
    db: Session  = Depends(get_db),
    user: User   = Depends(get_current_user),
):
    import requests as _req
    from requests.auth import HTTPBasicAuth

    wc_url, wp_user, wp_pass = _get_wc_config(user, store_id)
    auth = HTTPBasicAuth(wp_user, wp_pass)
    all_urls = []
    page = 1

    while True:
        params = {k: v for k, v in {
            "page":     page,
            "per_page": 100,
            "status":   status,
            "orderby":  "date",
            "order":    "desc",
            "context":  "edit",
            "after":    (date_after + "T00:00:00+07:00") if date_after else None,
            "before":   (date_before + "T23:59:59+07:00") if date_before else None,
            "author":   target_user_id if (user.is_admin and target_user_id) else None,
        }.items() if v is not None}

        r = _req.get(
            f"{wc_url.rstrip('/')}/wp-json/wc/v3/products",
            auth=auth, params=params, timeout=30,
        )
        if r.status_code != 200:
            break

        products = r.json()
        if not products:
            break

        for p in products:
            permalink = p.get("permalink") or p.get("link", "")
            if not permalink:
                slug = p.get("slug", "")
                if slug:
                    permalink = f"{wc_url.rstrip('/')}/product/{slug}/"
            if permalink:
                all_urls.append(permalink.rstrip("/") + "/")

        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1

    return {"urls": all_urls, "total": len(all_urls)}

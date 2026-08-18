"""
WooMMO All-in-One — WooCommerce API
Dùng WordPress Application Password (Basic Auth) thay Consumer Key/Secret
"""

import requests
from requests.auth import HTTPBasicAuth


class WooCommerceAPI:
    """WooCommerce REST API wrapper dùng Basic Auth (WP Application Password)"""

    def __init__(self, url: str, username: str, app_password: str):
        self.url          = url.rstrip("/")
        self.username     = username
        self.app_password = app_password.replace(" ", "")   # strip spaces WP adds
        self._auth        = HTTPBasicAuth(self.username, self.app_password)
        self._wc_base     = f"{self.url}/wp-json/wc/v3"
        self._wp_base     = f"{self.url}/wp-json/wp/v2"
        # Warn nếu dùng HTTP — credentials sẽ đi plain text
        if self.url.startswith("http://"):
            import warnings
            warnings.warn(
                f"⚠️ Store URL dùng HTTP ({self.url}) — Application Password sẽ gửi plain text. "
                "Nên dùng HTTPS để bảo mật.",
                UserWarning, stacklevel=2
            )

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict = None) -> dict:
        r = requests.get(
            f"{self._wc_base}/{endpoint.lstrip('/')}",
            auth=self._auth, params=params, timeout=60
        )
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, data: dict) -> dict:
        r = requests.post(
            f"{self._wc_base}/{endpoint.lstrip('/')}",
            auth=self._auth, json=data, timeout=60
        )
        r.raise_for_status()
        return r.json()

    def _put(self, endpoint: str, data: dict) -> dict:
        r = requests.put(
            f"{self._wc_base}/{endpoint.lstrip('/')}",
            auth=self._auth, json=data, timeout=60
        )
        r.raise_for_status()
        return r.json()

    def _delete(self, endpoint: str, params: dict = None) -> dict:
        r = requests.delete(
            f"{self._wc_base}/{endpoint.lstrip('/')}",
            auth=self._auth, params=params, timeout=60
        )
        r.raise_for_status()
        return r.json()

    # ── Auth / Connection ──────────────────────────────────────────────────────

    def test_connection(self) -> dict:
        """
        Verify credentials via wp/v2/users/me
        Returns: {"success": True, "user": {...}} or {"success": False, "error": "..."}
        """
        try:
            r = requests.get(
                f"{self._wp_base}/users/me",
                auth=self._auth, timeout=60
            )
            if r.status_code == 200:
                user = r.json()
                return {
                    "success":      True,
                    "user_id":      user.get("id"),
                    "display_name": user.get("name", ""),
                    "email":        user.get("slug", ""),
                    "roles":        user.get("roles", []),
                }
            elif r.status_code == 401:
                return {"success": False, "error": "Sai username hoặc Application Password"}
            elif r.status_code == 403:
                return {"success": False, "error": "Tài khoản không có quyền truy cập REST API"}
            else:
                return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Không kết nối được tới {self.url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Products ───────────────────────────────────────────────────────────────

    def get_products(self, page: int = 1, per_page: int = 100,
                     status: str = "any", search: str = "",
                     context: str = "edit") -> dict:
        import time
        params = {"page": page, "per_page": per_page, "status": status,
                  "context": context, "_": int(time.time())}
        if search:
            params["search"] = search
        try:
            r = requests.get(
                f"{self._wc_base}/products",
                auth=self._auth, params=params, timeout=60
            )
            r.raise_for_status()
            return {
                "success":     True,
                "products":    r.json(),
                "total":       int(r.headers.get("X-WP-Total", 0)),
                "total_pages": int(r.headers.get("X-WP-TotalPages", 0)),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_products(self, status: str = "any") -> list:
        """
        Fetch tất cả sản phẩm với tối ưu tốc độ:
        - Lấy page 1 trước để biết total_pages
        - Fetch các page còn lại song song (ThreadPoolExecutor)
        - Chỉ lấy fields cần thiết (giảm payload ~80%)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Chỉ lấy fields cần thiết cho SEO tab
        # description: WC trả về full HTML — dùng để check has_description
        FIELDS = "id,name,description,status,categories,images"

        def fetch_page(page: int) -> list:
            try:
                r = requests.get(
                    f"{self._wc_base}/products",
                    auth=self._auth,
                    params={
                        "page":      page,
                        "per_page":  100,
                        "status":    status,
                        "_fields":   FIELDS,
                    },
                    timeout=60,
                )
                r.raise_for_status()
                return r.json()
            except Exception as e:
                print(f"[Products] Page {page} error: {e}")
                return []

        # ── Bước 1: Fetch page 1 để biết total_pages ──────────────────────────
        try:
            r1 = requests.get(
                f"{self._wc_base}/products",
                auth=self._auth,
                params={"page": 1, "per_page": 100,
                        "status": status, "_fields": FIELDS},
                timeout=60,
            )
            r1.raise_for_status()
            total_pages = int(r1.headers.get("X-WP-TotalPages", 1))
            all_products = r1.json()
        except Exception as e:
            print(f"[Products] Page 1 error: {e}")
            return []

        if total_pages <= 1:
            return all_products

        # ── Bước 2: Fetch các page còn lại song song ──────────────────────────
        # Tối đa 5 request đồng thời để không overload server
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_page, page): page
                for page in range(2, total_pages + 1)
            }
            for future in as_completed(futures):
                batch = future.result()
                if batch:
                    all_products.extend(batch)

        return all_products

    def get_products_by_ids(self, ids: list, status: str = "any") -> list:
        """
        Fetch đúng danh sách sản phẩm theo product ID (dùng cho Bulk SEO khi
        user chỉ chọn 1 vài sản phẩm — nhanh hơn get_all_products() + filter).
        WooCommerce giới hạn include= tối đa ~100 ID/request nên tự chia batch.
        """
        if not ids:
            return []

        FIELDS = "id,name,description,status,categories,images"
        products = []
        seen_ids = set()

        for i in range(0, len(ids), 100):
            batch = ids[i:i + 100]
            try:
                r = requests.get(
                    f"{self._wc_base}/products",
                    auth=self._auth,
                    params={
                        "include":  ",".join(str(x) for x in batch),
                        "per_page": len(batch),
                        "status":   status,
                        "_fields":  FIELDS,
                    },
                    timeout=60,
                )
                r.raise_for_status()
                for p in r.json():
                    pid = p.get("id")
                    if pid is not None and pid not in seen_ids:
                        seen_ids.add(pid)
                        products.append(p)
            except Exception as e:
                print(f"[Products] get_products_by_ids batch {batch}: {e}")

        return products

    def fetch_existing_slugs(self, progress_fn=None) -> dict:
        """
        Fetch toàn bộ sản phẩm (chỉ lấy id, name, slug) để check duplicate trước upload.
        Trả về:
          {
            "slugs":  set[str],          # tất cả slug đang có
            "titles": set[str],          # tất cả title.lower() đang có
            "count":  int,               # tổng số sản phẩm
          }
        progress_fn: callable(msg: str) — optional callback log tiến trình
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        FIELDS = "id,name,slug"

        def _log(msg):
            if progress_fn:
                progress_fn(msg)

        def fetch_page(page: int) -> list:
            try:
                r = requests.get(
                    f"{self._wc_base}/products",
                    auth=self._auth,
                    params={"page": page, "per_page": 100,
                            "status": "any", "_fields": FIELDS},
                    timeout=60,
                )
                r.raise_for_status()
                return r.json()
            except Exception as e:
                _log(f"  ⚠ Page {page} error: {e}")
                return []

        # Page 1 — lấy total_pages
        try:
            r1 = requests.get(
                f"{self._wc_base}/products",
                auth=self._auth,
                params={"page": 1, "per_page": 100,
                        "status": "any", "_fields": FIELDS},
                timeout=60,
            )
            r1.raise_for_status()
            total_pages   = int(r1.headers.get("X-WP-TotalPages", 1))
            total_count   = int(r1.headers.get("X-WP-Total", 0))
            all_products  = r1.json()
            _log(f"  📦 Tổng sản phẩm hiện có: {total_count} ({total_pages} trang)")
        except Exception as e:
            _log(f"  ✗ Không fetch được danh sách sản phẩm: {e}")
            return {"slugs": set(), "titles": set(), "count": 0}

        # Fetch song song các trang còn lại
        if total_pages > 1:
            with ThreadPoolExecutor(max_workers=5) as ex:
                futures = {ex.submit(fetch_page, p): p for p in range(2, total_pages + 1)}
                for fut in as_completed(futures):
                    batch = fut.result()
                    if batch:
                        all_products.extend(batch)

        existing_slugs  = {p.get("slug", "").strip().lower() for p in all_products if p.get("slug")}
        existing_titles = {p.get("name", "").strip().lower() for p in all_products if p.get("name")}

        return {
            "slugs":  existing_slugs,
            "titles": existing_titles,
            "count":  len(all_products),
        }


    def check_slug_exists(self, slug: str) -> bool:
        """Check real-time xem slug da ton tai tren store chua."""
        try:
            r = requests.get(
                f"{self._wc_base}/products",
                auth=self._auth,
                params={"slug": slug, "_fields": "id,slug", "per_page": 1},
                timeout=15,
            )
            r.raise_for_status()
            return len(r.json()) > 0
        except Exception:
            return False

    def create_product(self, product_data: dict) -> dict:
        import time
        last_error = ""
        for attempt in range(3):
            try:
                r = requests.post(
                    f"{self._wc_base}/products",
                    auth=self._auth, json=product_data, timeout=60
                )
                r.raise_for_status()
                return {"success": True, "product": r.json()}
            except requests.exceptions.HTTPError as e:
                try:
                    err = e.response.json()
                    last_error = err.get("message", str(e))
                except Exception:
                    last_error = e.response.text[:200] if hasattr(e, 'response') and e.response else str(e)
                print(f"[create_product] attempt={attempt} error={last_error} status={e.response.status_code if hasattr(e,'response') and e.response else 'N/A'}")
                # Không retry nếu lỗi business logic (slug trùng, thiếu field...)
                if "already exists" in last_error or "required" in last_error.lower():
                    return {"success": False, "error": last_error}
            except Exception as e:
                last_error = str(e)
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
        return {"success": False, "error": last_error}

    def create_product_variations_batch(self, product_id: int, variations: list) -> dict:
        """
        Tạo nhiều variation cùng lúc qua WooCommerce REST API:
        POST /products/{id}/variations/batch  { "create": [...] }
        Returns {"success": True, "created": [...], "errors": [...]}
        """
        import time
        last_error = ""
        for attempt in range(3):
            try:
                r = requests.post(
                    f"{self._wc_base}/products/{product_id}/variations/batch",
                    auth=self._auth, json={"create": variations}, timeout=90
                )
                r.raise_for_status()
                data = r.json()
                created = data.get("create", [])
                errors  = [c for c in created if c.get("error")]
                return {"success": True, "created": created, "errors": errors}
            except requests.exceptions.HTTPError as e:
                try:
                    err = e.response.json()
                    last_error = err.get("message", str(e))
                except Exception:
                    last_error = e.response.text[:200] if hasattr(e, 'response') and e.response else str(e)
                print(f"[create_product_variations_batch] attempt={attempt} error={last_error}")
            except Exception as e:
                last_error = str(e)
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
        return {"success": False, "error": last_error, "created": [], "errors": []}

    def update_product(self, product_id: int, data: dict) -> dict:
        try:
            r = requests.put(
                f"{self._wc_base}/products/{product_id}",
                auth=self._auth, json=data, timeout=60
            )
            r.raise_for_status()
            return {"success": True, "product": r.json()}
        except requests.exceptions.HTTPError as e:
            try:
                msg = e.response.json().get("message", str(e))
            except Exception:
                msg = str(e)
            status = e.response.status_code if hasattr(e, "response") and e.response else "N/A"
            print("[upload_media ERROR] status=" + str(status) + " msg=" + str(msg) + " file=" + str(file_path))
            return {"success": False, "error": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_product(self, product_id: int, force: bool = False) -> dict:
        try:
            r = requests.delete(
                f"{self._wc_base}/products/{product_id}",
                auth=self._auth, params={"force": force}, timeout=60
            )
            r.raise_for_status()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Categories ─────────────────────────────────────────────────────────────

    def get_product(self, product_id: int) -> dict:
        """Lấy 1 sản phẩm theo ID."""
        try:
            import requests as _req
            r = _req.get(
                f"{self._wc_base}/products/{product_id}",
                auth=self._auth,
                params={"context": "edit"},
                timeout=20,
            )
            r.raise_for_status()
            return {"success": True, "product": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_categories(self, per_page: int = 100, page: int = 1) -> dict:
        try:
            r = requests.get(
                f"{self._wc_base}/products/categories",
                auth=self._auth,
                params={"per_page": per_page, "page": page, "hide_empty": False},
                timeout=20
            )
            r.raise_for_status()
            total_pages = int(r.headers.get("X-WP-TotalPages", 1))
            return {"success": True, "categories": r.json(), "total_pages": total_pages}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_category(self, name: str, parent: int = 0, description: str = "") -> dict:
        try:
            r = requests.post(
                f"{self._wc_base}/products/categories",
                auth=self._auth,
                json={"name": name, "parent": parent, "description": description},
                timeout=20
            )
            r.raise_for_status()
            return {"success": True, "category": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Media upload (via WP REST API) ─────────────────────────────────────────

    def upload_media(self, file_path: str, alt_text: str = "") -> dict:
        """
        Upload ảnh qua WP REST API /wp/v2/media (Basic Auth).
        Trả về {"success": True, "media_id": int, "url": str}
        """
        import os
        import mimetypes

        filename     = os.path.basename(file_path)
        content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            r = requests.post(
                f"{self._wp_base}/media",
                auth=self._auth,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Type":        content_type,
                },
                data=file_data,
                timeout=120,
            )
            r.raise_for_status()
            media = r.json()

            # Optionally set alt text
            if alt_text and media.get("id"):
                requests.post(
                    f"{self._wp_base}/media/{media['id']}",
                    auth=self._auth,
                    json={"alt_text": alt_text},
                    timeout=60,
                )

            return {
                "success":  True,
                "media_id": media["id"],
                "url":      media.get("source_url", ""),
            }
        except requests.exceptions.HTTPError as e:
            try:
                msg = e.response.json().get("message", str(e))
            except Exception:
                msg = str(e)
            return {"success": False, "error": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── WCPA Forms ─────────────────────────────────────────────────────────────

    def get_wcpa_forms(self) -> dict:
        """
        Fetch WCPA forms — thử nhiều chiến lược vì WCPA Pro không luôn
        expose REST API. Thứ tự ưu tiên:
          1. WooMMO custom endpoint (woommo/v1/wcpa-forms) — do plugin của chúng ta
          2. WP REST API wp/v2/wcpa_pt_forms (nếu plugin bật show_in_rest)
          3. WP REST API wp/v2/posts?post_type=wcpa_pt_forms (fallback WP query)
          4. Trả về danh sách rỗng (không crash)
        """
        forms = []

        # ── Strategy 1: WooMMO plugin endpoint ────────────────────────────────
        try:
            r = requests.get(
                f"{self.url}/wp-json/woommo/v1/wcpa-forms",
                auth=self._auth, timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                forms = data.get("forms", [])
                if forms:
                    print(f"[WCPA] Loaded {len(forms)} forms via woommo/v1/wcpa-forms")
                    return {"success": True, "forms": forms}
        except Exception as e:
            print(f"[WCPA] Strategy 1 failed: {e}")

        # ── Strategy 2: wp/v2/wcpa_pt_forms (cần show_in_rest=true) ──────────
        try:
            r = requests.get(
                f"{self.url}/wp-json/wp/v2/wcpa_pt_forms",
                auth=self._auth,
                params={"per_page": 100, "status": "publish"},
                timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    for item in data:
                        fid   = item.get("id")
                        title = item.get("title", {})
                        if isinstance(title, dict):
                            title = title.get("rendered", "")
                        if fid and title:
                            forms.append({"id": int(fid), "title": str(title)})
                if forms:
                    print(f"[WCPA] Loaded {len(forms)} forms via wp/v2/wcpa_pt_forms")
                    return {"success": True, "forms": forms}
        except Exception as e:
            print(f"[WCPA] Strategy 2 failed: {e}")

        # ── Strategy 3: WP REST search posts by post_type ─────────────────────
        try:
            r = requests.get(
                f"{self.url}/wp-json/wp/v2/posts",
                auth=self._auth,
                params={"post_type": "wcpa_pt_forms", "per_page": 100, "status": "any"},
                timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    for item in data:
                        fid   = item.get("id")
                        title = item.get("title", {})
                        if isinstance(title, dict):
                            title = title.get("rendered", "")
                        if fid and title:
                            forms.append({"id": int(fid), "title": str(title)})
                if forms:
                    print(f"[WCPA] Loaded {len(forms)} forms via wp/v2/posts?post_type")
                    return {"success": True, "forms": forms}
        except Exception as e:
            print(f"[WCPA] Strategy 3 failed: {e}")

        print("[WCPA] No forms found — returning empty list")
        return {"success": True, "forms": []}

    # ── Brand ──────────────────────────────────────────────────────────────────

    # Thứ tự ưu tiên: pwb-brand trước vì đây là slug của Perfect WooCommerce Brands
    BRAND_TAXONOMY_SLUGS = [
        "pwb-brand",            # Perfect WooCommerce Brands (PWB) ← phổ biến nhất
        "product_brand",        # WooCommerce Brands (official)
        "yith_product_brand",   # YITH WooCommerce Brands
        "brand",                # Generic / một số theme
        "product-brand",        # Một số theme khác
    ]

    def detect_brand_taxonomy(self) -> str | None:
        """
        Tự detect taxonomy slug của Brand plugin đang dùng.
        Thử lần lượt, trả về slug đầu tiên phản hồi 200.
        """
        for slug in self.BRAND_TAXONOMY_SLUGS:
            try:
                r = requests.get(
                    f"{self.url}/wp-json/wp/v2/{slug}",
                    auth=self._auth,
                    params={"per_page": 1},
                    timeout=10
                )
                if r.status_code == 200 and isinstance(r.json(), list):
                    print(f"[Brand] Detected taxonomy slug: '{slug}'")
                    return slug
            except Exception:
                continue
        return None

    def get_brand_id(self, brand_name: str, taxonomy_slug: str) -> int | None:
        """
        Tìm term ID của brand theo tên (so sánh case-insensitive).
        Trả về ID nếu tìm thấy, None nếu không có.
        """
        try:
            r = requests.get(
                f"{self.url}/wp-json/wp/v2/{taxonomy_slug}",
                auth=self._auth,
                params={"search": brand_name, "per_page": 50},
                timeout=60
            )
            if r.status_code == 200:
                for t in r.json():
                    if t.get("name", "").lower().strip() == brand_name.lower().strip():
                        print(f"[Brand] Found '{brand_name}' → ID={t['id']} in '{taxonomy_slug}'")
                        return t["id"]
                # Fallback: tìm theo slug
                for t in r.json():
                    if t.get("slug", "").lower().strip() == brand_name.lower().strip():
                        print(f"[Brand] Found by slug '{brand_name}' → ID={t['id']}")
                        return t["id"]
        except Exception as e:
            print(f"[Brand] get_brand_id error: {e}")
        return None

    def find_brand(self, brand_name: str = "BreakTees") -> dict:
        """
        Tìm brand theo tên trên store hiện tại.
        Tự detect taxonomy, tìm term, trả về kết quả đầy đủ.

        Returns:
          {"found": True,  "taxonomy": str, "brand_id": int, "brand_name": str}
          {"found": False, "reason": str}
        """
        slug = self.detect_brand_taxonomy()
        if not slug:
            return {"found": False, "reason": "Không tìm thấy Brand plugin (pwb-brand, product_brand, ...)"}

        brand_id = self.get_brand_id(brand_name, slug)
        if not brand_id:
            return {
                "found":  False,
                "reason": f"Không tìm thấy brand '{brand_name}' trong taxonomy '{slug}'"
            }

        return {
            "found":      True,
            "taxonomy":   slug,
            "brand_id":   brand_id,
            "brand_name": brand_name,
        }

    # ── WordPress Blog Posts ───────────────────────────────────────────────────

    def get_wp_categories(self, per_page: int = 100) -> dict:
        """
        Lấy WordPress post categories (khác với WooCommerce product categories).
        Endpoint: /wp/v2/categories
        """
        try:
            r = requests.get(
                f"{self._wp_base}/categories",
                auth=self._auth,
                params={"per_page": per_page, "hide_empty": False},
                timeout=20,
            )
            r.raise_for_status()
            return {"success": True, "categories": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_post(self, title: str, content: str,
                    status: str = "draft",
                    featured_media: int = 0,
                    category_ids: list = None,
                    excerpt: str = "",
                    slug: str = "") -> dict:
        """
        Tạo WordPress blog post qua REST API /wp/v2/posts.
        Returns {"success": True, "post": {...}} or {"success": False, "error": "..."}
        """
        payload = {
            "title":   title,
            "content": content,
            "status":  status,
        }
        if featured_media:
            payload["featured_media"] = featured_media
        if category_ids:
            payload["categories"] = category_ids
        if excerpt:
            payload["excerpt"] = excerpt
        if slug:
            payload["slug"] = slug

        try:
            r = requests.post(
                f"{self._wp_base}/posts",
                auth=self._auth,
                json=payload,
                timeout=60,
            )
            r.raise_for_status()
            return {"success": True, "post": r.json()}
        except requests.exceptions.HTTPError as e:
            try:    msg = e.response.json().get("message", str(e))
            except: msg = str(e)
            return {"success": False, "error": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_product_featured_media_id(self, product_id: int) -> int | None:
        """
        Lấy media_id của featured image của 1 sản phẩm WooCommerce.
        Dùng làm fallback featured image cho blog post.
        """
        try:
            r = requests.get(
                f"{self._wc_base}/products/{product_id}",
                auth=self._auth,
                params={"_fields": "images"},
                timeout=60,
            )
            r.raise_for_status()
            images = r.json().get("images", [])
            if images:
                return images[0].get("id")
        except Exception:
            pass
        return None

    def set_rank_math_meta(self, post_id: int,
                            focus_keyword: str = "",
                            meta_desc: str = "") -> bool:
        """
        Set Rank Math SEO fields.
        Rank Math Free lưu data vào wp_postmeta table với các key:
          rank_math_focus_keyword, rank_math_description
        Thử 3 cách theo thứ tự:
          1. rankmath/v1/updateMeta REST endpoint (Rank Math Pro / một số Free versions)
          2. WooMMO plugin custom endpoint (nếu đã cài)
          3. WP update_post_meta qua woommo/v1/set-meta (cần plugin hỗ trợ)
        """
        # ── Cách 1: Rank Math REST endpoint ───────────────────────────────────
        try:
            r = requests.post(
                f"{self.url}/wp-json/rankmath/v1/updateMeta",
                auth=self._auth,
                json={
                    "objectID":   post_id,
                    "objectType": "post",
                    "meta": {
                        "focus_keyword": focus_keyword,
                        "description":   meta_desc,
                    }
                },
                timeout=10,
            )
            print(f"[RankMath] Cách 1 status: {r.status_code} | {r.text[:100]}")
            if r.status_code in (200, 201):
                data = r.json() if r.text else {}
                if data.get("success") or data.get("status") == "success":
                    print(f"[RankMath] ✓ Set via rankmath/v1/updateMeta")
                    return True
        except Exception as e:
            print(f"[RankMath] Cách 1 exception: {e}")

        # ── Cách 2: WooMMO plugin set-meta endpoint ────────────────────────────
        try:
            r = requests.post(
                f"{self.url}/wp-json/woommo/v1/set-post-meta",
                auth=self._auth,
                json={
                    "post_id": post_id,
                    "meta": {
                        "rank_math_focus_keyword": focus_keyword,
                        "rank_math_description":   meta_desc,
                    }
                },
                timeout=10,
            )
            print(f"[RankMath] Cách 2 status: {r.status_code} | {r.text[:100]}")
            if r.status_code in (200, 201):
                print(f"[RankMath] ✓ Set via woommo/v1/set-post-meta")
                return True
        except Exception as e:
            print(f"[RankMath] Cách 2 exception: {e}")

        # ── Cách 3: WP REST meta — hoạt động nếu Rank Math register meta với show_in_rest
        try:
            r = requests.post(
                f"{self._wp_base}/posts/{post_id}",
                auth=self._auth,
                json={
                    "meta": {
                        "rank_math_focus_keyword": focus_keyword,
                        "rank_math_description":   meta_desc,
                    }
                },
                timeout=10,
            )
            print(f"[RankMath] Cách 3 status: {r.status_code} | {r.text[:150]}")
            if r.status_code in (200, 201):
                # Verify meta actually saved by checking response
                resp = r.json()
                saved_meta = resp.get("meta", {})
                if saved_meta.get("rank_math_focus_keyword"):
                    print(f"[RankMath] ✓ Set via WP REST meta (verified)")
                    return True
                else:
                    print(f"[RankMath] ⚠ WP REST accepted but meta not in response — may need plugin update")
        except Exception as e:
            print(f"[RankMath] Cách 3 exception: {e}")

        print(f"[RankMath] ✗ Tất cả cách đều thất bại — cần thêm endpoint vào Plugin WooMMO")
        return False

    def set_post_meta(self, post_id: int, meta: dict) -> bool:
        """
        Update meta fields của một post qua /wp/v2/posts/{id}.
        Dùng để set Fixed TOC meta key sau khi tạo post.
        """
        try:
            r = requests.post(
                f"{self._wp_base}/posts/{post_id}",
                auth=self._auth,
                json={"meta": meta},
                timeout=60,
            )
            return r.status_code in (200, 201)
        except Exception:
            return False

    def set_post_meta_on_media(self, media_id: int, post_id: int) -> bool:
        """
        Gán media attachment vào post bằng cách set post_parent.
        Dùng POST /wp/v2/media/{id} với {"post": post_id}.
        Giống cách attach product images — hiện "Uploaded to [post]" trong Media Library.
        """
        try:
            r = requests.post(
                f"{self._wp_base}/media/{media_id}",
                auth=self._auth,
                json={"post": post_id},
                timeout=60,
            )
            if r.status_code in (200, 201):
                print(f"[Media] ✓ Attached media #{media_id} → post #{post_id}")
                return True
            else:
                print(f"[Media] ✗ media #{media_id}: HTTP {r.status_code}")
                return False
        except Exception as e:
            print(f"[Media] ✗ Exception: {e}")
            return False


    # ── Review methods ─────────────────────────────────────────────────────────

    def get_review_counts(self, product_ids: list) -> dict:
        """
        Lấy số review của danh sách product IDs qua PHP endpoint.
        Trả về dict {product_id_str: count}.
        """
        if not product_ids:
            return {}
        ids_str = ",".join(str(i) for i in product_ids)
        try:
            r = requests.get(
                f"{self.url}/wp-json/woommo/v1/review-counts",
                auth=self._auth,
                params={"product_ids": ids_str},
                timeout=60,
            )
            r.raise_for_status()
            return r.json().get("counts", {})
        except Exception as e:
            print(f"[review_counts] Error: {e}")
            return {}

    def get_product_image_base64(self, product: dict) -> str:
        """
        Lấy feature image của sản phẩm, trả về base64 JPEG string.
        product: dict từ WC API (có 'images' field).
        Trả về "" nếu không lấy được.
        """
        import base64
        images = product.get("images", [])
        if not images:
            return ""
        img_url = images[0].get("src", "")
        if not img_url:
            return ""
        try:
            r = requests.get(img_url, timeout=20)
            r.raise_for_status()
            content_type = r.headers.get("content-type", "image/jpeg")
            if "jpeg" in content_type or "jpg" in content_type:
                mime = "image/jpeg"
            elif "png" in content_type:
                mime = "image/png"
            elif "webp" in content_type:
                mime = "image/webp"
            else:
                mime = "image/jpeg"
            b64 = base64.b64encode(r.content).decode()
            return f"data:{mime};base64,{b64}"
        except Exception as e:
            print(f"[get_image] Error fetching {img_url}: {e}")
            return ""

    def clear_product_cache(self, product_id: int, sale_price: str = None, regular_price: str = None):
        try:
            # Bước 1: Set _price meta trực tiếp qua WP REST API
            price_val = sale_price if sale_price else regular_price
            if price_val:
                wp_url = self.url.rstrip("/") + f"/wp-json/wp/v2/product/{product_id}"
                r1 = requests.post(
                    wp_url, auth=self._auth,
                    json={"meta": {"_price": str(price_val)}},
                    timeout=60,
                )
                print(f"[Cache] ✓ Set _price={price_val} product #{product_id} (HTTP {r1.status_code})")
            # Bước 2: Touch product để clear transient
            requests.put(
                f"{self._wc_base}/products/{product_id}",
                auth=self._auth, json={}, timeout=60,
            )
        except Exception as e:
            print(f"[Cache] ✗ {e}")

    def import_reviews_batch(self, reviews: list) -> dict:
        """
        Gửi batch reviews lên PHP endpoint /woommo/v1/import-reviews.
        reviews: list of dicts với keys: product_id, author, email,
                 author_ip, author_agent, content, title, rating,
                 date, up_votes, down_votes
        Trả về {"success": bool, "inserted": int, "failed": int, "errors": [...]}
        """
        try:
            r = requests.post(
                f"{self.url}/wp-json/woommo/v1/import-reviews",
                auth=self._auth,
                json={"reviews": reviews},
                timeout=120,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"success": False, "inserted": 0, "failed": len(reviews),
                    "errors": [str(e)]}

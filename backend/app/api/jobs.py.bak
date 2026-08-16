import os, json, shutil, uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.models.database import get_db, Job, User
from app.core.auth import get_current_user
from app.core.config import UPLOAD_TMP_DIR, WC_URL, WC_USERNAME, WC_APP_PASSWORD
from app.workers.upload_worker import task_upload_products
from app.workers.seo_worker    import task_seo_bulk
from app.workers.review_worker import task_review_bulk

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _get_wc_config(user: User, store_id: int = 0):
    """
    Ưu tiên: 
    1. user_stores (WP credentials riêng của user cho store đó)
    2. Store credentials (chung)
    3. .env fallback
    """
    from app.models.database import SessionLocal, Store as StoreModel, UserStore

    db = SessionLocal()
    try:
        target_store = None
        wp_user = ""
        wp_pass = ""

        if store_id > 0:
            # Tìm user_store record
            us = db.query(UserStore).filter_by(user_id=user.id, store_id=store_id).first()
            if us:
                target_store = us.store
                wp_user = us.wp_username or us.store.wp_username or WC_USERNAME
                wp_pass = us.wp_app_password or us.store.wp_app_password or WC_APP_PASSWORD
            else:
                # Admin có thể chọn bất kỳ store
                target_store = db.query(StoreModel).filter_by(id=store_id).first()
                if target_store:
                    wp_user = target_store.wp_username or WC_USERNAME
                    wp_pass = target_store.wp_app_password or WC_APP_PASSWORD

        if not target_store:
            # Fallback: lấy store đầu tiên trong user_stores
            first_us = db.query(UserStore).filter_by(user_id=user.id).first()
            if first_us:
                target_store = first_us.store
                wp_user = first_us.wp_username or first_us.store.wp_username or WC_USERNAME
                wp_pass = first_us.wp_app_password or first_us.store.wp_app_password or WC_APP_PASSWORD
            elif user.store:
                target_store = user.store
                wp_user = user.wp_username or user.store.wp_username or WC_USERNAME
                wp_pass = user.wp_app_password or user.store.wp_app_password or WC_APP_PASSWORD
            else:
                return WC_URL, WC_USERNAME, WC_APP_PASSWORD

        return target_store.wc_url, wp_user, wp_pass
    finally:
        db.close()


def _create_job(db, user, job_type, params):
    job = Job(user_id=user.id, job_type=job_type, status="pending",
              params=params, log="", result=None)
    db.add(job); db.commit(); db.refresh(job)
    return job


@router.post("/upload")
async def start_upload(
    file:                UploadFile = File(...),
    store_id:            int  = Form(0),
    status:              str  = Form("draft"),
    sku_mode:            str  = Form("random"),
    regular_price:       str  = Form(""),
    sale_price:          str  = Form(""),
    categories:          str  = Form("[]"),
    wcpa_form_id:        str  = Form(""),
    optimize_images:     bool = Form(False),
    skip_duplicates:     bool = Form(True),
    brand_name:          str  = Form(""),
    primary_category_id: str  = Form(""),
    tags:                str  = Form("[]"),
    brand_id:            str  = Form(""),
    brand_taxonomy:      str  = Form("pwb-brand"),
    pipeline_config:     str  = Form("{}"),
    image_config:        str  = Form("{}"),
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    fname_lower = file.filename.lower()
    if not (fname_lower.endswith(".zip") or fname_lower.endswith(".rar")):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file ZIP hoặc RAR")
    # Admin có thể chọn bất kỳ store, member phải có store được gán
    # Check store qua user_stores hoặc store_id cũ
    from app.models.database import UserStore as _US
    _has_store = user.store or db.query(_US).filter_by(user_id=user.id).first()
    if not user.is_admin and not _has_store:
        raise HTTPException(status_code=400, detail="Tài khoản chưa được gán Store. Liên hệ Admin.")

    ext      = ".rar" if fname_lower.endswith(".rar") else ".zip"
    tmp_path = os.path.join(UPLOAD_TMP_DIR, f"{uuid.uuid4().hex}" + ext)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try: cat_ids = json.loads(categories)
    except: cat_ids = []
    # Đưa primary category lên đầu để WooCommerce hiển thị đúng thứ tự
    if primary_category_id and int(primary_category_id) in cat_ids:
        cat_ids.remove(int(primary_category_id))
        cat_ids.insert(0, int(primary_category_id))

    wc_url, wc_user, wc_pass = _get_wc_config(user, store_id)

    try: pipeline = json.loads(pipeline_config)
    except: pipeline = {}
    try: img_cfg = json.loads(image_config)
    except: img_cfg = {}

    pipeline["user_id"] = user.id
    options = {
        "status": status, "sku_mode": sku_mode,
        "regular_price": regular_price, "sale_price": sale_price,
        "categories": cat_ids, "wcpa_form_id": wcpa_form_id or None,
        "optimize_images": optimize_images, "skip_duplicates": skip_duplicates,
        "primary_category_id": int(primary_category_id) if primary_category_id else None,
        "tags": json.loads(tags) if tags else [],
        "brand_info": {"taxonomy": brand_taxonomy, "brand_id": int(brand_id)} if brand_id else None,
        "pipeline": pipeline, "image_config": img_cfg, "image_processing": img_cfg,
    }

    print(f"[DEBUG] primary_category_id={primary_category_id} options_primary={options.get('primary_category_id')}")
    job = _create_job(db, user, "upload", {"filename": file.filename, "uploader": user.username, "store_id": store_id, "store_url": wc_url})
    task_upload_products.apply_async(args=[job.id, tmp_path, options, wc_url, wc_user, wc_pass], queue="upload")
    return {"job_id": job.id, "ok": True}


@router.post("/seo")
async def start_seo(
    product_ids:   str  = Form("[]"),
    store_id:      int  = Form(0),
    skip_existing: bool = Form(True),
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    # Check store qua user_stores hoặc store_id cũ
    from app.models.database import UserStore as _US
    _has_store = user.store or db.query(_US).filter_by(user_id=user.id).first()
    if not user.is_admin and not _has_store:
        raise HTTPException(status_code=400, detail="Tài khoản chưa được gán Store. Liên hệ Admin.")
    ids = json.loads(product_ids)
    wc_url, wc_user, wc_pass = _get_wc_config(user, store_id)
    job = _create_job(db, user, "seo", {"product_ids": ids, "uploader": user.username, "store_id": store_id, "store_url": wc_url})
    task_seo_bulk.apply_async(args=[job.id, ids, skip_existing, wc_url, wc_user, wc_pass, user.id, store_id], queue="celery")
    return {"job_id": job.id, "ok": True}


@router.post("/review")
async def start_review(
    product_ids: str = Form("[]"),
    store_id:    int = Form(0),
    config:      str = Form("{}"),
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    if not user.is_admin and not user.store:
        raise HTTPException(status_code=400, detail="Tài khoản chưa được gán Store. Liên hệ Admin.")
    ids = json.loads(product_ids)
    cfg = json.loads(config)
    wc_url, wc_user, wc_pass = _get_wc_config(user, store_id)
    job = _create_job(db, user, "review", {"product_ids": ids, "uploader": user.username, "store_id": store_id, "store_url": wc_url})
    review_count     = cfg.get("review_count", 10)
    review_count_min = cfg.get("review_count_min", 5)
    review_count_max = cfg.get("review_count_max", 15)
    start_date       = cfg.get("start_date", "")
    end_date         = cfg.get("end_date", "")
    dist_5           = cfg.get("dist_5", 80)
    dist_4           = cfg.get("dist_4", 15)
    dist_3           = cfg.get("dist_3", 5)
    delay_between    = cfg.get("delay_between", 2.5)
    skip_has_review  = cfg.get("skip_has_review", True)
    task_review_bulk.apply_async(args=[job.id, ids, review_count, review_count_min, review_count_max, start_date, end_date, dist_5, dist_4, dist_3, delay_between, skip_has_review, wc_url, wc_user, wc_pass], queue="celery")
    return {"job_id": job.id, "ok": True}


@router.get("/my")
def my_jobs(job_type: str = None, limit: int = 20,
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Job).filter_by(user_id=user.id).order_by(Job.id.desc())
    if job_type: q = q.filter_by(job_type=job_type)
    return [{"id": j.id, "job_type": j.job_type, "status": j.status,
             "created_at": j.created_at.isoformat(), "log_tail": (j.log or "")[-500:],
             "result": j.result} for j in q.limit(limit).all()]



@router.get("/queue")
def get_queue(
    job_type: str = None,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    q = db.query(Job).filter_by(user_id=user.id).filter(
        Job.status.in_(["pending", "running"])
    ).order_by(Job.id.desc())
    if job_type:
        q = q.filter_by(job_type=job_type)
    jobs = q.all()
    return [{"id": j.id, "job_type": j.job_type, "status": j.status,
             "created_at": j.created_at.isoformat(), "log_tail": (j.log or "")[-200:],
             "result": j.result, "params": j.params} for j in jobs]


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.query(Job).filter_by(id=job_id, user_id=user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.id, "job_type": job.job_type, "status": job.status,
            "log": job.log or "", "result": job.result, "created_at": job.created_at.isoformat()}


@router.delete("/clear-done")
def clear_done_jobs(
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    count = db.query(Job).filter(
        Job.user_id == user.id,
        Job.status.in_(["done", "failed"])
    ).delete(synchronize_session=False)
    db.commit()
    return {"deleted": count}

@router.get("/{job_id}/log")
def get_job_log(job_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"log": job.log or "", "status": job.status, "result": job.result}

@router.get("/{job_id}/status")
def get_job_status(job_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job.status, "result": job.result}

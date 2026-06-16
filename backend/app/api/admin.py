from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.database import get_db, User, Job, Store, UserStore
from app.core.auth import require_admin, hash_password
from app.services.settings_service import get_all_settings, set_setting

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ── Store Management ───────────────────────────────────────────────────────────

class StoreRequest(BaseModel):
    name:            str
    wc_url:          str
    wp_username:     str = ""
    wp_app_password: str = ""
    store_name:      str = ""
    shortcode:       str = "[thien_display_single_image]"

@router.get("/stores")
def list_stores(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stores = db.query(Store).order_by(Store.id).all()
    return [{
        "id":              s.id,
        "name":            s.name,
        "wc_url":          s.wc_url,
        "wp_username":     s.wp_username or "",
        "has_wp_password": bool(s.wp_app_password),
        "store_name":      s.store_name or "",
        "shortcode":       s.shortcode or "",
        "created_at":      s.created_at.isoformat(),
        "user_count":      len(s.users),
    } for s in stores]

@router.post("/stores")
def create_store(req: StoreRequest, db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    if not req.wc_url.startswith("http"):
        raise HTTPException(status_code=400, detail="WC URL không hợp lệ")
    store = Store(
        name            = req.name,
        wc_url          = req.wc_url.rstrip("/"),
        wp_username     = req.wp_username,
        wp_app_password = req.wp_app_password,
        store_name      = req.store_name or req.name,
        shortcode       = req.shortcode,
    )
    db.add(store); db.commit(); db.refresh(store)
    return {"id": store.id, "name": store.name, "ok": True}

@router.put("/stores/{store_id}")
def update_store(store_id: int, req: StoreRequest,
                 db: Session = Depends(get_db), _: User = Depends(require_admin)):
    store = db.query(Store).filter_by(id=store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store không tồn tại")
    store.name        = req.name
    store.wc_url      = req.wc_url.rstrip("/")
    store.wp_username = req.wp_username
    store.store_name  = req.store_name or req.name
    store.shortcode   = req.shortcode
    if req.wp_app_password:
        store.wp_app_password = req.wp_app_password
    db.commit()
    return {"ok": True}

@router.delete("/stores/{store_id}")
def delete_store(store_id: int, db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    store = db.query(Store).filter_by(id=store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store không tồn tại")
    # Xóa user_stores liên quan trước
    db.query(UserStore).filter_by(store_id=store_id).delete(synchronize_session=False)
    # Reset store_id của users dùng store này
    for u in store.users:
        u.store_id = None
    db.delete(store); db.commit()
    return {"ok": True}

# ── User Management ────────────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    username:        str
    email:           str
    password:        str
    is_admin:        bool = False
    store_id:        Optional[int] = None
    wp_username:     str = ""
    wp_app_password: str = ""

class UpdateUserRequest(BaseModel):
    username:        Optional[str]  = None
    email:           Optional[str]  = None
    password:        Optional[str]  = None
    is_active:       Optional[bool] = None
    is_admin:        Optional[bool] = None
    store_id:        Optional[int]  = None
    wp_username:     Optional[str]  = None
    wp_app_password: Optional[str]  = None
    note:            Optional[str]  = None

@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id).all()
    return [{
        "id":              u.id,
        "username":        u.username,
        "email":           u.email,
        "is_admin":        u.is_admin,
        "is_active":       u.is_active,
        "created_at":      u.created_at.isoformat(),
        "store_id":        u.store_id,
        "store_name":      u.store.name if u.store else None,
        "store_url":       u.store.wc_url if u.store else None,
        "wp_username":     u.wp_username or "",
        "has_wp_password": bool(u.wp_app_password),
        "note":            u.note or "",
    } for u in users]

@router.post("/users")
def create_user(req: CreateUserRequest, db: Session = Depends(get_db),
                _: User = Depends(require_admin)):
    if db.query(User).filter_by(username=req.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    if db.query(User).filter_by(email=req.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password phải ≥ 8 ký tự")
    if req.store_id and not db.query(Store).filter_by(id=req.store_id).first():
        raise HTTPException(status_code=400, detail="Store không tồn tại")
    user = User(
        username        = req.username,
        email           = req.email,
        hashed_pw       = hash_password(req.password),
        is_admin        = req.is_admin,
        is_active       = True,
        store_id        = req.store_id,
        wp_username     = req.wp_username,
        wp_app_password = req.wp_app_password,
    )
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "username": user.username, "ok": True}

@router.put("/users/{user_id}")
def update_user(user_id: int, req: UpdateUserRequest,
                db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    if req.username        is not None: user.username  = req.username
    if req.email           is not None: user.email     = req.email
    if req.is_active       is not None: user.is_active = req.is_active
    if req.is_admin        is not None: user.is_admin  = req.is_admin
    if req.note            is not None: user.note      = req.note
    if req.wp_username     is not None: user.wp_username = req.wp_username
    if req.wp_app_password is not None and req.wp_app_password:
        user.wp_app_password = req.wp_app_password
    if req.password is not None:
        if len(req.password) < 8:
            raise HTTPException(status_code=400, detail="Password phải ≥ 8 ký tự")
        user.hashed_pw = hash_password(req.password)
    if req.store_id is not None:
        user.store_id = req.store_id if req.store_id > 0 else None
    db.commit()
    return {"ok": True}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db),
                current_admin: User = Depends(require_admin)):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Không thể xóa chính mình")
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    # Xóa jobs của user trước
    db.query(Job).filter_by(user_id=user_id).delete(synchronize_session=False)
    db.delete(user); db.commit()
    return {"ok": True}

# ── Settings ───────────────────────────────────────────────────────────────────

class UpdateSettingsRequest(BaseModel):
    openai_key:       Optional[str] = None
    openai_model:     Optional[str] = None
    serper_key:       Optional[str] = None
    gemini_key:       Optional[str] = None
    store_name:       Optional[str] = None
    custom_shortcode: Optional[str] = None
    link_config:      Optional[str] = None

@router.get("/settings")
def get_settings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_all_settings(db)

@router.post("/settings")
def update_settings(req: UpdateSettingsRequest, db: Session = Depends(get_db),
                    _: User = Depends(require_admin)):
    SECRET_KEYS = {"openai_key", "serper_key", "gemini_key"}
    data = req.dict(exclude_none=True)
    for k, v in data.items():
        if k in SECRET_KEYS and ("*" in str(v) or str(v).strip() == ""):
            continue
        set_setting(db, k, str(v))
    return {"ok": True}

# ── Password Management ────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    new_password: str

@router.post("/users/{user_id}/change-password")
def change_password(user_id: int, req: ChangePasswordRequest,
                    db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải ít nhất 6 ký tự")
    target.hashed_pw = hash_password(req.new_password)
    db.commit()
    return {"success": True, "username": target.username}

# ── Job Management ─────────────────────────────────────────────────────────────

@router.get("/jobs")
def list_all_jobs(job_type: str = None, status: str = None, limit: int = 50,
                  db: Session = Depends(get_db), user: User = Depends(require_admin)):
    q = db.query(Job).order_by(Job.id.desc())
    if job_type: q = q.filter_by(job_type=job_type)
    if status:   q = q.filter_by(status=status)
    jobs = q.limit(limit).all()
    result = []
    for j in jobs:
        params = j.params or {}
        result.append({
            "id":         j.id,
            "job_type":   j.job_type,
            "status":     j.status,
            "created_at": j.created_at.isoformat(),
            "sp_count":   len(params.get("product_ids", []) if isinstance(params.get("product_ids", []), list) else []),
            "filename":   params.get("filename", ""),
            "uploader":   params.get("uploader", ""),
            "store_url":  params.get("store_url", ""),
            "store_id":   params.get("store_id", 0),
            "log_tail":   (j.log or "")[-200:],
            "result":     j.result,
            "celery_id":  j.celery_id,
        })
    return result

@router.delete("/jobs/clear-done")
def admin_clear_done(job_type: str = None, db: Session = Depends(get_db),
                     user: User = Depends(require_admin)):
    q = db.query(Job).filter(Job.status.in_(["done", "failed"]))
    if job_type: q = q.filter_by(job_type=job_type)
    count = q.count()
    q.delete(synchronize_session=False); db.commit()
    return {"deleted": count}

@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job); db.commit()
    return {"deleted": job_id}

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Job không thể hủy")
    if job.celery_id:
        from app.workers.celery_app import celery_app as _celery
        _celery.control.revoke(job.celery_id, terminate=True)
    job.status = "failed"
    job.log    = (job.log or "") + "\n❌ Bị hủy bởi admin"
    db.commit()
    return {"cancelled": job_id}

@router.post("/jobs/cancel-all-pending")
def cancel_all_pending(job_type: str = None, db: Session = Depends(get_db),
                       user: User = Depends(require_admin)):
    from app.workers.celery_app import celery_app as _celery
    q = db.query(Job).filter(Job.status.in_(["pending"]))
    if job_type: q = q.filter_by(job_type=job_type)
    jobs = q.all()
    for j in jobs:
        if j.celery_id:
            _celery.control.revoke(j.celery_id, terminate=False)
        j.status = "failed"
        j.log    = (j.log or "") + "\n❌ Bị hủy hàng loạt bởi admin"
    db.commit()
    return {"cancelled": len(jobs)}


# ── User Store Management ──────────────────────────────────────────────────────

class UserStoreRequest(BaseModel):
    store_id:        int
    wp_username:     str = ""
    wp_app_password: str = ""

@router.get("/users/{user_id}/stores")
def get_user_stores(user_id: int, db: Session = Depends(get_db),
                    _: User = Depends(require_admin)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    user_stores = db.query(UserStore).filter_by(user_id=user_id).all()
    return [{
        "id":              us.id,
        "store_id":        us.store_id,
        "store_name":      us.store.name,
        "store_url":       us.store.wc_url,
        "wp_username":     us.wp_username or "",
        "has_wp_password": bool(us.wp_app_password),
    } for us in user_stores]

@router.post("/users/{user_id}/stores")
def add_user_store(user_id: int, req: UserStoreRequest,
                   db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    if not db.query(Store).filter_by(id=req.store_id).first():
        raise HTTPException(status_code=404, detail="Store không tồn tại")
    existing = db.query(UserStore).filter_by(user_id=user_id, store_id=req.store_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User đã được gán store này rồi")
    us = UserStore(
        user_id         = user_id,
        store_id        = req.store_id,
        wp_username     = req.wp_username,
        wp_app_password = req.wp_app_password,
    )
    db.add(us); db.commit(); db.refresh(us)
    return {"id": us.id, "ok": True}

@router.put("/users/{user_id}/stores/{store_id}")
def update_user_store(user_id: int, store_id: int, req: UserStoreRequest,
                      db: Session = Depends(get_db), _: User = Depends(require_admin)):
    us = db.query(UserStore).filter_by(user_id=user_id, store_id=store_id).first()
    if not us:
        raise HTTPException(status_code=404, detail="Không tìm thấy")
    us.wp_username = req.wp_username
    if req.wp_app_password:
        us.wp_app_password = req.wp_app_password
    db.commit()
    return {"ok": True}

@router.delete("/users/{user_id}/stores/{store_id}")
def remove_user_store(user_id: int, store_id: int,
                      db: Session = Depends(get_db), _: User = Depends(require_admin)):
    us = db.query(UserStore).filter_by(user_id=user_id, store_id=store_id).first()
    if not us:
        raise HTTPException(status_code=404, detail="Không tìm thấy")
    db.delete(us); db.commit()
    return {"ok": True}

@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: int, db: Session = Depends(get_db),
              user: User = Depends(require_admin)):
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("failed", "done"):
        raise HTTPException(status_code=400, detail="Chỉ retry job failed/done")

    params = job.params or {}
    store_id = params.get("store_id", 0)

    # Lấy WC credentials từ store
    from app.models.database import Store, UserStore
    wc_url = wc_user = wc_pass = ""
    if store_id:
        us = db.query(UserStore).filter_by(user_id=job.user_id, store_id=store_id).first()
        if us:
            wc_url  = us.store.wc_url
            wc_user = us.wp_username or us.store.wp_username
            wc_pass = us.wp_app_password or us.store.wp_app_password
        else:
            s = db.query(Store).filter_by(id=store_id).first()
            if s:
                wc_url  = s.wc_url
                wc_user = s.wp_username
                wc_pass = s.wp_app_password
    # Fallback: lấy từ params nếu store_id=0 hoặc không tìm được store
    if not wc_url:
        wc_url  = params.get("wc_url", "")
        wc_user = params.get("wc_username", "")
        wc_pass = params.get("wc_app_password", "")

    # Reset job status
    job.status = "pending"
    job.log    = f"🔄 Retry lúc {__import__('datetime').datetime.now().strftime('%H:%M:%S')}\n"
    job.result = None
    db.commit()

    # Dispatch lại task
    if job.job_type == "upload":
        from app.workers.upload_worker import task_upload_products
        from app.core.config import UPLOAD_TMP_DIR
        zip_path = params.get("zip_path", "")
        options  = {k:v for k,v in params.items()
                    if k not in ("filename","uploader","store_id","store_url","zip_path")}
        task = task_upload_products.apply_async(
            args=[job.id, zip_path, options, wc_url, wc_user, wc_pass], queue="upload")
    elif job.job_type == "seo":
        from app.workers.seo_worker import task_seo_bulk
        product_ids  = params.get("product_ids", [])
        task = task_seo_bulk.apply_async(
            args=[job.id, product_ids, False, wc_url, wc_user, wc_pass, job.user_id, store_id],
            queue="celery")
    elif job.job_type == "review":
        from app.workers.review_worker import task_review_bulk
        product_ids = params.get("product_ids", [])
        rcfg = params.get("review_config", {})
        task = task_review_bulk.apply_async(
            args=[job.id, product_ids,
                  rcfg.get("review_count", 15), rcfg.get("review_count_min"),
                  rcfg.get("review_count_max"), rcfg.get("start_date", "2024-01-01"),
                  rcfg.get("end_date", "2025-06-01"), rcfg.get("dist_5", 70),
                  rcfg.get("dist_4", 30), rcfg.get("dist_3", 0),
                  rcfg.get("delay_between", 1.5), rcfg.get("skip_has_review", True),
                  wc_url, wc_user, wc_pass],
            queue="celery")
    else:
        raise HTTPException(status_code=400, detail=f"Không hỗ trợ retry job type: {job.job_type}")

    job.celery_id = task.id
    db.commit()
    return {"ok": True, "job_id": job.id}

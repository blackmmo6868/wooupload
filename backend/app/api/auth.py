"""
WooMMO Web — Auth API
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.database import get_db, User
from app.core.auth import (authenticate_user, create_access_token,
                            get_current_user, hash_password, require_admin)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str
    is_admin:     bool
    username:     str


@router.post("/token", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    token = create_access_token({"sub": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        is_admin=user.is_admin,
        username=user.username,
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id":       current_user.id,
        "username": current_user.username,
        "email":    current_user.email,
        "is_admin": current_user.is_admin,
        "store_name": current_user.store.store_name if current_user.store else "",
        "store_id": current_user.store_id,
    }


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.core.auth import verify_password
    if not verify_password(req.old_password, current_user.hashed_pw):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải ≥ 8 ký tự")
    current_user.hashed_pw = hash_password(req.new_password)
    db.commit()
    return {"ok": True}



@router.get("/my-stores")
def my_stores(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.database import Store, UserStore
    if user.is_admin:
        # Admin thấy tất cả stores
        stores = db.query(Store).order_by(Store.id).all()
        return [{
            "id":          s.id,
            "name":        s.name,
            "wc_url":      s.wc_url,
            "store_name":  s.store_name or s.name,
            "shortcode":   s.shortcode or "",
            "wp_username":     s.wp_username or "",
            "wp_app_password": s.wp_app_password or "",
        } for s in stores]
    else:
        # Member thấy stores được gán qua user_stores
        user_stores = db.query(UserStore).filter_by(user_id=user.id).all()
        result = []
        for us in user_stores:
            result.append({
                "id":          us.store.id,
                "name":        us.store.name,
                "wc_url":      us.store.wc_url,
                "store_name":  us.store.store_name or us.store.name,
                "shortcode":   us.store.shortcode or "",
                # WP credentials riêng của user cho store này
                "wp_username":     us.wp_username or us.store.wp_username or "",
                "wp_app_password": us.wp_app_password or us.store.wp_app_password or "",
            })
        # Fallback: nếu chưa có user_stores, dùng store_id cũ
        if not result and user.store:
            result.append({
                "id":          user.store.id,
                "name":        user.store.name,
                "wc_url":      user.store.wc_url,
                "store_name":  user.store.store_name or user.store.name,
                "shortcode":   user.store.shortcode or "",
                "wp_username":     user.wp_username or user.store.wp_username or "",
                "wp_app_password": user.wp_app_password or user.store.wp_app_password or "",
            })
        return result

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import json

from app.models.database import get_db, User, Settings
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/links", tags=["links"])

class CategoryLink(BaseModel):
    name: str
    url:  str

class ProductLink(BaseModel):
    title: str
    url:   str

class LinkConfigRequest(BaseModel):
    mode:           str = "category"
    category_links: List[CategoryLink] = []
    product_pool:   List[ProductLink]  = []

def _key(user_id, store_id=0): return f"link_config_user_{user_id}_store_{store_id}"

@router.get("/config")
def get_config(store_id: int = 0, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Settings).filter_by(key=_key(user.id, store_id)).first()
    if not row or not row.value:
        return {"mode": "category", "category_links": [], "product_pool": []}
    try:    return json.loads(row.value)
    except: return {"mode": "category", "category_links": [], "product_pool": []}

@router.post("/config")
def save_config(req: LinkConfigRequest, store_id: int = 0,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    key   = _key(user.id, store_id)
    value = json.dumps(req.dict(), ensure_ascii=False)
    row   = db.query(Settings).filter_by(key=key).first()
    if row: row.value = value
    else:   db.add(Settings(key=key, value=value))
    db.commit()
    return {"ok": True}

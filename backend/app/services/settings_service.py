"""
WooMMO Web — Settings Service
Lưu API keys và config trong DB (encrypted ở tầng app)
"""
from sqlalchemy.orm import Session
from app.models.database import Settings


KEYS = {
    "openai_key":        "",
    "openai_model":      "gpt-4o",
    "serper_key":        "",
    "gemini_key":        "",
    "store_name":        "BreakTees",
    "custom_shortcode":  "[thien_display_single_image]",
    "link_config":       "{}",   # JSON string
}


def get_setting(db: Session, key: str) -> str:
    row = db.query(Settings).filter_by(key=key).first()
    return row.value if row else KEYS.get(key, "")


def set_setting(db: Session, key: str, value: str):
    row = db.query(Settings).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.add(Settings(key=key, value=value))
    db.commit()


def get_all_settings(db: Session) -> dict:
    rows = {r.key: r.value for r in db.query(Settings).all()}
    result = {}
    for k, default in KEYS.items():
        result[k] = rows.get(k, default)
    # Mask API keys trước khi trả về
    for k in ("openai_key", "serper_key", "gemini_key"):
        v = result.get(k, "")
        result[k] = ("*" * (len(v) - 4) + v[-4:]) if len(v) > 4 else ("*" * len(v))
    return result


def get_all_settings_raw(db: Session) -> dict:
    """Lấy settings không mask — chỉ dùng nội bộ"""
    rows = {r.key: r.value for r in db.query(Settings).all()}
    result = {}
    for k, default in KEYS.items():
        result[k] = rows.get(k, default)
    return result

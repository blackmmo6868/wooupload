"""
WooMMO Web — Core Config
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL  = os.getenv("DATABASE_URL", "postgresql://woommo:password@localhost:5432/woommo")
REDIS_URL     = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY    = os.getenv("SECRET_KEY", "changeme-please-use-random-string")
ALGORITHM     = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 ngày

WC_URL          = os.getenv("WC_URL", "https://breaktees.com")
WC_USERNAME     = os.getenv("WC_USERNAME", "")
WC_APP_PASSWORD = os.getenv("WC_APP_PASSWORD", "")
STORE_NAME      = os.getenv("STORE_NAME", "BreakTees")
UPLOAD_TMP_DIR  = os.getenv("UPLOAD_TMP_DIR", "/tmp/woommo_uploads")

os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)

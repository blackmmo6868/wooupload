"""
WooMMO — File Logger
Ghi log đầy đủ (kể cả thông tin nhạy cảm) ra file để debug
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "/var/log/woommo"
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"woommo.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # File handler — rotate 10MB, giữ 5 file
    fh = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{name}.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(fh)
    return logger

# Loggers sẵn dùng
upload_logger = get_logger("upload")
seo_logger    = get_logger("seo")
review_logger = get_logger("review")

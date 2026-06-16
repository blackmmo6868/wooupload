"""
WooMMO Web — Celery App
"""
from celery import Celery
from app.core.config import REDIS_URL

celery_app = Celery(
    "woommo",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.workers.upload_worker",
        "app.workers.seo_worker",
        "app.workers.review_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,           # 1 task / worker (jobs nặng)
    result_expires=86400,                   # giữ result 24h
    worker_concurrency=2,                   # tối đa 2 job song song
    broker_connection_retry_on_startup=True, # fix CPendingDeprecationWarning
    task_annotations={
        "upload.products": {"rate_limit": "10/m"},
    },
)

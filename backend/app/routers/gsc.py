import os
from urllib.parse import urlparse
import psycopg2
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/gsc", tags=["gsc"])

GSC_PG_DSN = os.getenv("GSC_PG_DSN")

def get_conn():
    return psycopg2.connect(GSC_PG_DSN)

def url_to_site_id(url: str) -> str:
    """https://printedaura.com/product/abc/ -> sc-domain:printedaura.com"""
    netloc = urlparse(url).netloc.replace("www.", "")
    return f"sc-domain:{netloc}"

class SubmitPayload(BaseModel):
    urls: str

@router.post("/submit")
def submit_urls(payload: SubmitPayload):
    urls = [u.strip() for u in payload.urls.splitlines() if u.strip()]
    if not urls:
        return {"added": 0, "skipped": 0}

    conn = get_conn()
    cur = conn.cursor()
    added, skipped = 0, 0

    for url in urls:
        site_id = url_to_site_id(url)
        # Check trùng: đã index xong hoặc đang/đã có trong queue (pending/done)
        cur.execute(
            "SELECT 1 FROM indexed_history WHERE site_id=%s AND url=%s",
            (site_id, url)
        )
        if cur.fetchone():
            skipped += 1
            continue

        cur.execute(
            "SELECT 1 FROM queue WHERE site_id=%s AND url=%s AND status IN ('pending','done')",
            (site_id, url)
        )
        if cur.fetchone():
            skipped += 1
            continue

        cur.execute(
            "INSERT INTO queue (site_id, url, priority, retry_count) VALUES (%s, %s, 1, 0)",
            (site_id, url)
        )
        added += 1

    conn.commit()
    cur.close()
    conn.close()
    return {"added": added, "skipped": skipped}

@router.get("/list")
def list_urls():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, site_id, url, status, added_at FROM queue ORDER BY added_at DESC LIMIT 200"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "site_id": r[1], "url": r[2], "status": r[3], "added_at": r[4].isoformat()} for r in rows]

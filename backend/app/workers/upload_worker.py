"""
WooMMO Web — Upload Worker (Celery Task)
"""
import os, sys, json, time
import requests as _req
from requests.auth import HTTPBasicAuth as _Auth
sys.path.insert(0, "/opt/woommo/backend")
sys.path.insert(0, "/opt/woommo/logic")

from app.workers.celery_app import celery_app
from app.models.database import SessionLocal, Job
from woocommerce_api  import WooCommerceAPI
from product_uploader import ProductUploader


def _update_job(job_id, status, log_line="", result=None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = status
            job.log   += log_line + "\n" if log_line else ""
            if result is not None: job.result = result
            db.commit()
    finally:
        db.close()


@celery_app.task(bind=True, name="upload.products",
                 soft_time_limit=3600, time_limit=3660)
def task_upload_products(self, job_id: int, zip_path: str, options: dict,
                         wc_url: str = None, wc_user: str = None, wc_pass: str = None):
    _update_job(job_id, "running", "🚀 Bắt đầu upload...")
    try:
        api = WooCommerceAPI(wc_url, wc_user, wc_pass)

        def on_progress(current, total, message):
            _update_job(job_id, "running", message)
            self.update_state(state="PROGRESS",
                              meta={"current": current, "total": total, "message": message})

        uploader = ProductUploader(api, progress_callback=on_progress)
        result   = uploader.upload_products(zip_path, options)

        # Retry sản phẩm lỗi
        first_errors = [e for e in result.get("errors", []) if "Trùng slug" not in str(e.get("error","")) and "Trùng title" not in str(e.get("error",""))]
        retry_ok, retry_errors = [], []
        if first_errors:
            _update_job(job_id, "running", f"⚠️ {len(first_errors)} SP lỗi, retry sau 10s...")
            time.sleep(10)
            for err in first_errors:
                err_name = err if isinstance(err, str) else err.get("product", "")
                for attempt in range(2):
                    try:
                        r2 = uploader.upload_single_by_name(zip_path, err_name, options) \
                             if hasattr(uploader, "upload_single_by_name") else None
                        if r2 and r2.get("success"):
                            retry_ok.append(err_name)
                            _update_job(job_id, "running", f"  ✅ Retry OK: {err_name}")
                            break
                        raise Exception("failed")
                    except Exception:
                        if attempt < 1:
                            time.sleep(15 * (attempt + 1))
                        else:
                            retry_errors.append(err_name)

        summary = {
            "total":        result.get("total", 0),
            "successful":   result.get("successful", 0) + len(retry_ok),
            "failed":       result.get("failed", 0),
            "skipped":      result.get("skipped", 0),
            "errors":       result.get("errors", [])[:20],
            "retried_ok":   retry_ok,
            "product_urls": result.get("product_urls", []),
        }

        # ── Set primary category (Rank Math) ────────────────────────────────
        primary_cat_id = options.get("primary_category_id")
        uploaded_ids   = [p["id"] for p in summary.get("product_urls", []) if p.get("id")]
        if primary_cat_id and uploaded_ids:
            _update_job(job_id, "running", f"⭐ Set primary category ID={primary_cat_id}...")
            _endpoint = f"{wc_url.rstrip('/')}/wp-json/woommo/v1/set-post-meta"
            _auth     = _Auth(wc_user, wc_pass)
            ok = failed = 0
            for pid in uploaded_ids:
                try:
                    r = _req.post(
                        _endpoint, auth=_auth,
                        json={"post_id": pid, "meta": {
                            "rank_math_primary_category":    str(primary_cat_id),
                            "rank_math_primary_product_cat": str(primary_cat_id),
                        }},
                        timeout=10,
                    )
                    if r.status_code == 200: ok += 1
                    else: failed += 1
                except Exception: failed += 1
            _update_job(job_id, "running", f"⭐ Primary category: {ok} OK, {failed} lỗi")

        _update_job(job_id, "done",
                    f"✅ Hoàn thành: {summary['successful']}/{summary['total']} SP",
                    result=summary)

        # ── Auto pipeline ────────────────────────────────────────────────────
        pipeline    = options.get("pipeline", {})
        product_ids = [p["id"] for p in summary.get("product_urls", []) if p.get("id")]

        if pipeline.get("seo") and product_ids:
            _update_job(job_id, "done",
                        f"🤖 Auto SEO job đã vào hàng đợi ({len(product_ids)} SP)")
            from app.workers.seo_worker import task_seo_bulk
            db3 = SessionLocal()
            try:
                user_id = pipeline.get("user_id")
                from app.models.database import Store as _Store
                _db_s = SessionLocal()
                try:
                    _sr = _db_s.query(_Store).filter_by(wc_url=wc_url).first()
                    _real_store_id = _sr.id if _sr else 0
                finally:
                    _db_s.close()
                seo_job = Job(
                    user_id=user_id, job_type="seo", status="pending",
                    params={"product_ids": product_ids, "uploader": "auto-pipeline",
                            "auto_publish": pipeline.get("publish", False),
                            "wc_url": wc_url, "wc_username": wc_user,
                            "wc_app_password": wc_pass, "store_id": _real_store_id},
                    log="", result=None
                )
                db3.add(seo_job)
                db3.commit()
                db3.refresh(seo_job)
                task_seo_bulk.apply_async(
                    args=[seo_job.id, product_ids, True, wc_url, wc_user, wc_pass, user_id, _real_store_id],
                    queue="celery")
            finally:
                db3.close()

        return summary

    except Exception as e:
        _update_job(job_id, "failed", f"❌ Lỗi: {str(e)}", result={"error": str(e)})
        raise
    finally:
        try:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass

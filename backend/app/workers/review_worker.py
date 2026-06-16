import sys, time, random
sys.path.insert(0, "/opt/woommo/backend")
sys.path.insert(0, "/opt/woommo/logic")

from app.workers.celery_app import celery_app
from app.models.database import SessionLocal, Job
from app.services.settings_service import get_all_settings_raw
from woocommerce_api   import WooCommerceAPI
from review_generator  import generate_reviews_for_product, generate_reviews_for_product_batched, BATCH_SIZE


def _update_job(job_id, status, log_line="", result=None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = status
            job.log   += log_line + "\n" if log_line else ""
            if result is not None:
                job.result = result
            db.commit()
    finally:
        db.close()


@celery_app.task(bind=True, name="review.bulk_import")
def task_review_bulk(self, job_id, product_ids,
                     review_count, review_count_min, review_count_max,
                     start_date, end_date, dist_5, dist_4, dist_3,
                     delay_between, skip_has_review,
                     wc_url, wc_username, wc_app_password):
    _update_job(job_id, "running", "🤖 Khởi động Review generator...")

    db = SessionLocal()
    try:
        cfg = get_all_settings_raw(db)
    finally:
        db.close()

    openai_key = cfg.get("openai_key", "")
    if not openai_key:
        _update_job(job_id, "failed", "❌ Chưa cấu hình OpenAI API key",
                    result={"error": "missing openai_key"})
        return

    api = WooCommerceAPI(wc_url, wc_username, wc_app_password)

    if product_ids:
        _update_job(job_id, "running", f"Fetching {len(product_ids)} products...")
        products = []
        import requests as _req2
        from requests.auth import HTTPBasicAuth as _Auth2
        for i in range(0, len(product_ids), 100):
            batch = product_ids[i:i+100]
            r = _req2.get(
                f"{wc_url.rstrip('/')}/wp-json/wc/v3/products",
                auth=_Auth2(wc_username, wc_app_password),
                params={"include": ",".join(str(x) for x in batch), "per_page": 100},
                timeout=30,
            )
            if r.status_code == 200:
                products.extend(r.json())
    else:
        _update_job(job_id, "running", "Fetching all products...")
        products = api.get_all_products(status="any")

    # Lấy review counts nếu skip_has_review
    existing_counts = {}
    if skip_has_review and products:
        ids = [p["id"] for p in products]
        existing_counts = api.get_review_counts(ids)

    total = len(products)
    done_count = fail_count = 0
    errors = []

    for i, product in enumerate(products):
        pid   = product["id"]
        pname = product.get("name", "")

        # Bỏ qua nếu đã có review
        if skip_has_review:
            rc = int(existing_counts.get(str(pid), 0))
            if rc > 0:
                _update_job(job_id, "running", f"⏭ [{i+1}/{total}] Bỏ qua (đã có {rc} reviews): {pname}")
                continue

        rc = random.randint(review_count_min, review_count_max) \
             if review_count_min and review_count_max else review_count

        self.update_state(state="PROGRESS",
            meta={"current": i+1, "total": total,
                  "message": f"[{i+1}/{total}] {pname} ({rc} reviews)"})
        _update_job(job_id, "running", f"[{i+1}/{total}] Generating {rc} reviews: {pname}")

        try:
            image_b64 = api.get_product_image_base64(product)

            def batch_cb(b, tb, msg):
                _update_job(job_id, "running", f"  {msg}")

            if rc > BATCH_SIZE:
                reviews = generate_reviews_for_product_batched(
                    openai_api_key=openai_key, product_id=pid,
                    product_name=pname, image_b64=image_b64 or "",
                    review_count=rc, start_date=start_date, end_date=end_date,
                    dist_5=dist_5, dist_4=dist_4, dist_3=dist_3,
                    progress_callback=batch_cb,
                )
            else:
                reviews = generate_reviews_for_product(
                    openai_api_key=openai_key, product_id=pid,
                    product_name=pname, image_b64=image_b64 or "",
                    review_count=rc, start_date=start_date, end_date=end_date,
                    dist_5=dist_5, dist_4=dist_4, dist_3=dist_3,
                )

            result = api.import_reviews_batch(reviews)
            inserted = result.get("inserted", 0)

            if inserted > 0:
                done_count += 1
                _update_job(job_id, "running", f"  ✅ {inserted} reviews imported: {pname}")
            else:
                fail_count += 1
                err = "; ".join(result.get("errors", [])[:2])
                errors.append({"product": pname, "error": err})
                _update_job(job_id, "running", f"  ❌ {pname}: {err}")

        except Exception as e:
            fail_count += 1
            errors.append({"product": pname, "error": str(e)})
            _update_job(job_id, "running", f"  ❌ {pname}: {e}")

        if i < total - 1:
            time.sleep(delay_between)

    summary = {"total": total, "done": done_count,
               "failed": fail_count, "errors": errors[:20]}
    _update_job(job_id, "done", f"✅ Review xong: {done_count}/{total}", result=summary)
    return summary

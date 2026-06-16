"""
WooMMO — Review Importer Worker
QThread chạy background: với mỗi sản phẩm được chọn →
    1. Fetch feature image
    2. Gọi GPT-4o sinh reviews
    3. Import batch lên WP qua PHP endpoint
"""

import time
import random
from PyQt5.QtCore import QThread, pyqtSignal

from woocommerce_api  import WooCommerceAPI
from review_generator import generate_reviews_for_product, generate_reviews_for_product_batched, BATCH_SIZE


class ReviewImportWorker(QThread):
    """
    Signals:
        product_started(index, total, product_name)
        product_done(index, total, product_name, inserted, failed, error_msg)
        all_done(summary_dict)
    """

    product_started = pyqtSignal(int, int, str)
    product_done    = pyqtSignal(int, int, str, int, int, str)
    all_done        = pyqtSignal(dict)

    def __init__(
        self,
        wc_api: WooCommerceAPI,
        openai_api_key: str,
        products: list,
        review_count: int,
        start_date: str,
        end_date: str,
        dist_5: int,
        dist_4: int,
        dist_3: int,
        delay_between: float = 1.5,
        review_count_min: int = None,   # None = dùng review_count cố định
        review_count_max: int = None,
        parent=None,
    ):
        super().__init__(parent)
        self._api             = wc_api
        self._openai_key      = openai_api_key
        self._products        = products
        self._review_count    = review_count
        self._review_count_min = review_count_min
        self._review_count_max = review_count_max
        self._start_date      = start_date
        self._end_date        = end_date
        self._dist_5          = dist_5
        self._dist_4          = dist_4
        self._dist_3          = dist_3
        self._delay           = delay_between
        self._stop_flag       = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        total       = len(self._products)
        done_count  = 0
        fail_count  = 0
        skip_count  = 0

        for i, product in enumerate(self._products, start=1):
            if self._stop_flag:
                break

            product_id   = product["id"]
            product_name = product["name"]

            self.product_started.emit(i, total, product_name)

            # Xác định số review cho SP này
            if self._review_count_min is not None and self._review_count_max is not None:
                review_count = random.randint(self._review_count_min, self._review_count_max)
            else:
                review_count = self._review_count

            try:
                # 1. Fetch feature image → base64
                image_b64 = self._api.get_product_image_base64(product)
                if not image_b64:
                    # Không có ảnh — vẫn generate nhưng GPT-4o sẽ dựa vào tên SP
                    image_b64 = ""

                # 2. GPT-4o generate CSV → batch nếu review_count > BATCH_SIZE
                def _batch_cb(b, total_b, msg):
                    self.product_started.emit(i, total, f"{product_name} [batch {b}/{total_b}]")

                if review_count > BATCH_SIZE:
                    reviews = generate_reviews_for_product_batched(
                        openai_api_key=self._openai_key,
                        product_id=product_id,
                        product_name=product_name,
                        image_b64=image_b64,
                        review_count=review_count,
                        start_date=self._start_date,
                        end_date=self._end_date,
                        dist_5=self._dist_5,
                        dist_4=self._dist_4,
                        dist_3=self._dist_3,
                        progress_callback=_batch_cb,
                    )
                else:
                    reviews = generate_reviews_for_product(
                        openai_api_key=self._openai_key,
                        product_id=product_id,
                        product_name=product_name,
                        image_b64=image_b64,
                        review_count=review_count,
                        start_date=self._start_date,
                        end_date=self._end_date,
                        dist_5=self._dist_5,
                        dist_4=self._dist_4,
                        dist_3=self._dist_3,
                    )

                # 3. Import batch lên WP
                result = self._api.import_reviews_batch(reviews)

                inserted = result.get("inserted", 0)
                failed   = result.get("failed",   0)
                errors   = result.get("errors",   [])
                err_msg  = "; ".join(errors[:2]) if errors else ""

                if inserted > 0:
                    done_count += 1
                else:
                    fail_count += 1

                self.product_done.emit(i, total, product_name, inserted, failed, err_msg)

            except Exception as e:
                fail_count += 1
                self.product_done.emit(i, total, product_name, 0, review_count, str(e))

            # Delay giữa các SP để tránh OpenAI rate limit
            if i < total and not self._stop_flag:
                time.sleep(self._delay)

        self.all_done.emit({
            "done":    done_count,
            "failed":  fail_count,
            "skipped": skip_count,
            "total":   total,
        })

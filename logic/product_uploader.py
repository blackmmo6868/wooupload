"""
WooMMO All-in-One — Product Uploader
- Featured image = file trùng tên với folder
- Còn lại = gallery
- Không có tags, không có S3, không có consumer key
- Upload ảnh qua WP REST API /wp/v2/media (Basic Auth)
"""

import os
import re
import io
import shutil
import string
import random
import zipfile
from pathlib import Path

from PIL import Image
from slugify import slugify
try:
    from image_processor import ImageBatchProcessor, RENAME_MODE_CLASSIC, RENAME_MODE_AUTODETECT
    HAS_IMAGE_PROCESSOR = True
except ImportError:
    HAS_IMAGE_PROCESSOR = False


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class ProductUploader:

    def __init__(self, wc_api, progress_callback=None):
        """
        Args:
            wc_api: WooCommerceAPI instance (Basic Auth)
            progress_callback: callable(current: int, total: int, message: str)
        """
        self.wc_api            = wc_api
        self.progress_callback = progress_callback

    # ── Progress ───────────────────────────────────────────────────────────────

    def _progress(self, current: int, total: int, message: str):
        if self.progress_callback:
            self.progress_callback(current, total, message)

    # ── ZIP handling ───────────────────────────────────────────────────────────

    def extract_zip(self, zip_path: str, extract_to: str = None) -> str:
        if extract_to is None:
            extract_to = str(Path(zip_path).parent / "_woommo_tmp")
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)
        os.makedirs(extract_to)
        if zip_path.lower().endswith(".rar"):
            try:
                import subprocess
                result = subprocess.run(
                    ["/usr/bin/unar", "-o", extract_to, "-force-overwrite", zip_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                if result.returncode not in (0, 1):
                    raise Exception(f"unar failed with code {result.returncode}")
            except FileNotFoundError:
                raise Exception("Không tìm thấy tool giải nén RAR. Vui lòng dùng file ZIP.")
            except Exception:
                import traceback, sys
                print(traceback.format_exc(), file=sys.stderr, flush=True)
                raise
        else:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_to)
        return extract_to

    # ── Parse folders → products ───────────────────────────────────────────────

    def parse_product_folders(self, extract_path: str) -> list:
        """
        Mỗi sub-folder = 1 sản phẩm.
        Tên folder = Title.
        File trùng tên folder (bất kể extension) = featured image.
        Các file còn lại = gallery (sorted alphabetically).

        Trả về list[dict]:
          {
            "title":    str,
            "slug":     str,
            "featured": str | None,   # absolute path
            "gallery":  list[str],    # absolute paths, sorted
          }
        """
        root = extract_path

        # Nếu chỉ có 1 folder con ở root (wrapper folder), đi sâu vào
        items    = os.listdir(root)
        subdirs  = [d for d in items if os.path.isdir(os.path.join(root, d))]
        if len(subdirs) == 1 and len(items) == 1:
            # Chỉ bóc wrapper folder nếu bên trong subdir đó CŨNG là thư mục
            # (không phải file ảnh trực tiếp — tránh nhầm sản phẩm 1-folder thành wrapper)
            inner_path  = os.path.join(root, subdirs[0])
            inner_items = os.listdir(inner_path)
            inner_has_subdir = any(os.path.isdir(os.path.join(inner_path, i)) for i in inner_items)
            if inner_has_subdir:
                root = inner_path

        products = []

        for folder_name in sorted(os.listdir(root)):
            try:
                folder_name = folder_name.encode('utf-8', errors='surrogateescape').decode('utf-8', errors='replace')
            except Exception:
                pass
            folder_path = os.path.join(root, folder_name)
            if not os.path.isdir(folder_path):
                continue

            # Collect image files
            all_images = sorted([
                f for f in os.listdir(folder_path)
                if Path(f).suffix.lower() in IMAGE_EXTS
            ])

            if not all_images:
                continue

            # Featured = file whose stem == folder_name (case-insensitive)
            folder_stem = folder_name.strip().lower()
            featured    = None
            gallery     = []

            for fname in all_images:
                fpath = os.path.join(folder_path, fname)
                if Path(fname).stem.strip().lower().replace("-", " ") == folder_stem.replace("-", " "):
                    featured = fpath
                else:
                    gallery.append(fpath)

            # Fallback: nếu không tìm được featured, dùng ảnh đầu tiên
            if featured is None and all_images:
                featured = os.path.join(folder_path, all_images[0])
                gallery  = [os.path.join(folder_path, f) for f in all_images[1:]]

            products.append({
                "title":    folder_name,
                "slug":     slugify(folder_name),
                "featured": featured,
                "gallery":  gallery,
            })

        return products

    # ── Image helpers ──────────────────────────────────────────────────────────

    def optimize_image(self, image_path: str,
                       max_size: tuple = (1920, 1920),
                       quality: int = 85) -> str:
        """
        Resize & compress image in-place.
        Returns the (possibly same) path.
        """
        try:
            with Image.open(image_path) as img:
                if img.mode == "RGBA":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                elif img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                buf.seek(0)

            with open(image_path, "wb") as f:
                f.write(buf.read())
        except Exception as e:
            print(f"[WARN] Could not optimize {image_path}: {e}")

        return image_path

    def _upload_image(self, image_path: str, alt_text: str = "") -> dict:
        """
        Upload một ảnh qua WP REST /wp/v2/media.
        Returns {"media_id": int, "url": str} or raises Exception.
        """
        result = self.wc_api.upload_media(image_path, alt_text=alt_text)
        if not result["success"]:
            raise Exception(result["error"])
        return {"media_id": result["media_id"], "url": result["url"]}

    # ── Create one product ─────────────────────────────────────────────────────

    def create_product(self, product: dict, options: dict) -> dict:
        """
        Upload ảnh → tạo sản phẩm WooCommerce.
        product: dict từ parse_product_folders()
        options: dict từ upload_dialog (status, price, categories, sku_mode, ...)
        Returns WooCommerce product dict on success, raises on failure.
        """
        title    = product["title"]
        featured = product["featured"]
        gallery  = product["gallery"]
        optimize = options.get("optimize_images", False)

        # ── 1. Upload featured image ───────────────────────────────────────────
        if featured and os.path.exists(featured):
            if optimize:
                self.optimize_image(featured)
            feat_result = self._upload_image(featured, alt_text=title)
            featured_id = feat_result["media_id"]
        else:
            featured_id = None

        # ── 2. Upload gallery images ───────────────────────────────────────────
        gallery_ids = []
        for i, gpath in enumerate(gallery):
            if not os.path.exists(gpath):
                continue
            if optimize:
                self.optimize_image(gpath)
            try:
                g_result = self._upload_image(gpath, alt_text=f"{title} {i+1}")
                gallery_ids.append(g_result["media_id"])
            except Exception as e:
                print(f"[WARN] Gallery image upload failed ({gpath}): {e}")

        # ── 3. Build images list (featured first) ──────────────────────────────
        images = []
        if featured_id:
            images.append({"id": featured_id})
        for gid in gallery_ids:
            images.append({"id": gid})

        # ── 4. SKU ─────────────────────────────────────────────────────────────
        sku_mode   = options.get("sku_mode", "empty")
        sku_prefix = options.get("sku_prefix", "").strip().upper()
        sku        = ""
        if sku_mode == "random":
            sku = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        elif sku_mode == "filename":
            sku = slugify(title)[:50]
        elif sku_mode == "prefix_random":
            rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            prefix    = sku_prefix if sku_prefix else "SKU"
            sku       = f"{prefix}-{rand_part}"

        # ── 5. Build WooCommerce payload ───────────────────────────────────────
        wc_data = {
            "name":   title,
            "type":   "simple",
            "status": options.get("status", "draft"),
            "images": images,
        }

        if sku:
            wc_data["sku"] = sku

        if options.get("regular_price"):
            wc_data["regular_price"] = str(options["regular_price"])

        if options.get("sale_price"):
            wc_data["sale_price"] = str(options["sale_price"])

        if options.get("short_description"):
            wc_data["short_description"] = options["short_description"]
        if options.get("tags"):
            wc_data["tags"] = [{"name": t.strip()} for t in options["tags"] if t.strip()]

        if options.get("categories"):
            wc_data["categories"] = [{"id": cid} for cid in options["categories"]]

        # ── 6. Meta data (Rank Math focus keyword, WCPA) ──────────────────────
        meta_data = [
            {"key": "rank_math_focus_keyword", "value": title}
        ]


        if options.get("wcpa_form_id"):
            form_id = int(options["wcpa_form_id"])
            meta_data.append({"key": "wcpa_product_meta",  "value": [str(form_id)]})
            meta_data.append({"key": "_wcpa_product_meta", "value": [form_id]})

        wc_data["meta_data"] = meta_data

        # ── 7. Create product via API ──────────────────────────────────────────
        result = self.wc_api.create_product(wc_data)
        if not result["success"]:
            raise Exception(result["error"])

        product = result["product"]
        product_id = product.get("id")

        # ── 8. Set post_parent → ảnh hiện "Uploaded to" trong Media Library ─────
        # WP REST API PATCH /wp/v2/media/{id} với {"post": product_id}
        # Code cũ dùng custom plugin woommo-simple.php để làm điều này;
        # bản này dùng chuẩn WP REST API — không cần plugin.
        if product_id:
            all_media_ids = ([featured_id] if featured_id else []) + gallery_ids
            self._attach_images_to_product(all_media_ids, product_id, title)

        # ── 9. Gán Brand qua WP REST API (sau khi có product_id) ──────────────
        brand_info = options.get("brand_info")
        if product_id and brand_info and brand_info.get("taxonomy") and brand_info.get("brand_id"):
            self._assign_brand(product_id, brand_info["taxonomy"], brand_info["brand_id"], title)

        # ── 10. Fix _price meta → fix layout giá trên storefront ──
        if product_id:
            self.wc_api.clear_product_cache(
                product_id,
                sale_price=str(options["sale_price"]) if options.get("sale_price") else None,
                regular_price=str(options["regular_price"]) if options.get("regular_price") else None,
            )

        return product

    def _attach_images_to_product(self, media_ids: list, product_id: int, title: str):
        """
        Set post_parent cho tất cả attachment → hiện "Uploaded to [product]"
        trong WordPress Media Library.

        Dùng WP REST API: POST /wp/v2/media/{media_id} với {"post": product_id}
        Không cần plugin custom — hoạt động với Application Password.
        """
        import requests as _req
        for media_id in media_ids:
            if not media_id:
                continue
            try:
                url = f"{self.wc_api.url}/wp-json/wp/v2/media/{media_id}"
                r   = _req.post(
                    url,
                    auth=self.wc_api._auth,
                    json={"post": product_id},
                    timeout=15,
                )
                if r.status_code in (200, 201):
                    print(f"[Media] ✓ Attached media #{media_id} → product #{product_id} ({title})")
                else:
                    print(f"[Media] ✗ media #{media_id}: HTTP {r.status_code} {r.text[:120]}")
            except Exception as e:
                print(f"[Media] ✗ Exception attaching media #{media_id}: {e}")

    def _assign_brand(self, product_id: int, taxonomy: str, brand_id: int, title: str):
        """
        Gán brand term vào product qua WP REST API /wp/v2/product/{id}
        Đây là cách duy nhất hoạt động với PWB (pwb-brand có dấu gạch ngang).
        """
        import requests as _requests
        try:
            url = f"{self.wc_api.url}/wp-json/wp/v2/product/{product_id}"
            payload = {taxonomy: [brand_id]}
            r = _requests.post(
                url,
                auth=self.wc_api._auth,
                json=payload,
                timeout=20,
            )
            if r.status_code in (200, 201):
                print(f"[Brand] ✓ Gán '{taxonomy}' ID={brand_id} → product #{product_id} ({title})")
            else:
                print(f"[Brand] ✗ Lỗi {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[Brand] ✗ Exception: {e}")

    # ── Upload all products from ZIP ───────────────────────────────────────────

    def upload_products(self, zip_path: str, options: dict) -> dict:
        """
        Main entry point.
        Returns:
          {
            "total":      int,
            "successful": int,
            "failed":     int,
            "skipped":    int,   # sản phẩm bị bỏ qua do trùng slug/title
            "errors":     [{"product": str, "error": str}]
          }
        """
        results = {"total": 0, "successful": 0, "failed": 0,
                   "skipped": 0, "errors": [], "product_urls": []}

        # Khởi tạo trước để tránh UnboundLocalError nếu exception xảy ra sớm
        existing_slugs  = set()
        existing_titles = set()
        extract_path = None
        try:
            self._progress(0, 100, "Đang giải nén ZIP...")
            extract_path = self.extract_zip(zip_path)

            # Image Processing (nen + rename + EXIF metadata)
            img_opts = options.get("image_processing", {})
            if img_opts.get("enabled") and HAS_IMAGE_PROCESSOR:
                self._progress(3, 100, "Dang xu ly anh (nen + metadata)...")
                import shutil as _shutil

                rename_mode_str = img_opts.get("rename_mode", "none")
                if rename_mode_str == "classic":
                    _rename_mode = RENAME_MODE_CLASSIC
                    _do_rename   = True
                elif rename_mode_str == "autodetect":
                    _rename_mode = RENAME_MODE_AUTODETECT
                    _do_rename   = True
                else:
                    _rename_mode = RENAME_MODE_CLASSIC
                    _do_rename   = False

                # Tim dung folder chua cac product folders
                # Neu extract_path co 1 wrapper folder thi di sau vao
                _img_root = extract_path
                _items = os.listdir(_img_root)
                _subdirs = [d for d in _items if os.path.isdir(os.path.join(_img_root, d))]
                if len(_subdirs) == 1 and len(_items) == 1:
                    _img_root = os.path.join(_img_root, _subdirs[0])

                processor = ImageBatchProcessor(
                    folder          = _img_root,
                    brand           = img_opts.get("brand", "BreakTees"),
                    basewidth       = img_opts.get("max_width", 1000),
                    quality         = img_opts.get("quality", 90),
                    rating          = img_opts.get("rating", 5),
                    date_taken_days = img_opts.get("date_days", 7),
                    do_rename       = _do_rename,
                    rename_mode     = _rename_mode,
                    log_fn          = lambda m: self._progress(3, 100, m),
                )
                img_result = processor.run()

                output_dir = img_result.get("output", "")
                if output_dir and os.path.isdir(output_dir):
                    if _img_root == extract_path:
                        _shutil.rmtree(extract_path)
                        os.rename(output_dir, extract_path)
                    else:
                        for item in os.listdir(output_dir):
                            src = os.path.join(output_dir, item)
                            dst = os.path.join(_img_root, item)
                            if os.path.isdir(src):
                                if os.path.exists(dst):
                                    _shutil.rmtree(dst)
                                _shutil.copytree(src, dst)
                        _shutil.rmtree(output_dir, ignore_errors=True)
                    self._progress(4, 100,
                        f"Xu ly anh xong: {img_result['processed']} file, "
                        f"{img_result['errors']} loi")
                else:
                    self._progress(4, 100, "Xu ly anh xong nhung khong tim thay output")


            self._progress(5, 100, "Đang phân tích cấu trúc folder...")
            products = self.parse_product_folders(extract_path)
            results["total"] = len(products)

            if not products:
                raise Exception("Không tìm thấy sản phẩm nào trong ZIP!")

            # ── Duplicate check — pre-fetch một lần, check offline ────────────
            skip_duplicates = options.get("skip_duplicates", False)
            existing_slugs  = set()
            existing_titles = set()

            if skip_duplicates:
                self._progress(10, 100, "✅ Bắt đầu upload (check trùng slug real-time)...")
                self._progress(10, 100,
                    f"✅ Đã tải {dup_data['count']} sản phẩm — bắt đầu upload...")

            n = len(products)
            for i, product in enumerate(products):
                pct = 10 + int((i / n) * 88)
                title = product["title"]
                self._progress(pct, 100, f"[{i+1}/{n}] Đang upload: {title}")

                # ── Kiểm tra trùng lặp ────────────────────────────────────────
                if skip_duplicates:
                    product_slug  = product["slug"].lower()
                    product_title = title.lower()

                    slug_exists = (product_slug in existing_slugs) or \
                                  self.wc_api.check_slug_exists(product_slug)
                    if slug_exists:
                        existing_slugs.add(product_slug)
                        print(f"⚠ [{i+1}/{n}] TRÙNG SLUG: {title} (slug: {product_slug})")
                        self._progress(pct, 100,
                            f"⚠ [{i+1}/{n}] Bỏ qua (trùng slug): {title}")
                        results["skipped"] += 1
                        results["errors"].append({
                            "product": title,
                            "error":   f"⚠ Trùng slug: '{product_slug}' — đã bỏ qua",
                        })
                        continue

                    if product_title in existing_titles:
                        print(f"⚠ [{i+1}/{n}] TRÙNG TITLE: {title}")
                        self._progress(pct, 100,
                            f"⚠ [{i+1}/{n}] Bỏ qua (trùng title): {title}")
                        results["skipped"] += 1
                        results["errors"].append({
                            "product": title,
                            "error":   f"⚠ Trùng title — đã bỏ qua",
                        })
                        continue

                # ── Upload ────────────────────────────────────────────────────
                try:
                    wc_product = self.create_product(product, options)
                    results["successful"] += 1
                    pid       = wc_product.get("id", "")
                    store_url = self.wc_api.url.rstrip("/")

                    slug = (wc_product.get("slug", "") or "").strip()
                    if not slug:
                        import unicodedata
                        name_norm = unicodedata.normalize("NFKD", title)
                        name_norm = name_norm.encode("ascii", "ignore").decode("ascii")
                        slug = re.sub(r"[^a-z0-9\s-]", "", name_norm.lower())
                        slug = re.sub(r"\s+", "-", slug.strip())
                        slug = re.sub(r"-+", "-", slug).strip("-")

                    purl = (f"{store_url}/product/{slug}/"
                            if slug else
                            wc_product.get("permalink", "") or f"{store_url}/?p={pid}")

                    results["product_urls"].append({"title": title, "url": purl, "id": pid})
                    print(f"✓ [{i+1}/{n}] {title} (ID: {pid})")

                    # Cập nhật session set để tránh stale check trong cùng batch
                    if skip_duplicates:
                        existing_slugs.add(slug.lower())
                        existing_titles.add(title.lower())

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({"product": title, "error": str(e)})
                    print(f"✗ [{i+1}/{n}] {title}: {e}")

            self._progress(100, 100, "Hoàn thành!")

            # ── Set primary category (Rank Math) via woommo plugin ────────────
            primary_cat_id = options.get("primary_category_id")
            print(f"[PRIMARY] primary_cat_id={primary_cat_id} urls={results.get('product_urls', [])}")
            if primary_cat_id:
                uploaded_ids = [p["id"] for p in results.get("product_urls", []) if p.get("id")]
                if uploaded_ids:
                    self._progress(100, 100, f"⭐ Set primary category ID={primary_cat_id}...")
                    import requests as _req
                    _endpoint = f"{self.wc_api.url.rstrip('/')}/wp-json/woommo/v1/set-post-meta"
                    ok = failed = 0
                    for pid in uploaded_ids:
                        try:
                            r = _req.post(
                                _endpoint,
                                auth=self.wc_api._auth,
                                json={"post_id": pid, "meta": {"rank_math_primary_category": str(primary_cat_id), "rank_math_primary_product_cat": str(primary_cat_id)}},
                                timeout=10,
                            )
                            if r.status_code == 200:
                                ok += 1
                            else:
                                failed += 1
                        except Exception:
                            failed += 1
                    self._progress(100, 100, f"⭐ Primary category: {ok} OK, {failed} lỗi")

        except Exception as e:
            results["errors"].append({"product": "General", "error": str(e)})
        finally:
            if extract_path and os.path.exists(extract_path):
                shutil.rmtree(extract_path, ignore_errors=True)

        return results

    def upload_single_by_name(self, zip_path: str, product_name: str, options: dict) -> dict:
        """Retry upload 1 sản phẩm theo tên từ ZIP đã có sẵn hoặc giải nén lại"""
        try:
            extract_path = self.extract_zip(zip_path) if zip_path and os.path.exists(zip_path) else None
            if not extract_path:
                return {"success": False, "error": "ZIP không còn tồn tại"}

            products = self.parse_product_folders(extract_path)
            match = next((p for p in products if p["title"] == product_name), None)
            if not match:
                return {"success": False, "error": f"Không tìm thấy '{product_name}' trong ZIP"}

            wc_product = self.create_product(match, options)
            return {"success": True, "product": wc_product}
        except Exception as e:
            return {"success": False, "error": str(e)}

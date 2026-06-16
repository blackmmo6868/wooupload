"""
WooMMO Pro — Image Processor
Tách từ compress_and_rename_v11_METADATA_PRO.py
Business logic thuần túy: Rename + Compress (WebP→JPG) + EXIF Metadata
Không phụ thuộc Tkinter — dùng được trong PyQt5 QThread.
"""

import os
import re
import uuid
import glob
from pathlib import Path
from datetime import datetime, timedelta

from PIL import Image, PngImagePlugin
from PIL.Image import LANCZOS

PngImagePlugin.MAX_TEXT_CHUNK = 100 * (1024 ** 2)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────

IMAGE_EXTS_INPUT = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

COLORS = [
    "Royal Blue", "Forest Green", "Dark Green", "Light Blue", "Hot Pink",
    "Dark Heather", "Sport Grey", "Sport Gray", "Kelly Green", "Carolina Blue",
    "Light Pink", "Light Blue", "Bright Pink",
    "Black", "White", "Red", "Blue", "Green", "Yellow", "Navy", "Grey", "Gray",
    "Pink", "Purple", "Orange", "Brown", "Maroon", "Beige", "Cream", "Gold",
    "Silver", "Olive", "Teal", "Cyan", "Magenta", "Coral", "Indigo", "Violet",
    "Charcoal", "Ash", "Sand", "Natural", "Heather",
]
COLORS_SORTED = sorted(COLORS, key=lambda x: -len(x))

PRODUCT_TYPES = sorted([
    # Apparel
    "Pullover Hoodie", "Zip Hoodie", "Long Sleeve", "Sweatshirt", "Sweater",
    "Hoodie", "Tank Top", "T-Shirt", "Tshirt", "Tee", "Polo", "Crop Top",
    "Youth T-Shirt", "Kids T-Shirt", "V-Neck", "V Neck", "Shirt",
    # Footwear
    "Canvas Shoes", "Shoes", "Crocs", "Sneakers", "Boots", "Slip-On",
    "Clogs",
    # Home & Living
    "Area Rug", "Rugs", "Rug",
    "Canvas Print", "Canvas Wall Art", "Canvas",
    "Poster", "Wall Print", "Art Print",
    "Tumbler", "Travel Mug", "Coffee Mug", "Mug",
    # Accessories
    "Phone Case", "iPhone Case", "Samsung Case",
], key=lambda x: -len(x))

PRODUCT_ALIASES = {
    "T-Shirt":         ["Shirt", "Tshirt", "Tee", "T Shirt"],
    "Shirt":           ["T-Shirt", "Tshirt", "Tee", "T Shirt"],
    "Hoodie":          ["Pullover Hoodie", "Zip Hoodie", "Hooded"],
    "Pullover Hoodie": ["Hoodie", "Zip Hoodie"],
    "Zip Hoodie":      ["Hoodie", "Pullover Hoodie"],
    "Long Sleeve":     ["Long-Sleeve", "Longsleeve", "Long Sleve", "Long-Sleve", "Longsleve", "LS"],
    "Sweatshirt":      ["Crewneck", "Crew Neck"],
    "Sweater":         ["Knit Sweater"],
    "V-Neck":          ["V Neck", "V-neck"],
    "Tank Top":        ["Tank", "Tanktop", "Racerback"],
    "Tee":             ["T-Shirt", "Shirt", "Tshirt"],
    "Crocs":           ["Clog", "Clogs", "Croc"],
    "Shoes":           ["Canvas Shoes", "Sneakers", "Boots", "Slip-On", "Footwear"],
    "Mug":             ["Coffee Mug", "Ceramic Mug"],
    "Tumbler":         ["Travel Mug", "Insulated Tumbler"],
    "Canvas":          ["Canvas Print", "Canvas Wall Art", "Wrapped Canvas"],
    "Poster":          ["Art Print", "Wall Print"],
    "Rugs":            ["Rug", "Area Rug", "Floor Mat"],
    "Phone Case":      ["iPhone Case", "Samsung Case", "Mobile Case"],
}

# ── Noise words để strip khỏi tên file (brand, model, suffix rác) ─────────────
NOISE_WORDS = sorted([
    # Brand names
    "gildan", "bella", "canvas", "next level", "comfort colors", "hanes",
    "anvil", "port authority", "american apparel", "district", "champion",
    "independent", "trading", "co",
    # Model numbers phổ biến
    "5000", "3001", "3413", "64000", "6004", "4980", "8000",
    "11oz", "15oz", "20oz", "30oz", "12oz",
    # Mockup suffixes
    "mockup", "mock", "result", "mockup_result", "preview",
    "front", "back", "side", "flat", "lay",
    "transparent", "bg", "nobg",
], key=lambda x: -len(x))

# Mode rename
RENAME_MODE_CLASSIC  = "classic"   # Mode 1: bỏ "Color - " prefix (behavior cũ)
RENAME_MODE_AUTODETECT = "autodetect"  # Mode 2: detect Color + ProductType từ tên file

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def strip_color_prefix(name: str) -> str:
    for color in COLORS_SORTED:
        pattern = rf"^{re.escape(color)}\s*[-–]\s*"
        result = re.sub(pattern, "", name, flags=re.IGNORECASE)
        if result != name:
            return result.strip()
    return name.strip()


def strip_product_suffix(folder_name: str) -> str:
    for pt in PRODUCT_TYPES:
        pattern = rf"\s*{re.escape(pt)}\s*$"
        result = re.sub(pattern, "", folder_name, flags=re.IGNORECASE)
        if result != folder_name:
            return result.strip()
    return folder_name.strip()


def get_title_product_type(title: str):
    for pt in PRODUCT_TYPES:
        pattern = rf"\s*{re.escape(pt)}\s*$"
        if re.search(pattern, title, flags=re.IGNORECASE):
            return pt
    return None


def resolve_product_type(file_product_type: str, title_product_type) -> str:
    if title_product_type is None:
        return file_product_type
    if file_product_type.lower() == title_product_type.lower():
        return title_product_type
    title_group = {title_product_type.lower()}
    for alias in PRODUCT_ALIASES.get(title_product_type, []):
        title_group.add(alias.lower())
    if file_product_type.lower() in title_group:
        return title_product_type
    return file_product_type


def filename_to_product_title(filename: str) -> str:
    name = filename.rsplit('.', 1)[0]
    remove_patterns = [
        r'-women-tee$', r'-men-tee$', r'-kids-tee$', r'-unisex-tee$',
        r'-hoodie$', r'-sweatshirt$', r'-tank-top$', r'-long-sleeve$',
        r'-tshirt$', r'-t-shirt$', r'-shirt$'
    ]
    for p in remove_patterns:
        name = re.sub(p, '', name, flags=re.IGNORECASE)
    return name.replace('-', ' ').title()

# ─── MODE 2: AUTO-DETECT ─────────────────────────────────────────────────────

def _strip_leading_index(name: str) -> str:
    """Bỏ số thứ tự ở đầu: '01.', '02_', '3-', '04 ' → bỏ."""
    return re.sub(r"^\d{1,3}[.\-_ ]+", "", name).strip()


def _normalize(name: str) -> str:
    """
    Chuẩn hoá separator thành space.
    Chỉ thay '_' và '.' thành space.
    Giữ nguyên '-' (T-Shirt, V-Neck giữ đúng dạng).
    Separator '-' đứng một mình (Black-Hoodie) cũng giữ
    để _find_product_type match được "T-Shirt".
    Sau đó strip các space thừa.
    """
    # Thay _ và . thành space, KHÔNG thay - vì T-Shirt cần giữ
    name = re.sub(r"[_.]", " ", name)
    return re.sub(r" +", " ", name).strip()


def _strip_noise(name: str) -> str:
    """Bỏ các brand name, model number, mockup suffix."""
    result = name
    for noise in NOISE_WORDS:
        pattern = rf"(?<![a-zA-Z]){re.escape(noise)}(?![a-zA-Z])"
        result = re.sub(pattern, " ", result, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", result).strip()


def _find_product_type(name: str) -> tuple[str | None, str]:
    """
    Tìm product type trong name (đã normalize).
    Ưu tiên type dài nhất (Canvas Shoes > Shoes > Canvas).
    Trả về (matched_canonical, name_với_type_đã_bỏ).
    """
    name_lower = name.lower()

    # Check canonical types trước (đã sort dài → ngắn)
    for pt in PRODUCT_TYPES:
        pattern = rf"(?<![a-zA-Z]){re.escape(pt)}(?![a-zA-Z])"
        if re.search(pattern, name_lower, flags=re.IGNORECASE):
            stripped = re.sub(pattern, " ", name, flags=re.IGNORECASE)
            return pt, re.sub(r"\s+", " ", stripped).strip()

    # Check aliases
    for canonical, aliases in PRODUCT_ALIASES.items():
        for alias in aliases:
            pattern = rf"(?<![a-zA-Z]){re.escape(alias)}(?![a-zA-Z])"
            if re.search(pattern, name_lower, flags=re.IGNORECASE):
                stripped = re.sub(pattern, " ", name, flags=re.IGNORECASE)
                return canonical, re.sub(r"\s+", " ", stripped).strip()

    return None, name


def _find_color(name: str) -> tuple[str | None, str]:
    """
    Tìm color trong name (đã normalize, đã bỏ product type).
    Ưu tiên color dài nhất (Royal Blue > Blue).
    Trả về (matched_color, name_với_color_đã_bỏ).
    """
    for color in COLORS_SORTED:
        pattern = rf"(?<![a-zA-Z]){re.escape(color)}(?![a-zA-Z])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            stripped = re.sub(pattern, " ", name, flags=re.IGNORECASE)
            return color, re.sub(r"\s+", " ", stripped).strip()
    return None, name


def autodetect_rename(filename: str, folder_base: str,
                      log_fn=None) -> str | None:
    """
    Mode 2: Auto-detect Color + ProductType từ tên file.
    Output: '{folder_base} {Color} {ProductType}.{ext}'
    Fallback: None (giữ nguyên tên gốc).

    Pipeline đúng:
      1. Bỏ số thứ tự
      2. Normalize separator (giữ dấu - trong T-Shirt, V-Neck)
      3. Tìm ProductType (dài nhất ưu tiên) — TRƯỚC khi strip noise
         vì noise "canvas" không được nuốt "Canvas Shoes"
      4. Tìm Color trong phần còn lại
      5. Strip noise chỉ để verify (không ảnh hưởng result)
      6. Build output

    Ví dụ:
      '02.Black Gildan 5000 T-Shirt Mockup.jpg' + 'Design Name'
      → 'Design Name Black T-Shirt.jpg'
    """
    name_noext, ext = os.path.splitext(filename)

    # Bước 1: Bỏ số thứ tự đầu
    name = _strip_leading_index(name_noext)

    # Bước 2: Normalize separator
    name = _normalize(name)

    # Bước 3: Tìm ProductType TRƯỚC (trước khi strip noise)
    product_type, name_after_pt = _find_product_type(name)

    # Bước 4: Tìm Color trong phần còn lại (sau khi đã bỏ product type)
    # Strip noise chỉ để clean phần còn lại khi tìm color
    name_for_color = _strip_noise(name_after_pt)
    color, _ = _find_color(name_for_color)

    # Nếu không tìm thấy color trong phần cleaned, thử tìm trong raw
    if not color:
        color, _ = _find_color(name_after_pt)

    # Bước 5: Build output
    if not product_type and not color:
        if log_fn:
            log_fn(f"  ⚠ Không nhận diện được — giữ nguyên: {filename}")
        return None

    parts = [folder_base]
    if color:
        parts.append(color)
    if product_type:
        parts.append(product_type)

    new_name = " ".join(parts) + ext
    return new_name


# ─── CORE FUNCTIONS ──────────────────────────────────────────────────────────

def rename_images_in_folder(folder_path: str, product_title: str = "",
                             log_fn=None,
                             mode: str = RENAME_MODE_CLASSIC) -> list:
    """
    Rename ảnh trong folder.
    mode = RENAME_MODE_CLASSIC:    bỏ 'Color - ' prefix (behavior cũ)
    mode = RENAME_MODE_AUTODETECT: detect Color + ProductType từ tên file

    log_fn: callable(msg: str) — optional callback để ghi log
    Trả về list các (old_path, new_path).
    """
    folder_name = os.path.basename(folder_path.rstrip("/\\"))
    title_for_base = product_title if product_title else folder_name
    base_name = strip_product_suffix(title_for_base)
    title_pt  = get_title_product_type(title_for_base)

    renamed = []
    for fname in sorted(os.listdir(folder_path)):
        if not fname.lower().endswith(IMAGE_EXTS_INPUT):
            continue

        old_path = os.path.join(folder_path, fname)

        # ── Mode 2: Auto-detect ───────────────────────────────────────────────
        if mode == RENAME_MODE_AUTODETECT:
            new_name = autodetect_rename(fname, base_name, log_fn=log_fn)
            if new_name is None:
                # Fallback: giữ nguyên
                renamed.append((old_path, old_path))
                continue
            new_path = os.path.join(folder_path, new_name)
            if old_path == new_path:
                if log_fn:
                    log_fn(f"  − {fname} (không đổi)")
                renamed.append((old_path, new_path))
                continue
            if os.path.exists(new_path):
                if log_fn:
                    log_fn(f"  ⚠ Bỏ qua (đã tồn tại): {new_name}")
                continue
            try:
                os.rename(old_path, new_path)
                if log_fn:
                    log_fn(f"  ✎ {fname}  →  {new_name}")
                renamed.append((old_path, new_path))
            except Exception as e:
                if log_fn:
                    log_fn(f"  ✗ Lỗi rename {fname}: {e}")
            continue

        # ── Mode 1: Classic ───────────────────────────────────────────────────
        name_noext, ext = os.path.splitext(fname)
        raw_pt   = strip_color_prefix(name_noext)
        final_pt = resolve_product_type(raw_pt, title_pt)
        new_name = f"{base_name} {final_pt}{ext}"
        old_path = os.path.join(folder_path, fname)
        new_path = os.path.join(folder_path, new_name)

        if old_path == new_path:
            if log_fn:
                log_fn(f"  − {fname} (không đổi)")
            renamed.append((old_path, new_path))
            continue
        if os.path.exists(new_path):
            if log_fn:
                log_fn(f"  ⚠ Bỏ qua (đã tồn tại): {new_name}")
            continue
        try:
            os.rename(old_path, new_path)
            if log_fn:
                log_fn(f"  ✎ {fname}  →  {new_name}")
            renamed.append((old_path, new_path))
        except Exception as e:
            if log_fn:
                log_fn(f"  ✗ Lỗi rename {fname}: {e}")
    return renamed


def _encode_xp(text: str) -> bytes:
    """Encode string sang UCS-2 LE bytes cho Windows XP EXIF fields."""
    return text.encode("utf-16-le") + b"\x00\x00"


def add_professional_metadata(image_path: str, original_filename: str,
                               product_title: str, brand: str,
                               rating: int = 5, date_taken_days: int = 7,
                               log_fn=None) -> bool:
    """
    Ghi EXIF metadata chuyên nghiệp vào file JPG bằng piexif.
    Trả về True nếu thành công.
    log_fn: callable(msg) để hiện lỗi ra UI.
    """
    def _log(msg):
        print(msg)
        if log_fn:
            log_fn(msg)

    try:
        import piexif

        now = datetime.now() - timedelta(days=date_taken_days)
        date_format = now.strftime('%Y:%m:%d %H:%M:%S')
        raw = uuid.uuid4().hex.upper()
        image_unique_id = f"{raw[:3]}{raw[3:6]}-{raw[6:9]}{raw[9:12]}"

        zeroth = {
            piexif.ImageIFD.ImageDescription:  original_filename.encode("utf-8"),
            piexif.ImageIFD.Artist:            brand.encode("utf-8"),
            piexif.ImageIFD.Copyright:         brand.encode("utf-8"),
            piexif.ImageIFD.Software:          b"Adobe Photoshop 23.0 (Windows)",
            piexif.ImageIFD.XResolution:       (300, 1),
            piexif.ImageIFD.YResolution:       (300, 1),
            piexif.ImageIFD.ResolutionUnit:    2,
            piexif.ImageIFD.Rating:            rating,
            piexif.ImageIFD.XPTitle:           _encode_xp(original_filename),
            piexif.ImageIFD.XPComment:         _encode_xp(f"Official {product_title}"),
            piexif.ImageIFD.XPKeywords:        _encode_xp(f"{brand};shirt"),
            piexif.ImageIFD.XPAuthor:          _encode_xp(brand),
            piexif.ImageIFD.XPSubject:         _encode_xp(original_filename),
        }
        exif = {
            piexif.ExifIFD.DateTimeOriginal:   date_format.encode("utf-8"),
            piexif.ExifIFD.DateTimeDigitized:  date_format.encode("utf-8"),
            piexif.ExifIFD.ImageUniqueID:      image_unique_id.encode("utf-8"),
        }
        exif_bytes = piexif.dump({"0th": zeroth, "Exif": exif})
        piexif.insert(exif_bytes, image_path)
        return True
    except Exception as e:
        _log(f"  ✗ Metadata lỗi: {e}")
        return False


def compress_one(file: str, out_dir: str, product_title: str,
                 brand: str, basewidth: int = 1000, quality: int = 90,
                 rating: int = 5, date_taken_days: int = 7,
                 log_fn=None) -> tuple:
    """
    Nén 1 file ảnh: (WebP trick) → JPG + EXIF metadata.
    Trả về (out_path: str, error: str|None).
    log_fn: callable(msg: str)
    """
    path_webp = None
    try:
        original_filename = os.path.basename(file)
        if not original_filename.lower().endswith('.jpg'):
            original_filename = os.path.splitext(original_filename)[0] + ".jpg"

        stem      = os.path.splitext(os.path.basename(file))[0].replace("'", "\u2019")
        path_webp = os.path.normpath(os.path.join(out_dir, f"{stem}.webp"))
        path_jpg  = os.path.normpath(os.path.join(out_dir, original_filename))
        size_orig = os.path.getsize(file)

        # Convert → WebP → JPG (compression trick)
        im = Image.open(file).convert("RGB")
        im.save(path_webp, "webp")

        im = Image.open(path_webp).convert("RGB")
        if im.size[0] > basewidth:
            wpct  = basewidth / float(im.size[0])
            hsize = int(im.size[1] * wpct)
            im    = im.resize((basewidth, hsize), LANCZOS)

        im.save(path_jpg, "jpeg", quality=quality, optimize=True)
        size_new = os.path.getsize(path_jpg)

        # Metadata
        final_title = product_title if product_title else filename_to_product_title(original_filename)
        ok = add_professional_metadata(
            path_jpg,
            original_filename=original_filename,
            product_title=final_title,
            brand=brand,
            rating=rating,
            date_taken_days=date_taken_days,
            log_fn=log_fn,
        )
        if not ok and log_fn:
            log_fn(f"  ⚠ Metadata không ghi được cho: {os.path.basename(path_jpg)}")

        if path_webp and os.path.exists(path_webp):
            os.remove(path_webp)

        reduction = (size_orig - size_new) / size_orig * 100
        if log_fn:
            log_fn(f"  ✓ {original_filename}  (↓{reduction:.1f}%)")
        return path_jpg, None

    except Exception as e:
        if path_webp and os.path.exists(path_webp):
            try:
                os.remove(path_webp)
            except Exception:
                pass
        msg = f"  ✗ Lỗi: {os.path.basename(file)} — {e}"
        if log_fn:
            log_fn(msg)
        return None, str(e)


# ─── BATCH PROCESSOR ─────────────────────────────────────────────────────────

class ImageBatchProcessor:
    """
    Xử lý batch folder: Rename → Compress → Metadata.
    Dùng trong QThread — không import Tkinter.

    Callbacks:
      log_fn(msg: str)           — ghi log từng dòng
      progress_fn(current, total, msg) — cập nhật progress bar
      stop_fn() -> bool          — trả về True nếu user bấm Dừng
    """

    def __init__(self, folder: str, brand: str,
                 basewidth: int = 1000, quality: int = 90,
                 rating: int = 5, date_taken_days: int = 7,
                 do_rename: bool = True,
                 rename_mode: str = RENAME_MODE_CLASSIC,
                 log_fn=None, progress_fn=None, stop_fn=None):
        self.folder          = os.path.normpath(folder)
        self.brand           = brand
        self.basewidth       = basewidth
        self.quality         = quality
        self.rating          = rating
        self.date_taken_days = date_taken_days
        self.do_rename       = do_rename
        self.rename_mode     = rename_mode
        self.log_fn          = log_fn or (lambda m: None)
        self.progress_fn     = progress_fn or (lambda c, t, m: None)
        self.stop_fn         = stop_fn or (lambda: False)

    def _log(self, msg: str):
        self.log_fn(msg)

    def run(self) -> dict:
        """
        Chạy toàn bộ batch.
        Trả về {"processed": int, "errors": int, "output": str}
        """
        master  = self.folder
        parent  = os.path.dirname(master)
        fname   = os.path.basename(master)
        output  = os.path.normpath(os.path.join(parent, f"{fname}_compress"))
        os.makedirs(output, exist_ok=True)

        self._log("=" * 60)
        self._log(f"🚀 Bắt đầu xử lý ảnh...")
        self._log("=" * 60)

        # Đếm tổng file để progress
        all_items = sorted(glob.glob(os.path.join(master, "*")))
        # Đếm tổng ảnh (bao gồm trong sub-folder)
        total_files = 0
        for item in all_items:
            if os.path.isdir(item):
                total_files += sum(
                    1 for f in os.listdir(item)
                    if f.lower().endswith(IMAGE_EXTS_INPUT)
                )
            elif os.path.isfile(item) and item.lower().endswith(IMAGE_EXTS_INPUT):
                total_files += 1

        processed = 0
        errors    = 0
        done      = 0

        for item in all_items:
            if self.stop_fn():
                self._log("⛔ Đã dừng bởi người dùng.")
                break

            if os.path.isdir(item):
                sub_basename = os.path.basename(item)
                out_sub      = os.path.normpath(os.path.join(output, sub_basename))
                os.makedirs(out_sub, exist_ok=True)

                self._log(f"\n📁 {sub_basename}")
                auto_title = sub_basename

                # Step 1 — Rename
                if self.do_rename:
                    self._log("  ── Rename ──")
                    rename_images_in_folder(item, product_title=auto_title,
                                            log_fn=self.log_fn,
                                            mode=self.rename_mode)

                # Step 2 — Compress + Metadata
                self._log("  ── Compress + Metadata ──")
                for file in sorted(glob.glob(os.path.join(item, "*"))):
                    if self.stop_fn():
                        break
                    if not file.lower().endswith(IMAGE_EXTS_INPUT):
                        continue
                    done += 1
                    self.progress_fn(done, total_files,
                                     f"⏳ {os.path.basename(file)}")
                    _, err = compress_one(
                        file, out_sub, auto_title,
                        brand=self.brand,
                        basewidth=self.basewidth,
                        quality=self.quality,
                        rating=self.rating,
                        date_taken_days=self.date_taken_days,
                        log_fn=self.log_fn,
                    )
                    if err:
                        errors += 1
                    else:
                        processed += 1

            elif os.path.isfile(item):
                if not item.lower().endswith(IMAGE_EXTS_INPUT):
                    continue

                self._log(f"\n📄 {os.path.basename(item)}")
                auto_title = fname  # tên thư mục cha

                # Rename file đơn lẻ
                if self.do_rename:
                    name_noext, ext = os.path.splitext(os.path.basename(item))
                    raw_pt      = strip_color_prefix(name_noext)
                    parent_base = strip_product_suffix(auto_title)
                    title_pt    = get_title_product_type(auto_title)
                    final_pt    = resolve_product_type(raw_pt, title_pt)
                    new_fname   = f"{parent_base} {final_pt}{ext}"
                    new_fpath   = os.path.join(master, new_fname)
                    if item != new_fpath and not os.path.exists(new_fpath):
                        os.rename(item, new_fpath)
                        self._log(f"  ✎ {os.path.basename(item)} → {new_fname}")
                        item = new_fpath

                done += 1
                self.progress_fn(done, total_files, f"⏳ {os.path.basename(item)}")
                _, err = compress_one(
                    item, output, auto_title,
                    brand=self.brand,
                    basewidth=self.basewidth,
                    quality=self.quality,
                    rating=self.rating,
                    date_taken_days=self.date_taken_days,
                    log_fn=self.log_fn,
                )
                if err:
                    errors += 1
                else:
                    processed += 1

        # Dọn webp thừa
        for f in glob.glob(os.path.join(output, "**", "*.webp"), recursive=True):
            try:
                os.remove(f)
            except Exception:
                pass

        self._log("=" * 60)
        self._log(f"✅ Xử lý ảnh xong — {processed} file, {errors} lỗi")
        self._log("=" * 60)

        return {"processed": processed, "errors": errors, "output": output}

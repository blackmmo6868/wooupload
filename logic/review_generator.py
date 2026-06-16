"""
WooMMO — Review Generator
Dùng OpenAI GPT-4o Vision để tạo fake reviews từ ảnh sản phẩm + tên sản phẩm.
"""

import csv
import io
import re
import time
import requests
from datetime import datetime


# ── OpenAI API call ────────────────────────────────────────────────────────────

def _call_openai(api_key: str, system_prompt: str,
                 user_text: str, image_b64: str) -> str:
    """
    Gọi GPT-4o với vision qua OpenAI REST API.
    Trả về text response hoặc raise Exception.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Build message content
    user_content = []

    # Ảnh sản phẩm (nếu có)
    if image_b64:
        # Đảm bảo có data URI prefix
        if not image_b64.startswith("data:"):
            image_b64 = "data:image/jpeg;base64," + image_b64

        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": image_b64,
                "detail": "low",   # "low" đủ để nhận diện màu sắc/design, tiết kiệm token
            },
        })

    user_content.append({
        "type": "text",
        "text": user_text,
    })

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        "temperature": 1.0,
        "max_tokens": 8192,
    }

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )

    if r.status_code != 200:
        raise Exception(f"OpenAI API error {r.status_code}: {r.text[:400]}")

    data = r.json()
    choices = data.get("choices", [])
    if not choices:
        raise Exception("OpenAI trả về 0 choices")

    return choices[0]["message"]["content"].strip()


# ── Build system prompt ────────────────────────────────────────────────────────

def _build_system_prompt(product_id: int, product_name: str,
                         review_count: int,
                         start_date: str, end_date: str,
                         dist_5: int, dist_4: int, dist_3: int) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dist_3_rule = "DO NOT generate ANY 3-star reviews — dist_3=0%" if dist_3 == 0 else f"3-star reviews allowed ({dist_3}%)"
    dist_4_rule = "DO NOT generate ANY 4-star reviews — dist_4=0%" if dist_4 == 0 else f"4-star reviews allowed ({dist_4}%)"
    return f"""You are a review generation engine for WooCommerce.
Write reviews that are completely indistinguishable from real verified buyers.

==================================================
CSV FORMAT & HEADER (CRITICAL)
==================================================
- Output MUST be valid CSV. Start DIRECTLY with the header — no preamble, no markdown.
- Line 1 MUST be exactly:
Comment ID,Product ID,Author name,Author email,Author URL,Content,Comment status,Rating,Verified,Photos,Optional fields/Variations,Review title,Up-vote count,Down-vote count,Comment parent,User id,Author IP,Comment agent,Comment date,Comment date gmt

==================================================
ROW STRUCTURE (exactly 19 commas per row)
==================================================
[ID],[PID],"[Name]",[Email],,"[Content]",approved,[Rating],1,,,"[Title]",[Up],[Down],0,0,[IP],"[Agent]",[Date],[Date]

THREE commas between '1' and "[Title]": CORRECT: 1,,,"Title" / WRONG: 1,,,,"Title"

==================================================
COLUMNS
==================================================
1.  Comment ID: unique integer from 1.
2.  Product ID: {product_id}.
3.  Author name: quoted, realistic US first+last name.
4.  Author email: unquoted, realistic (gmail/yahoo/hotmail/outlook mix).
5.  Author URL: always empty.
6.  Content: quoted review text — see CONTENT RULES below.
7.  Comment status: approved.
8.  Rating: 3, 4, or 5.
9.  Verified: 1.
10. Photos: always empty.
11. Optional fields/Variations: always empty.
12. Review title: quoted, 3-8 words — see TITLE RULES below.
13. Up-vote count: integer.
14. Down-vote count: integer.
15. Comment parent: 0.
16. User id: 0.
17. Author IP: realistic US public IP (vary prefixes: 24.x, 67.x, 73.x, 98.x, 104.x, 172.x).
18. Comment agent: quoted realistic browser UA string (mix Chrome/Firefox/Safari, Windows/Mac/iPhone).
19. Comment date: YYYY-MM-DD HH:MM:SS.
20. Comment date gmt: identical to col 19.

==================================================
CONTENT RULES (most important)
==================================================
- Examine the product image carefully. Write about what you ACTUALLY SEE:
  specific graphic elements, colors, text on the item, art style, layout.
- Each review must reference at least one concrete visual detail unique to this product.
- VARY sentence structure naturally — some reviews start with "Ordered this...", 
  "Got it as a gift...", "Wasn't sure at first...", "My husband loved...", etc.
- Mix review lengths organically: 1 sentence (20%), 2-3 sentences (50%), 4-5 sentences (30%).
- Avoid repeating the same sentence openings across reviews.
- About 5% of reviews may have minor imperfections: casual phrasing, slight abbreviation,
  or informal tone (e.g. "tbh", "lowkey", missing a period). Do NOT add typos.
- Avoid overusing generic phrases; use them sparingly if natural: "comfortable", "fits well".

==================================================
TITLE RULES
==================================================
- Mix title styles naturally:
  * Short noun phrase: "Great graphic tee", "Bold statement shirt"
  * Reaction phrase: "Exactly what I wanted", "Better than expected"  
  * Specific detail: "Love the crown graphic", "Missouri pride"
  * Casual: "Solid purchase", "Really happy with this"
- Avoid every title following the same Adjective+Noun pattern.

==================================================
RATING BEHAVIOR (HARD RULES — STRICTLY ENFORCED)
==================================================
- 5★ ({dist_5}%): enthusiastic, expressive, specific praise.
- 4★ ({dist_4}%): mostly positive with one small nitpick (sizing, shipping time, etc).
- 3★ ({dist_3}%): genuinely mixed — mention at least one clear downside or hesitation.

CRITICAL RATING RULES:
- If a rating percentage is 0%, you MUST NOT generate ANY review with that rating. ZERO means ZERO.
- {dist_3_rule}
- {dist_4_rule}
- The exact counts must match the percentages: for {review_count} reviews,
  generate exactly round({dist_5}/100 * {review_count}) five-star reviews,
  exactly round({dist_4}/100 * {review_count}) four-star reviews,
  and exactly round({dist_3}/100 * {review_count}) three-star reviews.
- Double-check your rating column before outputting — no exceptions.

==================================================
VOTING REALISM
==================================================
- 60% of reviews: Up=0, Down=0.
- 5★ with votes: Up 2-8, Down 0-1. Up MUST > Down.
- 4★ with votes: Up 1-5, Down 0-1. Up MUST > Down.
- 3★ with votes: Up 0-3, Down 0-2. Can be equal.
- NEVER Down > Up for 4★ or 5★.

==================================================
DATE RULES
==================================================
- Spread randomly between {start_date} and {end_date}.
- NO dates after {now_str}.
- GMT column = date column exactly.

==================================================
FORMAT RULES (non-negotiable)
==================================================
- NO preamble. NO markdown fences. Start with the header line.
- EXACTLY 19 commas per data row.
- Rating distribution: ~{dist_5}% five-star, ~{dist_4}% four-star, ~{dist_3}% three-star.

Product ID: {product_id}
Product Name: {product_name}
Total reviews to generate: {review_count}
Date range: {start_date} to {end_date}"""


# ── Parse CSV thành list of dicts ──────────────────────────────────────────────

def _parse_csv_to_reviews(csv_text: str, product_id: int) -> list:
    """
    Parse CSV output của GPT-4o thành list of review dicts.
    """
    # Strip markdown fences nếu model vẫn thêm vào
    text = re.sub(r"^```(?:csv)?\s*", "", csv_text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    reader  = csv.DictReader(io.StringIO(text))
    reviews = []

    for row in reader:
        try:
            # Safe int parse
            def _int(val, default=0):
                try:
                    return int(str(val).strip().strip('"') or default)
                except (ValueError, TypeError):
                    return default

            review = {
                "product_id":   product_id,
                "author":       row.get("Author name",    "Anonymous").strip().strip('"'),
                "email":        row.get("Author email",   "").strip(),
                "author_ip":    row.get("Author IP",      "").strip(),
                "author_agent": row.get("Comment agent",  "").strip().strip('"'),
                "content":      row.get("Content",        "").strip().strip('"'),
                "title":        row.get("Review title",   "").strip().strip('"'),
                "rating":       _int(row.get("Rating", 5), 5),
                "date":         row.get("Comment date",   "").strip(),
                "up_votes":     _int(row.get("Up-vote count",   0), 0),
                "down_votes":   _int(row.get("Down-vote count", 0), 0),
            }

            if not review["content"] or not review["date"]:
                continue
            if review["rating"] not in (1, 2, 3, 4, 5):
                review["rating"] = 5

            reviews.append(review)
        except Exception:
            continue

    return reviews


# ── Main public function ───────────────────────────────────────────────────────

def generate_reviews_for_product(
    openai_api_key: str,
    product_id: int,
    product_name: str,
    image_b64: str,
    review_count: int = 15,
    start_date: str = "2024-01-01",
    end_date: str = "2025-01-01",
    dist_5: int = 60,
    dist_4: int = 30,
    dist_3: int = 10,
    max_retries: int = 2,
) -> list:
    """
    Generate reviews cho 1 sản phẩm bằng GPT-4o Vision.
    Trả về list of review dicts sẵn sàng import.
    Raises Exception nếu tất cả retries đều thất bại.
    """
    # Normalize distribution — giữ 0 nguyên, không round về số dương
    total = dist_5 + dist_4 + dist_3
    if total != 100 and total > 0:
        if dist_3 == 0:
            # Chỉ chia 5★ và 4★
            t = dist_5 + dist_4
            dist_5 = round(dist_5 / t * 100) if t > 0 else 100
            dist_4 = 100 - dist_5
            dist_3 = 0
        else:
            dist_5 = round(dist_5 / total * 100)
            dist_4 = round(dist_4 / total * 100)
            dist_3 = 100 - dist_5 - dist_4

    system_prompt = _build_system_prompt(
        product_id=product_id,
        product_name=product_name,
        review_count=review_count,
        start_date=start_date,
        end_date=end_date,
        dist_5=dist_5,
        dist_4=dist_4,
        dist_3=dist_3,
    )

    user_text = (
        f'Generate exactly {review_count} unique WooCommerce reviews for '
        f'"{product_name}" (Product ID: {product_id}). '
        f'Carefully examine the product image and mention specific visual details '
        f'(colors, graphics, artwork, text printed on the item) in the reviews. '
        f'Output ONLY the CSV — start directly with the header line, no preamble, no markdown.'
    )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            csv_text = _call_openai(
                api_key=openai_api_key,
                system_prompt=system_prompt,
                user_text=user_text,
                image_b64=image_b64,
            )
            reviews = _parse_csv_to_reviews(csv_text, product_id)
            if reviews:
                # Filter bỏ rating không được phép theo distribution
                allowed_ratings = set()
                if dist_5 > 0: allowed_ratings.add(5)
                if dist_4 > 0: allowed_ratings.add(4)
                if dist_3 > 0: allowed_ratings.add(3)
                if allowed_ratings:
                    before = len(reviews)
                    reviews = [r for r in reviews if r["rating"] in allowed_ratings]
                    if len(reviews) < before:
                        print(f"[Review] Filtered {before - len(reviews)} reviews with disallowed ratings")
                return reviews
            last_error = "CSV parse trả về 0 reviews"
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                time.sleep(3 * (attempt + 1))

    raise Exception(f"OpenAI thất bại sau {max_retries + 1} lần: {last_error}")

# ── Batch generate (dùng khi review_count > BATCH_SIZE) ───────────────────────

BATCH_SIZE = 15   # Max reviews per single API call — giữ response nhanh < 60s

def generate_reviews_for_product_batched(
    openai_api_key: str,
    product_id: int,
    product_name: str,
    image_b64: str,
    review_count: int = 15,
    start_date: str = "2024-01-01",
    end_date: str = "2025-01-01",
    dist_5: int = 60,
    dist_4: int = 30,
    dist_3: int = 10,
    progress_callback=None,   # callback(current_batch, total_batches, msg)
) -> list:
    """
    Generate reviews theo batch nhỏ (mỗi batch BATCH_SIZE reviews).
    Tránh timeout khi review_count lớn (>20).
    progress_callback(batch_idx, total_batches, message) để update UI.
    """
    import math

    # Normalize distribution — giữ 0 nguyên
    total_dist = dist_5 + dist_4 + dist_3
    if total_dist != 100 and total_dist > 0:
        if dist_3 == 0:
            t = dist_5 + dist_4
            dist_5 = round(dist_5 / t * 100) if t > 0 else 100
            dist_4 = 100 - dist_5
            dist_3 = 0
        else:
            dist_5 = round(dist_5 / total_dist * 100)
            dist_4 = round(dist_4 / total_dist * 100)
            dist_3 = 100 - dist_5 - dist_4

    # Chia thành các batch
    total_batches = math.ceil(review_count / BATCH_SIZE)
    all_reviews   = []

    for batch_idx in range(total_batches):
        remaining    = review_count - len(all_reviews)
        batch_count  = min(BATCH_SIZE, remaining)

        if progress_callback:
            progress_callback(
                batch_idx + 1, total_batches,
                f"Batch {batch_idx + 1}/{total_batches}: generating {batch_count} reviews..."
            )

        try:
            batch = generate_reviews_for_product(
                openai_api_key=openai_api_key,
                product_id=product_id,
                product_name=product_name,
                image_b64=image_b64,
                review_count=batch_count,
                start_date=start_date,
                end_date=end_date,
                dist_5=dist_5,
                dist_4=dist_4,
                dist_3=dist_3,
                max_retries=2,
            )
            all_reviews.extend(batch)
        except Exception as e:
            # Nếu 1 batch lỗi → log nhưng tiếp tục batch tiếp theo
            if progress_callback:
                progress_callback(batch_idx + 1, total_batches,
                                  f"⚠️ Batch {batch_idx + 1} lỗi: {e}")

        # Delay nhỏ giữa các batch tránh rate limit
        if batch_idx < total_batches - 1:
            time.sleep(1.5)

    if not all_reviews:
        raise Exception("Tất cả batches đều thất bại — không có review nào được tạo.")

    return all_reviews

"""
WooMMO — Link Resolver (Public Edition)

Thay đổi so với v5:
  - Không hardcode domain nào
  - Nhận user_links từ credentials.get_links_for_store()
  - Hỗ trợ 2 mode: CATEGORY (1 link danh mục/niche) và PRODUCT (pool sản phẩm)
  - Round-robin index được quản lý bởi caller (BulkSEOWorker)
  - AI tự chọn anchor text — không truyền anchor cứng vào prompt
"""

import re
import random


# ══════════════════════════════════════════════════════════════════════════════
# KEYWORD MAPS
# ══════════════════════════════════════════════════════════════════════════════

OCCASION_KEYWORDS = {
    "fathers_day":  ["father's day", "fathers day", "father day", "dad gift",
                     "for dad", "best dad", "daddy", "papa", "father gift", "father",
                     "dog dad", "cat dad", "plant dad", "girl dad", "boy dad"],
    "mothers_day":  ["mother's day", "mothers day", "mom gift", "for mom", "best mom",
                     "mommy", "mama", "mother gift"],
    "valentines":   ["valentine", "valentines day", "valentine's day", "love gift",
                     "couples", "girlfriend gift", "boyfriend gift"],
    "st_patricks":  ["st patrick", "saint patrick", "patricks day", "st paddy", "irish"],
    "veterans":     ["veteran", "veterans day", "military", "army", "navy", "marines",
                     "air force", "coast guard", "soldier", "service member"],
    "thanksgiving": ["thanksgiving", "turkey day", "gobble"],
    "halloween":    ["halloween", "spooky", "skeleton", "ghost", "witch", "pumpkin",
                     "scary", "horror", "trick or treat"],
    "christmas":    ["christmas", "xmas", "santa", "holiday gift", "holiday tee",
                     "ugly sweater", "reindeer", "elf"],
}

SPORT_KEYWORDS = {
    "college_football": {
        "keys": ["college football", "ncaa football", "sec football", "big ten",
                 "bowl game", "heisman", "crimson tide", "longhorns", "buckeyes",
                 "wolverines", "fighting irish", "sooners", "seminoles", "gators",
                 "volunteers", "bulldogs football", "tigers football"],
        "wiki": "https://en.wikipedia.org/wiki/College_football",
    },
    "football": {
        "keys": ["nfl", "quarterback", "touchdown", "super bowl", "football",
                 "wide receiver", "linebacker"],
        "wiki": "https://en.wikipedia.org/wiki/American_football",
    },
    "baseball": {
        "keys": ["baseball", "mlb", "pitcher", "batter", "home run", "strikeout",
                 "world series", "dugout", "bullpen", "yankees", "red sox",
                 "dodgers", "cubs", "braves", "cardinals baseball"],
        "wiki": "https://en.wikipedia.org/wiki/Baseball",
    },
    "basketball": {
        "keys": ["basketball", "nba", "dunk", "three pointer", "march madness",
                 "ncaa basketball", "slam dunk", "buzzer beater", "final four",
                 "huskies", "uconn", "wildcats", "tar heels", "blue devils",
                 "jayhawks", "spartans", "hoosiers", "cavaliers basketball",
                 "raptors", "lakers", "celtics", "bulls", "warriors", "heat",
                 "big 12", "big east", "sec basketball", "acc basketball",
                 "championship shirt", "champions shirt", "tournament",
                 "women's basketball", "mens basketball"],
        "wiki": "https://en.wikipedia.org/wiki/Basketball",
    },
    "hockey": {
        "keys": ["hockey", "nhl", "puck", "ice rink", "slap shot", "power play",
                 "goalie", "penalty box", "stanley cup"],
        "wiki": "https://en.wikipedia.org/wiki/Ice_hockey",
    },
}

NICHE_KEYWORDS = {
    "music":        ["rock", "band", "guitar", "drummer", "bassist", "vinyl", "album",
                     "concert", "metal", "punk", "jazz", "blues", "rap", "hip hop",
                     "country music", "musician", "singer", "songwriter", "riff", "tour",
                     "artist", "pop", "idol", "dj", "rapper",
                     "ariana", "taylor", "beyonce", "drake", "billie", "weeknd",
                     "olivia rodrigo", "post malone", "bad bunny", "harry styles"],
    "anime":        ["anime", "manga", "otaku", "cosplay", "kawaii", "chibi",
                     "naruto", "dragonball", "one piece", "attack on titan", "demon slayer",
                     "my hero academia", "sword art", "sailor moon", "ghibli"],
    "movie":        ["movie", "film", "cinema", "actor", "director", "sequel",
                     "blockbuster", "netflix", "tv show", "series", "episode", "season"],
    "political":    ["political", "president", "democrat", "republican", "liberal",
                     "conservative", "vote", "election", "congress", "senate",
                     "patriot", "freedom", "constitution", "liberty", "government"],
    "meme":         ["meme", "humor", "lol", "joke", "sarcastic", "sarcasm",
                     "hilarious", "comedy", "parody", "ironic", "viral", "dank",
                     "peanuts", "snoopy", "charlie brown", "garfield", "simpsons",
                     "looney tunes", "disney", "mickey", "minnie", "bugs bunny",
                     "tom and jerry", "scooby", "cartoon"],
    "nurse":        ["nurse", "nursing", "cna", "doctor", "medical", "hospital",
                     "scrubs", "stethoscope", "healthcare", "pharmacist", "therapist",
                     "dentist", "physician", "surgeon", "icu", "er nurse"],
    "motivational": ["motivational", "inspirational", "hustle", "grind", "success",
                     "mindset", "warrior", "strong", "overcome", "believe",
                     "achieve", "champion", "winner", "determination"],
    "vintage":      ["vintage", "retro", "classic", "old school", "throwback",
                     "70s", "80s", "90s", "nostalgic", "antique", "heritage"],
    "dog":          ["dog", "puppy", "corgi", "golden retriever", "labrador", "poodle",
                     "bulldog", "dachshund", "husky", "beagle", "pug", "chihuahua",
                     "dog mom", "dog dad", "dog lover", "fur baby", "rescue dog"],
    "cat":          ["cat", "kitten", "kitty", "feline", "tabby", "persian",
                     "siamese", "maine coon", "cat mom", "cat dad", "cat lover"],
}

# External links handled by AI directly in seo_generator.py prompt — no hardcode needed

HOOK_STYLES = {
    "music": [
        "Start with a specific concert memory or album moment — no intro, jump straight in",
        "Open with 2 short punchy sentences that only real fans understand",
        "Start with a fragment that captures the feeling of hearing that band for the first time",
        "Open with a direct statement about what this shirt means to someone who owns the vinyl",
    ],
    "anime": [
        "Start mid-sentence like you're already in the fandom conversation",
        "Open with a specific scene or moment from the series that fans recognize immediately",
        "2 short sentences — one about the character, one about what wearing this means",
        "Start with a fragment: just the feeling, no subject, no setup",
    ],
    "movie": [
        "Start with a specific scene reference that only real fans catch",
        "Open with what it feels like to watch that movie/show for the first time",
        "2 punchy sentences — the show, then what wearing this shirt signals",
    ],
    "sports": [
        "Start with a specific game moment — a play, a score, a season",
        "Open with what it means to be a fan of this team, no generic intro",
        "2 short sentences: the team's identity, then the shirt's meaning",
        "Start with a fragment that only season ticket holders understand",
    ],
    "political": [
        "Start with the point, no warm-up — direct and unapologetic",
        "Open with what this shirt says without saying it — the subtext",
        "Start with a short punchy line that gets the reaction immediately",
    ],
    "meme": [
        "Start mid-joke, like the punchline is already understood",
        "Open with the internet context — where this meme lives and why it hit",
        "Start with a fragment that IS the joke",
    ],
    "nurse": [
        "Start with a specific moment from the shift that every nurse knows",
        "2 short sentences about the grind, then the shirt",
        "Start with a fragment that colleagues will recognize immediately",
    ],
    "motivational": [
        "Start with the mindset, not the product — the feeling first",
        "Open with a direct challenge or declaration, no setup",
        "Start with a short line that sounds like a coach talking to the team",
    ],
    "vintage": [
        "Start with the nostalgia trigger — a specific era detail",
        "Open with what vintage means to someone who actually lived it",
        "Start with a fragment that sounds like a memory",
    ],
    "dog": [
        "Start with a specific dog behavior or moment every dog owner knows",
        "2 short sentences: the dog breed's personality, then the shirt",
        "Start with a fragment that dog parents immediately feel",
    ],
    "cat": [
        "Start with a specific cat behavior that every cat owner knows",
        "Open with the cat's attitude — aloof, judgemental, perfect",
        "Start with a fragment from the cat's perspective",
    ],
    "general": [
        "Start with a direct statement about who this shirt is for",
        "Open with a specific detail from the product name — no generic intro",
        "Start with a fragment — drop straight into the point",
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# DETECTORS
# ══════════════════════════════════════════════════════════════════════════════

def _n(t: str) -> str:
    return t.lower().strip()

def detect_occasion(name: str) -> str | None:
    n = _n(name)
    for occ, kws in OCCASION_KEYWORDS.items():
        if any(k in n for k in kws):
            return occ
    return None

def detect_sport(name: str) -> str | None:
    n = _n(name)
    # college_football check first (more specific)
    for k in SPORT_KEYWORDS["college_football"]["keys"]:
        if k in n:
            return "college_football"
    for sport, data in SPORT_KEYWORDS.items():
        if sport == "college_football":
            continue
        if any(k in n for k in data["keys"]):
            return sport
    return None

def detect_niche(name: str) -> str:
    sport = detect_sport(name)
    if sport:
        return sport
    n = _n(name)

    # HARD RULE: "wnba" → basketball safety
    if "wnba" in n:
        return "basketball"

    # Priority-based detection — nurse xuống cuối tránh nhầm "doctor strange"
    PRIORITY_ORDER = ["anime", "movie", "music", "political",
                      "motivational", "meme", "dog", "cat", "vintage", "nurse"]
    for niche in PRIORITY_ORDER:
        if niche not in NICHE_KEYWORDS:
            continue
        if any(k in n for k in NICHE_KEYWORDS[niche]):
            return niche

    # Fallback: "merch" không match niche nào → likely music artist merch
    # (Naruto merch → đã detect anime trước, nên "merch" fallback = music)
    if "merch" in n:
        return "music"

    return "general"


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL LINK SELECTOR
# ══════════════════════════════════════════════════════════════════════════════

def pick_internal_link(
    product_name: str,
    link_config: dict,
    round_robin_index: int = 0,
) -> dict:
    """
    Chọn internal link phù hợp cho 1 sản phẩm.

    link_config format (từ Settings tab):
    {
        "mode": "category" | "product",

        # mode = category: dùng 1 URL danh mục cố định per niche
        "category_links": {
            "music":      "https://store.com/music/",
            "basketball": "https://store.com/basketball/",
            "trending":   "https://store.com/trending/",   # fallback
            ...
        },

        # mode = product: pool sản phẩm liên quan, round-robin
        "product_pool": [
            {"url": "https://store.com/product-a/", "title": "Product A"},
            {"url": "https://store.com/product-b/", "title": "Product B"},
            ...
        ],
    }

    Returns:
    {
        "url":   str,   # "" nếu không có link nào
        "title": str,   # title gợi ý cho AI chọn anchor (product title hoặc niche label)
        "mode":  str,   # "category" | "product" | "none"
    }
    """
    if not link_config:
        return {"url": "", "title": "", "mode": "none"}

    mode = link_config.get("mode", "category")

    # ── CATEGORY MODE ─────────────────────────────────────────────────────────
    if mode == "category":
        cat_links = link_config.get("category_links", [])
        if not cat_links:
            return {"url": "", "title": "", "mode": "none"}

        # Normalize: support cả list [{name,url}] lẫn dict {key:url} (backward compat)
        if isinstance(cat_links, dict):
            pool = [{"name": k, "url": v} for k, v in cat_links.items() if v]
        else:
            pool = [item for item in cat_links if item.get("url","").strip()]

        if not pool:
            return {"url": "", "title": "", "mode": "none"}

        # Match product name với category name — tìm category liên quan nhất
        name_lower = _n(product_name)
        best_url   = ""
        best_title = ""

        # Pass 1a: exact phrase match (category name nằm trong product name)
        for item in pool:
            cat_name = _n(item.get("name", ""))
            if cat_name and cat_name in name_lower:
                best_url   = item["url"].strip()
                best_title = item.get("name", "")
                break

        # Pass 1b: partial phrase match — bỏ suffix rác ("gifts","gift","store","tees")
        #   "Father's Day Gifts" → strip → "father's day" rồi tìm trong product name
        if not best_url:
            import re as _re
            SUFFIX_STRIP = _re.compile(
                r"\b(gifts?|tees?|shirts?|store|shop|collection|items?)\s*$",
                _re.IGNORECASE,
            )
            for item in pool:
                cat_name_stripped = SUFFIX_STRIP.sub(
                    "", _n(item.get("name", ""))
                ).strip()
                if cat_name_stripped and cat_name_stripped in name_lower:
                    best_url   = item["url"].strip()
                    best_title = item.get("name", "")
                    break

        # Pass 2: dùng detect_niche() + detect_occasion() để tìm niche phù hợp
        # rồi tìm category name có chứa niche keyword đó
        if not best_url:
            detected  = detect_niche(product_name)
            occasion  = detect_occasion(product_name)
            niche_aliases = {
                "basketball":       ["basketball", "nba", "wnba", "ncaa"],
                "football":         ["football", "nfl"],
                "college_football": ["football", "ncaa", "college"],
                "baseball":         ["baseball", "mlb"],
                "hockey":           ["hockey", "nhl"],
                "music":            ["music", "rock", "band", "artist", "merch"],
                "anime":            ["anime", "manga"],
                "movie":            ["movie", "film", "tv", "series"],
                "political":        ["political", "patriot"],
                "meme":             ["meme", "funny", "humor"],
                "nurse":            ["nurse", "medical", "healthcare"],
                "motivational":     ["motivational", "inspirational"],
                "vintage":          ["vintage", "retro"],
                "dog":              ["dog", "pet"],
                "cat":              ["cat", "pet"],
                "general":          ["trending", "general"],
                # Occasion niches — thêm để Pass 2 detect được
                "fathers_day":      ["father", "dad", "fathers day"],
                "mothers_day":      ["mother", "mom", "mothers day"],
                "valentines":       ["valentine", "valentines"],
                "halloween":        ["halloween"],
                "christmas":        ["christmas", "xmas", "holiday"],
                "thanksgiving":     ["thanksgiving"],
                "st_patricks":      ["patrick", "irish", "paddy"],
                "veterans":         ["veteran", "veterans day", "military"],
            }
            # Ưu tiên occasion nếu có (vd: "fathers_day" > "general")
            lookup_key = occasion if occasion else detected
            aliases = niche_aliases.get(lookup_key, [lookup_key])
            for item in pool:
                cat_name_lower = _n(item.get("name", ""))
                if any(alias in cat_name_lower for alias in aliases):
                    best_url   = item["url"].strip()
                    best_title = item.get("name", "")
                    break

        # Pass 3: tìm từ chung có nghĩa (bỏ qua stop words)
        STOP_WORDS = {"t", "shirt", "tee", "the", "a", "an", "and", "or",
                      "for", "of", "in", "on", "at", "to", "with", "2026",
                      "2025", "2024", "season", "edition", "limited", "special"}
        if not best_url:
            product_words = set(name_lower.split()) - STOP_WORDS
            for item in pool:
                cat_words = set(_n(item.get("name","")).split()) - STOP_WORDS
                overlap = product_words & cat_words
                if overlap:
                    best_url   = item["url"].strip()
                    best_title = item.get("name","")
                    break

        # Pass 4: fallback về item có tên "trending" hoặc "general" trong pool
        # Tuyệt đối KHÔNG lấy bừa item đầu tiên
        if not best_url:
            for item in pool:
                cat_name_lower = _n(item.get("name", ""))
                if any(k in cat_name_lower for k in ["trending", "general", "all"]):
                    best_url   = item["url"].strip()
                    best_title = item.get("name", "")
                    break

        if best_url:
            return {"url": best_url, "title": best_title, "mode": "category"}
        return {"url": "", "title": "", "mode": "none"}

    # ── PRODUCT MODE (round-robin) ────────────────────────────────────────────
    if mode == "product":
        pool = link_config.get("product_pool", [])
        if not pool:
            return {"url": "", "title": "", "mode": "none"}

        # Round-robin: index mod len(pool)
        item = pool[round_robin_index % len(pool)]
        return {
            "url":   item.get("url", ""),
            "title": item.get("title", ""),
            "mode":  "product",
        }

    return {"url": "", "title": "", "mode": "none"}


def _niche_label(key: str) -> str:
    labels = {
        "music": "music collection", "anime": "anime collection",
        "movie": "movie collection", "political": "political collection",
        "meme": "humor collection", "nurse": "medical collection",
        "motivational": "motivational collection", "vintage": "vintage collection",
        "dog": "dog lover collection", "cat": "cat lover collection",
        "sports": "sports collection", "football": "football collection",
        "college_football": "college football collection",
        "baseball": "baseball collection", "basketball": "basketball collection",
        "hockey": "hockey collection", "fathers_day": "Father's Day gifts",
        "mothers_day": "Mother's Day gifts", "valentines": "Valentine's Day gifts",
        "halloween": "Halloween collection", "christmas": "Christmas collection",
        "thanksgiving": "Thanksgiving gifts", "veterans": "Veterans Day gifts",
        "trending": "trending collection",
    }
    return labels.get(key, "collection")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

def resolve(
    product_name: str,
    link_config: dict | None = None,
    round_robin_index: int = 0,
) -> dict:
    """
    Public API — trả về toàn bộ context để inject vào SEO prompt.

    Returns:
    {
        "niche":          str,
        "occasion":       str | None,
        "sport":          str | None,
        "internal_url":   str,
        "internal_title": str,   # AI dùng để tự chọn anchor phù hợp
        "internal_mode":  str,   # "category" | "product" | "none"
        "external_url":   str,
        "hook_style":     str,
    }
    """
    occasion = detect_occasion(product_name)
    sport    = detect_sport(product_name)
    niche    = detect_niche(product_name)

    # Internal link
    link = pick_internal_link(product_name, link_config or {}, round_robin_index)

    # Hook style
    hook_niche = sport if sport else niche
    pool       = HOOK_STYLES.get(hook_niche, HOOK_STYLES["general"])
    hook_style = random.choice(pool)

    return {
        "niche":          niche,
        "occasion":       occasion,
        "sport":          sport,
        "internal_url":   link["url"],
        "internal_title": link["title"],
        "internal_mode":  link["mode"],
        "hook_style":     hook_style,
    }

"""
WooMMO All-in-One — SEO Generator (Public Edition)

Thay đổi so với v5:
  - store_name inject động vào quality section + CTA + meta snippet
  - AI tự chọn anchor text cho cả internal và external link
  - Internal link lấy từ link_config (category hoặc product pool, round-robin)
  - Shortcode configurable (default: [thien_display_single_image])
  - BulkSEOWorker quản lý round-robin index tự động
"""

import re, json, base64, requests
from link_resolver import resolve

# ══════════════════════════════════════════════════════════════════════════════
# POST-PROCESSING: Forbidden phrase patterns — auto-retry nếu phát hiện
# ══════════════════════════════════════════════════════════════════════════════
FORBIDDEN_PATTERNS = [
    # "not just" variants
    r"not just a shirt",
    r"not just a tee",
    r"not just a piece",
    r"not just clothing",
    r"not just apparel",
    r"not just fabric",
    r"not just another piece",
    r"not just about the",
    r"it's not just",
    r"it is not just",
    # "more than just" variants
    r"more than just a shirt",
    r"more than just a tee",
    r"more than just a piece",
    r"more than just clothing",
    r"more than just apparel",
    r"more than just fabric",
    r"more than just a",
    # other banned phrases
    r"badge of (honor|pride)",
    r"captures the essence",
    r"encapsulates the essence",
    r"a must-have",
    r"must have for",
    r"iconic tee",
    r"iconic shirt",
    r"perfect for those who",
    r"speaks directly to",
    r"resonates with (fans|your)",
    r"not your average tee",
    r"not your average shirt",
    # more variants
    r"resonates with the essence",
    r"essential addition to your wardrobe",
    r"you're not just investing",
    r"not just investing in",
    r"the rest of the .{0,30} gear",
    r"the rest of the gear",
    r"complete your (collection|wardrobe|look) with the rest",
    r"celebration of positivity",
    r"you can['']t help but",
    r"wear it with pride",
    r"let the world know",
    r"show the world",
    r"speaks volumes",
    r"the perfect way to show",
    r"a great way to show",
    r"express your (love|passion|fandom) for",
]

# ── Niche drift blacklist ─────────────────────────────────────────────────────
NICHE_BLACKLIST = {
    "music":   ["hospital", "nurse", "shift", "patient", "clinic", "break room",
                 "night shift", "long shift", "stress of the shift", "coworker"],
    "sports":  ["hospital", "nurse", "shift", "patient", "office", "meeting"],
    "anime":   ["hospital", "shift", "office", "corporate", "coworker"],
    "movie":   ["hospital", "shift", "office", "coworker"],
    "meme":    ["hospital", "shift", "coworker"],
    "vintage": ["hospital", "shift", "coworker"],
    "general": ["hospital", "nurse", "shift", "patient"],
}

# ── Generic writing patterns ───────────────────────────────────────────────────
GENERIC_PATTERNS = [
    r"you can['']t help but",
    r"this shirt is for those who",
    r"whether you['']?re a fan",
    r"perfect for (those|anyone|fans)",
    r"celebration of positivity",
    r"invest in (a|this) t-shirt",
    r"fans of all ages",
    r"from casual to hardcore",
    r"no matter your style",
    r"whether you['']?re a (lifelong|diehard|die-hard)",
]

# ── Bad anchor patterns ────────────────────────────────────────────────────────
BAD_ANCHOR_PATTERNS = [
    "the rest of the",
    "check out more",
    "explore more",
    "click here",
    "learn more",
    "shop now",
    "find more",
    "see more",
    "browse",
    "explore this",
    "similar items",
    "other designs",
    "more designs",
    "complete your",
    "check out our",
]

def check_hook_niche(html: str, niche: str) -> list[str]:
    """Detect niche drift — wrong context words anywhere in html."""
    blacklist = NICHE_BLACKLIST.get(niche, [])
    if not blacklist:
        return []
    found = []
    html_lower = html.lower()
    for word in blacklist:
        if re.search(rf"\b{re.escape(word)}\b", html_lower):
            found.append(f"niche_drift:{word}")
    return found

def check_structure(html: str, shortcode: str = "", product_name: str = "") -> list[str]:
    """Validate HTML structure — hook, FAQ format, shortcode, links, H2 suffix."""
    errors = []

    # Opening hook check — first element MUST be <p>, not <h2>
    html_stripped = html.strip()
    if html_stripped.startswith("<h2>"):
        errors.append("missing_opening_hook: output starts with <h2>, need <p> hook first")
    elif not html_stripped.startswith("<p>"):
        errors.append("missing_opening_hook: first element must be <p> opening hook")

    # FAQ format check
    if "<strong>Q1:" in html and "<p><strong>Q1:" not in html:
        errors.append("faq_format: use <p><strong>Q:</strong><br>A:</p>")
    # Shortcode after first H2
    if shortcode and shortcode in html:
        first_h2 = html.find("<h2>")
        sc_pos = html.find(shortcode)
        if first_h2 > 0 and sc_pos < first_h2:
            errors.append("shortcode_before_h2")
    # H2 suffix check — first H2 must not be product name alone or weak
    GENERIC_H2_SUFFIXES = [
        # Generic quality/CTA
        "quality you can trust", "premium quality", "must have",
        "best choice", "buy now", "shop now", "get yours",
        "t-shirt tee", "tee shirt", "t shirt tee",
        # Generic clickbait/filler suffixes AI hay dùng
        "that speaks volumes", "speaks volumes",
        "wear your", "for true patriots", "for true fans",
        "for every fan", "for every proud", "for the proud",
        "you need to have", "you need now",
        "stands out from", "stand out from",
        "for the passionate supporter",
        "for like-minded", "for the unapologetic",
        "a must have", "a must-have",
        "unleash your inner",
        "show your pride today", "show your support today",
        "wear your beliefs with pride", "wear your passion with",
        "make a statement with this",
    ]

    # Standalone generic H2 patterns (không cần bắt đầu bằng product name)
    STANDALONE_GENERIC_H2 = [
        r"^quality you can (trust|count on)",
        r"^unmatched quality",
        r"^exceptional quality",
        r"^high.quality fabric",
        r"^get yours (before|now|today)",
        r"^don.t miss out",
        r"^grab yours",
        r"^order (now|today)",
        r"^shop now",
    ]

    if product_name:
        first_h2_match = re.search(r"<h2>(.*?)</h2>", html, re.IGNORECASE)
        if first_h2_match:
            h2_text = re.sub(r"<[^>]+>", "", first_h2_match.group(1)).strip()
            pname_clean = product_name.strip()
            h2_lower = h2_text.lower()
            pname_lower = pname_clean.lower()

            # Case 0: H2 hoàn toàn generic (không liên quan product name)
            for pattern in STANDALONE_GENERIC_H2:
                if re.search(pattern, h2_lower):
                    errors.append(
                        f"h2_generic_suffix: '{h2_text}' — H2 is generic section header, "
                        f"must be product name + niche-specific suffix"
                    )
                    break

            # Case 1: H2 = tên SP trơn (exact match)
            if h2_lower == pname_lower:
                errors.append(
                    f"h2_no_suffix: '{h2_text}' — must add 2-5 creative niche words"
                )
            # Case 2: H2 bắt đầu bằng tên SP
            elif h2_lower.startswith(pname_lower):
                suffix = h2_text[len(pname_clean):].strip(" -—:")
                suffix_words = [w for w in suffix.split() if len(w) > 1]
                if len(suffix_words) < 2:
                    errors.append(
                        f"h2_weak_suffix: '{h2_text}' — suffix too short, need 2+ meaningful words"
                    )
                else:
                    # Case 3: suffix generic
                    for g in GENERIC_H2_SUFFIXES:
                        if g in suffix.lower():
                            errors.append(
                                f"h2_generic_suffix: '{suffix}' is generic — "
                                f"use niche-specific fan-voice suffix instead"
                            )
                            break
    # Link validation — cần cả external và internal
    links = re.findall(r'<a href="([^"]+)"', html)
    if len(links) < 2:
        errors.append(f"missing_links: found {len(links)}, need 2 (external + internal)")
    else:
        external_domains = ["wikipedia", "espn", "rollingstone", "billboard",
                            "imdb", "rottentomatoes", "myanimelist", "knowyourmeme",
                            "britannica", "nfl.com", "nba.com", "mlb.com"]
        has_external = any(any(d in l for d in external_domains) for l in links)
        if not has_external:
            errors.append("missing_external_link: no authority link found")
    return errors

def check_anchor_quality(html: str) -> list[str]:
    """Detect generic/bad anchor text."""
    errors = []
    html_lower = html.lower()
    for bad in BAD_ANCHOR_PATTERNS:
        if bad in html_lower:
            errors.append(f"bad_anchor: '{bad}'")
    # Check anchor length — < 3 words thường là generic
    anchors = re.findall(r"<a [^>]*>(.*?)</a>", html, re.IGNORECASE)
    for anchor_text in anchors:
        clean = re.sub(r"<[^>]+>", "", anchor_text).strip()
        if clean and len(clean.split()) <= 2:
            errors.append(f"weak_anchor_too_short: '{clean}'")
    return errors

def check_generic_writing(html: str) -> list[str]:
    """Detect generic marketing writing."""
    found = []
    html_lower = html.lower()
    for pattern in GENERIC_PATTERNS:
        if re.search(pattern, html_lower):
            found.append(f"generic_writing: '{pattern}'")
    return found

# ══════════════════════════════════════════════════════════════════════════════
# ── Word count helper ────────────────────────────────────────────────────────

def count_words_html(html: str) -> int:
    """Đếm số từ visible trong HTML — strip tags trước khi đếm."""
    text = re.sub(r"<[^>]+>", " ", html)          # bỏ tất cả tags
    text = re.sub(r"&[a-z]+;", " ", text)          # bỏ HTML entities
    text = re.sub(r"\s+", " ", text).strip()
    return len(text.split()) if text else 0


# AI NICHE DETECTION — thay thế keyword-based detection
# ══════════════════════════════════════════════════════════════════════════════
NICHE_DETECT_SYSTEM = """You are a product niche classifier for a Print-on-Demand store.
Given a product name, return ONLY one word from this list:
music, anime, movie, sports, political, meme, nurse, teacher, fishing, hunting,
camping, farming, trucker, firefighter, military, gym, gaming, beer, coffee,
family, christmas, halloween, birthday, horse, bird, motivational, vintage, dog, cat,
profession, holiday, general

Rules:
- music: music artists, bands, albums, concerts, singer/songwriter merch
- anime: anime series, manga, otaku, cosplay culture
- movie: movies, TV shows, film/series characters, Netflix, Disney
- sports: NBA, NFL, MLB, NHL, NCAA, soccer, MMA, any team/player/sport
- political: political figures, patriotic, USA pride, flag, freedom, independence, anniversary
- meme: internet memes, viral trends, humor, sarcasm, cartoon characters
- nurse: nurses, doctors, healthcare, hospital, medical profession
- teacher: teachers, educators, school, classroom, back to school, principal
- fishing: fishing, angler, bass, trout, fisherman, fish, tackle
- hunting: hunting, deer, duck, turkey, hunter, camo, outdoorsman
- camping: camping, campfire, hiking, trail, wilderness, outdoor adventure
- farming: farm, farmer, tractor, ranch, cowboy, country life, agriculture
- trucker: truck driver, semi, 18-wheeler, road, CDL, hauling
- firefighter: firefighter, fireman, fire dept, first responder, rescue
- military: army, navy, marines, air force, veteran, soldier, deployment
- gym: gym, workout, lifting, bodybuilding, fitness, gains, protein, beast
- gaming: video games, gamer, Xbox, PlayStation, console, PC, controller
- beer: beer, brewery, craft beer, IPA, drinking, pub, ale, cheers
- coffee: coffee, espresso, caffeine, cafe, barista, morning brew
- family: grandma, grandpa, mom, dad, nana, papa, son, daughter, sister, brother
- christmas: christmas, santa, xmas, holiday season, reindeer, elf, jolly
- halloween: halloween, spooky, ghost, witch, scary, pumpkin, trick or treat
- birthday: birthday, years old, born in, age, turning, celebration
- horse: horse, equestrian, cowgirl, riding, mare, stallion, rodeo
- bird: bird watching, birding, parrot, eagle, owl, cardinal, birder
- motivational: hustle, grind, success, mindset, inspirational, boss, achieve
- vintage: retro, throwback, 70s/80s/90s, classic, old school, nostalgia
- dog: dog breeds, dog mom/dad, puppy, canine, rescue dog, pawrent
- cat: cat breeds, cat mom/dad, kitten, feline, crazy cat, whiskers
- profession: any other job/career not listed (lawyer, mechanic, chef, pilot, chef, realtor, plumber...)
- holiday: any other holiday (mothers day, fathers day, memorial day, thanksgiving, 4th july...)
- general: anything that does not fit any category above

Priority (when multiple match, pick most specific):
- sports + meme → sports
- music + vintage → music
- dog + birthday → dog
- military + political → military
- camping + hunting → hunting

Return ONLY the single niche word. No explanation."""


# ══════════════════════════════════════════════════════════════════════════════
# NICHE PROFILE — angle + emotion + voice injection per niche
# ══════════════════════════════════════════════════════════════════════════════
# Mỗi niche có:
#   angle:        góc nhìn chính của mô tả
#   emotion:      cảm xúc cốt lõi cần trigger
#   pov:          người viết là ai (inject vào prompt)
#   context_refs: từ khoá ngữ cảnh đặc thù để AI dùng trong bài
#   h2_angles:    các hướng H2 (không phải template cứng, là gợi ý tư duy)
#   voice_rule:   rule giọng văn bổ sung cho niche này

NICHE_PROFILE = {
    "music": {
        "angle": "fan identity and cultural moment",
        "emotion": "pride, anticipation, belonging",
        "pov": "a devoted fan who knows every lyric, every era, and is hyped for what's coming next",
        "context_refs": ["tour era", "album cycle", "setlist", "fan culture", "concert energy"],
        "h2_angles": ["era-specific reference", "fan recognition moment", "concert/tour energy", "cultural legacy"],
        "voice_rule": "Ground in specific songs, albums, eras, or fan culture. Write in anticipation — hype for what's ahead, not nostalgia for events that may not have happened yet. NEVER write as if the reader already attended a show.",
    },
    "anime": {
        "angle": "fandom insider knowledge",
        "emotion": "passion, identity, exclusive belonging",
        "pov": "a fan who watched before it got mainstream, knows the lore",
        "context_refs": ["arc", "fandom", "character trait", "studio", "season", "manga"],
        "h2_angles": ["lore-specific angle", "character identity", "fandom culture", "series milestone"],
        "voice_rule": "Use fandom language. Reference specific characters, arcs, or cultural moments.",
    },
    "movie": {
        "angle": "character or cinematic cultural moment",
        "emotion": "nostalgia, fandom pride, humor",
        "pov": "someone who never skips the credits and has rewatched it 10 times",
        "context_refs": ["scene", "quote", "franchise", "cast", "director", "genre"],
        "h2_angles": ["iconic scene/quote angle", "fan dedication angle", "character identity", "franchise legacy"],
        "voice_rule": "Reference specific scenes, quotes, or character moments. Avoid generic 'movie lover'.",
    },
    "sports": {
        "angle": "fan identity and game day culture",
        "emotion": "pride, loyalty, competitive energy",
        "pov": "a fan who has been there since before the championship",
        "context_refs": ["game day", "season", "rivalry", "playoff", "team culture", "jersey"],
        "h2_angles": ["game day energy", "fan loyalty milestone", "rivalry context", "team pride moment"],
        "voice_rule": "Reference specific team culture, rivalry, or season moments. Never generic sports fan.",
    },
    "political": {
        "angle": "historical significance and American identity",
        "emotion": "pride, patriotism, heritage",
        "pov": "a proud American who understands the weight of this moment in history",
        "context_refs": ["independence", "freedom", "history", "founding", "milestone", "legacy", "anniversary"],
        "h2_angles": ["historical milestone angle", "freedom/legacy theme", "patriotic identity", "anniversary significance"],
        "voice_rule": "Ground in history or political identity. Reference specific events, figures, or American milestones.",
    },
    "meme": {
        "angle": "shared humor and insider culture",
        "emotion": "humor, rebellion, relatability",
        "pov": "someone who got the joke before it went viral",
        "context_refs": ["viral moment", "internet culture", "reaction", "inside joke", "trend"],
        "h2_angles": ["humor angle", "insider knowledge", "viral culture moment", "self-aware wit"],
        "voice_rule": "Lean into the joke. Write with wit and self-awareness. Never explain the meme.",
    },
    "nurse": {
        "angle": "profession pride and insider grind",
        "emotion": "pride, solidarity, dark humor",
        "pov": "a colleague who has worked the overnight shift and totally gets it",
        "context_refs": ["shift", "patient", "scrubs", "hospital", "break room", "night shift", "badge"],
        "h2_angles": ["shift life reality", "profession solidarity", "healthcare insider moment", "bedside identity"],
        "voice_rule": "Use healthcare insider language. Reference real shift culture, not generic 'hard work'.",
    },
    "teacher": {
        "angle": "profession identity and classroom culture",
        "emotion": "pride, humor, solidarity",
        "pov": "a teacher who has been doing this for years and still shows up every day",
        "context_refs": ["classroom", "lesson plan", "students", "back to school", "grade", "whiteboard"],
        "h2_angles": ["classroom culture angle", "teacher solidarity", "school year identity", "educator pride"],
        "voice_rule": "Reference classroom realities, teacher humor, or school culture. Not generic 'education is important'.",
    },
    "fishing": {
        "angle": "angler lifestyle and the culture of the catch",
        "emotion": "passion, patience, identity",
        "pov": "someone who was out on the water at 5am and wouldn't trade it for anything",
        "context_refs": ["cast", "reel", "catch", "lake", "river", "bass", "tackle", "early morning"],
        "h2_angles": ["early morning on the water", "species-specific angle", "angler identity", "fishing culture"],
        "voice_rule": "Reference specific fishing culture — early mornings, the wait, the catch. Not generic outdoor fun.",
    },
    "hunting": {
        "angle": "hunter lifestyle and tradition",
        "emotion": "pride, patience, tradition",
        "pov": "a hunter who has been doing this since childhood, knows the land",
        "context_refs": ["season", "blind", "harvest", "trophy", "camo", "dawn", "field dressing"],
        "h2_angles": ["hunting tradition angle", "season-specific moment", "hunter identity", "land connection"],
        "voice_rule": "Ground in hunting culture and tradition. Reference specific species or seasonal moments.",
    },
    "camping": {
        "angle": "outdoor lifestyle and escape culture",
        "emotion": "freedom, adventure, simplicity",
        "pov": "someone who unplugs on weekends and is happiest around a campfire",
        "context_refs": ["campfire", "trail", "tent", "s'mores", "stargazing", "off-grid", "national park"],
        "h2_angles": ["campfire culture angle", "trail life identity", "escape from everyday theme", "nature connection"],
        "voice_rule": "Reference specific outdoor moments — campfire, trail, stargazing. Not generic 'nature lover'.",
    },
    "farming": {
        "angle": "farm life identity and rural pride",
        "emotion": "pride, grit, roots",
        "pov": "someone who was raised on a farm and carries that identity everywhere",
        "context_refs": ["sunrise", "harvest", "tractor", "livestock", "soil", "barn", "country road"],
        "h2_angles": ["farm life reality", "rural identity", "harvest season moment", "hard work pride"],
        "voice_rule": "Root in specific farm life realities — early mornings, seasons, the land. Not generic country.",
    },
    "trucker": {
        "angle": "road life and trucker culture",
        "emotion": "pride, independence, grit",
        "pov": "a driver who has logged a million miles and knows every rest stop on the route",
        "context_refs": ["miles", "load", "highway", "CB radio", "rest stop", "deadhead", "logbook"],
        "h2_angles": ["road life identity", "miles-logged pride", "trucker culture moment", "highway independence"],
        "voice_rule": "Use trucker culture language. Reference the road, the load, the lifestyle.",
    },
    "firefighter": {
        "angle": "first responder identity and brotherhood",
        "emotion": "pride, sacrifice, brotherhood",
        "pov": "someone who runs toward the fire and calls it Tuesday",
        "context_refs": ["station", "alarm", "ladder", "hose", "turnout gear", "crew", "call"],
        "h2_angles": ["first responder pride", "brotherhood identity", "on-call culture", "sacrifice angle"],
        "voice_rule": "Reference firefighter culture — the station, the crew, the call. Not generic 'hero'.",
    },
    "military": {
        "angle": "service identity and military pride",
        "emotion": "pride, sacrifice, brotherhood/sisterhood",
        "pov": "a veteran who served and carries that identity for life",
        "context_refs": ["deployment", "unit", "branch", "rank", "service", "sacrifice", "honor"],
        "h2_angles": ["branch-specific pride", "veteran identity", "service culture moment", "sacrifice and honor"],
        "voice_rule": "Reference specific branch culture, deployment, or veteran identity. Never generic 'support the troops'.",
    },
    "gym": {
        "angle": "fitness culture and grind identity",
        "emotion": "motivation, pride, identity",
        "pov": "someone who is at the gym before most people are awake",
        "context_refs": ["PR", "gains", "rep", "squat rack", "pre-workout", "leg day", "bulk", "cut"],
        "h2_angles": ["gym culture identity", "fitness milestone", "grind culture moment", "lift community"],
        "voice_rule": "Use gym culture language — PR, gains, leg day. Not generic 'stay fit'.",
    },
    "gaming": {
        "angle": "gamer identity and gaming culture",
        "emotion": "passion, humor, community",
        "pov": "someone who has put 500+ hours into a game and knows every Easter egg",
        "context_refs": ["respawn", "grind", "boss fight", "loot", "server", "streamer", "platform"],
        "h2_angles": ["game-specific culture", "gamer identity", "gaming community moment", "skill/dedication angle"],
        "voice_rule": "Use gaming language naturally. Reference specific culture — grinding, boss fights, community.",
    },
    "beer": {
        "angle": "beer culture and social identity",
        "emotion": "humor, relaxation, community",
        "pov": "a craft beer enthusiast who can tell an IPA from a stout by smell",
        "context_refs": ["brew", "hops", "pint", "tap", "brewery", "session", "cold one", "cheers"],
        "h2_angles": ["brew culture angle", "social drinking identity", "craft beer moment", "relaxation culture"],
        "voice_rule": "Reference beer culture — brewing, styles, social moments. Not generic 'love to drink'.",
    },
    "coffee": {
        "angle": "coffee culture and morning ritual",
        "emotion": "identity, humor, ritual",
        "pov": "someone for whom coffee is not optional — it's a personality trait",
        "context_refs": ["brew", "espresso", "morning ritual", "caffeine", "roast", "pour over", "cold brew"],
        "h2_angles": ["morning ritual identity", "coffee culture moment", "caffeine dependency humor", "brew obsession"],
        "voice_rule": "Reference specific coffee culture — morning ritual, brew methods, caffeine identity.",
    },
    "family": {
        "angle": "family role and relationship pride",
        "emotion": "love, pride, warmth",
        "pov": "someone who wears their family role as a badge of honor",
        "context_refs": ["relationship", "milestone", "family gathering", "legacy", "generation"],
        "h2_angles": ["family role pride", "generational connection", "relationship milestone", "love expression"],
        "voice_rule": "Warm, specific, personal. Reference the specific family role — grandpa, mom, daughter, etc.",
    },
    "christmas": {
        "angle": "holiday spirit and Christmas culture",
        "emotion": "joy, nostalgia, warmth",
        "pov": "someone who starts decorating November 1st and has opinions about eggnog",
        "context_refs": ["tree", "gifts", "Santa", "caroling", "fireplace", "winter", "holiday tradition"],
        "h2_angles": ["holiday tradition angle", "Christmas culture moment", "seasonal identity", "gift-giving spirit"],
        "voice_rule": "Reference specific Christmas culture and traditions. Not generic 'happy holidays'.",
    },
    "halloween": {
        "angle": "spooky culture and Halloween identity",
        "emotion": "excitement, humor, community",
        "pov": "someone who has their costume planned months in advance",
        "context_refs": ["costume", "trick or treat", "haunted", "candy", "carving", "October", "spooky season"],
        "h2_angles": ["spooky culture angle", "Halloween tradition", "costume identity", "spooky season moment"],
        "voice_rule": "Lean into spooky culture. Reference Halloween traditions and the identity around loving it.",
    },
    "birthday": {
        "angle": "age milestone and celebration culture",
        "emotion": "joy, humor, milestone pride",
        "pov": "someone celebrating a specific age with personality",
        "context_refs": ["milestone", "age", "celebration", "another year", "cake", "friends", "party"],
        "h2_angles": ["age milestone angle", "birthday culture humor", "celebration identity", "year-marking moment"],
        "voice_rule": "Reference the specific age if present. Keep it celebratory and personality-driven.",
    },
    "dog": {
        "angle": "dog owner identity and breed culture",
        "emotion": "love, humor, belonging",
        "pov": "a dog owner who talks to their dog like a person and has no regrets",
        "context_refs": ["breed", "paw", "fetch", "walk", "zoomies", "good boy", "rescue", "fur baby"],
        "h2_angles": ["breed personality angle", "dog owner identity", "rescue culture", "dog-human bond"],
        "voice_rule": "Reference breed-specific behavior or dog owner culture. Not generic 'love dogs'.",
    },
    "cat": {
        "angle": "cat owner identity and feline culture",
        "emotion": "humor, love, belonging",
        "pov": "a cat owner who understands that the cat is in charge",
        "context_refs": ["purr", "knead", "midnight zoomies", "laser", "nap", "attitude", "independent"],
        "h2_angles": ["cat behavior angle", "cat owner identity", "feline humor", "cat-human dynamic"],
        "voice_rule": "Reference specific cat behaviors and the humor of cat ownership. Not generic 'cat lover'.",
    },
    "horse": {
        "angle": "equestrian identity and horse culture",
        "emotion": "passion, pride, connection",
        "pov": "someone who grew up riding and considers the stable a second home",
        "context_refs": ["barn", "saddle", "ride", "breed", "arena", "trail ride", "mucking out", "tack"],
        "h2_angles": ["equestrian culture angle", "horse-human bond", "barn life identity", "riding milestone"],
        "voice_rule": "Reference specific equestrian culture — barn life, riding, specific disciplines.",
    },
    "bird": {
        "angle": "birder identity and ornithology culture",
        "emotion": "passion, peace, community",
        "pov": "someone who wakes up at dawn with binoculars and a life list",
        "context_refs": ["life list", "binoculars", "species", "migration", "backyard feeder", "dawn chorus"],
        "h2_angles": ["birding culture angle", "species-specific moment", "birder identity", "nature connection"],
        "voice_rule": "Reference birding culture — life list, specific species, dawn watching. Not generic 'birds are pretty'.",
    },
    "motivational": {
        "angle": "mindset and personal growth identity",
        "emotion": "drive, empowerment, ambition",
        "pov": "a coach who means every word and has lived the grind",
        "context_refs": ["mindset", "discipline", "goal", "hustle", "growth", "setback", "consistency"],
        "h2_angles": ["mindset culture angle", "grind identity", "growth moment", "discipline pride"],
        "voice_rule": "Specific and direct. Reference the actual mindset or situation. Not generic inspirational filler.",
    },
    "vintage": {
        "angle": "nostalgia and era-specific identity",
        "emotion": "nostalgia, pride, authenticity",
        "pov": "someone who prefers the original to the remaster and knows exactly why",
        "context_refs": ["era", "decade", "throwback", "classic", "original", "analog", "old school"],
        "h2_angles": ["era-specific reference", "nostalgia identity", "authenticity angle", "classic culture moment"],
        "voice_rule": "Ground in a specific era or cultural moment. Reference why the original was better.",
    },
    "profession": {
        "angle": "career identity and professional pride",
        "emotion": "pride, solidarity, insider humor",
        "pov": "a colleague who truly understands the daily grind of this profession",
        "context_refs": ["daily grind", "profession-specific tool", "workplace", "client", "certification", "years of experience"],
        "h2_angles": ["profession pride angle", "insider culture moment", "career milestone", "daily reality"],
        "voice_rule": "Reference the specific job's culture and inside language. Not generic 'hard work'.",
    },
    "holiday": {
        "angle": "holiday culture and seasonal identity",
        "emotion": "joy, pride, tradition",
        "pov": "someone who takes this holiday seriously and celebrates with full commitment",
        "context_refs": ["tradition", "celebration", "season", "gathering", "symbol", "date"],
        "h2_angles": ["tradition angle", "holiday culture identity", "seasonal moment", "celebration pride"],
        "voice_rule": "Reference specific holiday culture and traditions. Ground in what makes this holiday meaningful.",
    },
    "general": {
        "angle": "specific identity and insider perspective",
        "emotion": "pride, humor, belonging",
        "pov": "an insider who immediately recognizes what this is about",
        "context_refs": ["specific interest", "community", "identity", "passion"],
        "h2_angles": ["identity angle", "community moment", "passion expression", "insider recognition"],
        "voice_rule": "Find the specific identity behind the design. Write from an insider perspective, not a seller.",
    },
}


def get_niche_profile(niche: str) -> dict:
    """Trả về profile của niche, fallback về general nếu không tìm thấy."""
    return NICHE_PROFILE.get(niche, NICHE_PROFILE["general"])


def check_forbidden(html: str) -> list[str]:
    """Trả về list các forbidden phrases tìm thấy trong html."""
    found = []
    html_lower = html.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, html_lower):
            found.append(pattern)
    return found


# ── Licensing claim check — luôn bật, không tắt như FORBIDDEN_PATTERNS ────────
# Store bán hàng fan-inspired KHÔNG có bản quyền/license thật — không được để
# AI tự ý claim "official"/"licensed" trong mô tả (rủi ro chính sách quảng cáo
# + hiểu lầm về bản quyền, không liên quan token/SEO nên luôn check).
LICENSING_CLAIM_PATTERNS = [
    r"\bofficial(ly)?\b",
    r"\blicens(e|ed|ing)\b",
]


def check_licensing_claims(html: str) -> list[str]:
    """Trả về list các claim 'official/licensed' tìm thấy trong html (luôn check)."""
    found = []
    html_lower = html.lower()
    for pattern in LICENSING_CLAIM_PATTERNS:
        m = re.search(pattern, html_lower)
        if m:
            found.append(f"licensing_claim:{m.group(0)}")
    return found


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT TYPE DETECTION & CONTEXT
# ══════════════════════════════════════════════════════════════════════════════

# Mỗi entry: {
#   "keywords":  list từ khoá detect trong product name (lowercase),
#   "label":     tên hiển thị để log,
#   "item_word": từ dùng thay "shirt" trong prompt ("mug", "poster"...),
#   "material":  mô tả chất liệu cho Quality section,
#   "use_case":  ngữ cảnh sử dụng cho Audience section,
#   "styling":   gợi ý styling/pairing cho Audience section,
#   "size_note": note về size (thay thế "S to XXL"),
#   "care":      hướng dẫn bảo quản cho FAQ,
#   "faq_hints": list gợi ý câu hỏi FAQ đặc thù,
#   "quality_h2_hint": gợi ý H2 cho Quality section,
# }
PRODUCT_CONTEXT = {
    # ── Apparel ───────────────────────────────────────────────────────────────
    "t-shirt": {
        "keywords":    ["t-shirt", "tshirt", "unisex tee", " tee shirt", " t shirt"],
        "label":       "T-Shirt",
        "item_word":   "shirt",
        "material":    "100% premium cotton, soft and breathable, lightweight for all-day wear. Advanced DTG printing delivers sharp, vibrant colors that stay bold wash after wash.",
        "use_case":    "Everyday wear, casual outings, concerts, rallies, gifting",
        "styling":     "Pair with jeans, shorts, or layer under a jacket. Works dressed up or down.",
        "size_note":   "Available in a range of sizes — check the size chart before ordering.",
        "care":        "Machine wash cold, tumble dry low. Avoid bleach to preserve print quality.",
        "faq_hints":   ["print durability", "sizing", "fabric feel", "care instructions", "gifting"],
        "quality_h2_hint": "quality fabric, premium cotton, print durability",
    },
    "hoodie": {
        "keywords":    ["hoodie", "pullover hoodie", "zip hoodie", "hooded sweatshirt"],
        "label":       "Hoodie",
        "item_word":   "hoodie",
        "material":    "Premium cotton-polyester blend with a soft fleece interior. Double-lined hood, front kangaroo pocket, and ribbed cuffs. Advanced print technology keeps colors vivid through every wash.",
        "use_case":    "Cool weather, layering, casual hangouts, outdoor events, gifting",
        "styling":     "Wear over a tee for casual warmth, or layer under a jacket. Pairs with joggers, jeans, or shorts.",
        "size_note":   "Available in a range of sizes — check the size chart before ordering.",
        "care":        "Machine wash cold inside out, tumble dry low. Do not bleach.",
        "faq_hints":   ["warmth and comfort", "print quality on fleece", "sizing", "care", "gifting"],
        "quality_h2_hint": "premium fleece, durable print, lasting comfort",
    },
    "sweatshirt": {
        "keywords":    ["sweatshirt", "crewneck", "crew neck"],
        "label":       "Sweatshirt",
        "item_word":   "sweatshirt",
        "material":    "Midweight cotton-polyester blend, ribbed crew neck collar and cuffs. Soft interior fleece for warmth without bulk. Print is crisp and fade-resistant.",
        "use_case":    "Casual everyday wear, cooler weather, lounging, gifting",
        "styling":     "Pair with jeans, chinos, or joggers. Great for layering over a tee.",
        "size_note":   "Available in a range of sizes — check the size chart before ordering.",
        "care":        "Machine wash cold, tumble dry low. Turn inside out to protect print.",
        "faq_hints":   ["fabric weight", "print durability", "sizing", "care", "gifting"],
        "quality_h2_hint": "midweight fleece, vibrant print, all-season comfort",
    },
    "sweater": {
        "keywords":    ["sweater", "knit sweater", "knitted"],
        "label":       "Sweater",
        "item_word":   "sweater",
        "material":    "Soft knit construction with a classic silhouette. Comfortable, warm, and stylish — built for colder seasons with a timeless aesthetic.",
        "use_case":    "Fall and winter wear, layering, casual and semi-formal occasions",
        "styling":     "Pair with chinos or jeans. Layer under a coat for extra warmth.",
        "size_note":   "Available in a range of sizes — check the size chart.",
        "care":        "Hand wash or machine wash gentle cycle in cold water. Lay flat to dry.",
        "faq_hints":   ["warmth", "knit quality", "sizing", "care", "seasonal versatility"],
        "quality_h2_hint": "soft knit, warm construction, timeless style",
    },
    "long sleeve": {
        "keywords":    ["long sleeve", "long-sleeve", "longsleeve", "long sleve"],
        "label":       "Long Sleeve",
        "item_word":   "long sleeve shirt",
        "material":    "100% premium cotton long sleeve tee, lightweight and breathable. Full-length sleeves for added coverage, with the same vibrant DTG print as our standard tees.",
        "use_case":    "Year-round wear, layering base, casual outings, cooler days",
        "styling":     "Wear solo or layer under a jacket or flannel. Pairs with jeans, chinos, or joggers.",
        "size_note":   "Available in a range of sizes — check the size chart.",
        "care":        "Machine wash cold, tumble dry low. Avoid bleach.",
        "faq_hints":   ["fabric and sleeve length", "print quality", "sizing", "care", "versatility"],
        "quality_h2_hint": "premium cotton, full-sleeve coverage, lasting print",
    },
    "tank top": {
        "keywords":    ["tank top", "tank", "racerback", "sleeveless"],
        "label":       "Tank Top",
        "item_word":   "tank top",
        "material":    "Lightweight 100% cotton or cotton-poly blend. Sleeveless cut designed for breathability and freedom of movement. Vibrant print stays crisp wash after wash.",
        "use_case":    "Summer, gym, beach, outdoor events, casual warm-weather wear",
        "styling":     "Pair with shorts, joggers, or layer under an open shirt. Perfect for active days.",
        "size_note":   "Available in a range of sizes — check the size chart.",
        "care":        "Machine wash cold, tumble dry low or hang dry.",
        "faq_hints":   ["fabric breathability", "print", "sizing", "care", "activity use"],
        "quality_h2_hint": "breathable fabric, vibrant print, active-ready fit",
    },

    # ── Footwear ──────────────────────────────────────────────────────────────
    "crocs": {
        "keywords":    ["crocs", "clog", "clogs", "croc"],
        "label":       "Crocs / Clogs",
        "item_word":   "clogs",
        "material":    "Lightweight Croslite EVA foam construction — soft, buoyant, and odor-resistant. Custom all-over print wraps the entire surface with vibrant, waterproof graphics that won't fade or peel.",
        "use_case":    "Casual everyday wear, beach, poolside, garden, indoor comfort",
        "styling":     "Rock them solo for a bold statement or with fun socks for a playful look. Perfect for low-key outings where comfort meets personality.",
        "size_note":   "Available in whole sizes. If between sizes, size up for a relaxed fit or size down for a snug fit. Check the size chart.",
        "care":        "Rinse with water and mild soap. Air dry — avoid prolonged exposure to direct sunlight to preserve print vibrancy.",
        "faq_hints":   ["print durability on foam", "sizing", "waterproof qualities", "comfort", "cleaning"],
        "quality_h2_hint": "EVA foam comfort, waterproof all-over print, all-day wearability",
    },
    "shoes": {
        "keywords":    ["shoes", "sneakers", "canvas shoes", "slip-on", "footwear", "boots"],
        "label":       "Shoes / Sneakers",
        "item_word":   "shoes",
        "material":    "Durable canvas or breathable mesh upper with a custom all-over printed design. Non-slip rubber sole for everyday traction. Lightweight construction keeps your feet comfortable all day.",
        "use_case":    "Casual daily wear, events, gifting, self-expression through fashion",
        "styling":     "Pair with jeans, chinos, or shorts for a relaxed streetwear look. Let the design do the talking.",
        "size_note":   "Available in a range of sizes. Measure your foot length and compare to the size chart for the best fit.",
        "care":        "Spot clean with a damp cloth and mild soap. Air dry only — do not machine wash or tumble dry.",
        "faq_hints":   ["print durability", "sizing and fit", "sole grip", "care", "comfort for daily wear"],
        "quality_h2_hint": "durable canvas, all-over print, comfortable rubber sole",
    },

    # ── Home & Living ─────────────────────────────────────────────────────────
    "mug": {
        "keywords":    ["mug", "coffee mug", "ceramic mug", "11oz", "15oz"],
        "label":       "Mug",
        "item_word":   "mug",
        "material":    "High-fired ceramic construction available in 11oz and 15oz. Scratch-resistant gloss coating locks in the vibrant, full-wrap print. Thick walls retain heat longer for a better sipping experience.",
        "use_case":    "Morning coffee ritual, gifting, desk companion, fan display piece",
        "styling":     "Display it on your desk, gift it to a fellow fan, or use it as your daily statement piece. Pairs with any beverage — coffee, tea, hot cocoa.",
        "size_note":   "Available in 11oz and 15oz. The 15oz is ideal for those who like a bigger cup.",
        "care":        "Dishwasher safe on the top rack. Microwave safe. Hand washing recommended to extend print life.",
        "faq_hints":   ["print durability on ceramic", "dishwasher safety", "microwave safety", "size options", "gifting"],
        "quality_h2_hint": "ceramic quality, heat-retaining walls, dishwasher-safe print",
    },
    "whiskey_bottle": {
        "keywords":    ["whiskey bottle", "wine bottle", "beer bottle", "liquor bottle", "spirit bottle", "bourbon bottle"],
        "label":       "Decorative Bottle",
        "item_word":   "decorative bottle",
        "material":    "high-quality glass or crystal-like material with premium printing",
        "use_case":    "display piece, bar cart decor, collector's item, gift — NOT for drinking, contains no liquid",
        "styling":     "Place on bar cart, shelf, or display case. Pairs with cocktail glasses, vintage barware, or collectible decor.",
        "size_note":   "Standard decorative bottle size. Check product listing for exact dimensions.",
        "care":        "Hand wash gently. Avoid abrasive materials. Do not fill with liquid unless specified.",
        "faq_hints":   ["Is this bottle functional or decorative?", "Does it contain real whiskey/wine?", "What is it made of?", "How should I display it?", "Is it a good gift?"],
        "quality_h2_hint": "Premium Materials for a Stunning Display Piece",
    },
    "tumbler": {
        "keywords":    ["tumbler", "travel mug", "insulated tumbler", "20oz", "30oz", "water bottle", "stanley"],
        "label":       "Tumbler",
        "item_word":   "tumbler",
        "material":    "Double-wall vacuum insulated stainless steel construction — keeps drinks cold up to 24 hours and hot up to 12 hours. Custom all-over printed wrap with scratch-resistant coating.",
        "use_case":    "Commute, gym, travel, outdoor adventures, desk use, gifting",
        "styling":     "Take it everywhere — from morning commutes to trail hikes. Fits most standard cup holders.",
        "size_note":   "Available in 20oz and 30oz options. Choose based on your typical daily drink intake.",
        "care":        "Hand wash with mild soap and warm water. Do not put in dishwasher or microwave. Do not freeze.",
        "faq_hints":   ["insulation performance", "print durability", "size options", "care", "leakproof lid"],
        "quality_h2_hint": "double-wall insulation, all-day temperature retention, durable print",
    },
    "poster": {
        "keywords":    ["poster", "wall print", "art print", "print"],
        "label":       "Poster",
        "item_word":   "poster",
        "material":    "Printed on premium heavyweight matte or semi-gloss paper with archival-quality inks. Colors are rich, deep, and fade-resistant — built to last for years without yellowing.",
        "use_case":    "Wall art, room décor, fan display, gifting, office or studio decoration",
        "styling":     "Frame it for a gallery-quality look, or pin it as-is for a more casual vibe. Works in any room — bedroom, living room, studio, or office.",
        "size_note":   "Available in multiple sizes. Measure your wall space before ordering and consider frame size.",
        "care":        "Keep away from direct sunlight and moisture to preserve print quality. Wipe gently with a dry cloth if dusty.",
        "faq_hints":   ["print quality and paper type", "size options", "framing tips", "color accuracy", "gifting"],
        "quality_h2_hint": "archival ink, heavyweight paper, gallery-ready print",
    },
    "canvas": {
        "keywords":    ["canvas", "canvas print", "canvas wall art", "wrapped canvas"],
        "label":       "Canvas Print",
        "item_word":   "canvas print",
        "material":    "Gallery-wrapped canvas print on premium artist-grade cotton canvas stretched over a solid pine wood frame. Giclée-quality printing with UV-resistant inks that stay vibrant for decades. Ready to hang — no framing needed.",
        "use_case":    "Wall art, home décor, living room centerpiece, office, gifting",
        "styling":     "Hang as a standalone statement piece or group with other prints for a gallery wall. Suits modern, rustic, and eclectic interior styles.",
        "size_note":   "Available in multiple sizes. Measure your wall space carefully — larger prints make a bigger visual impact from across the room.",
        "care":        "Dust gently with a dry soft cloth. Avoid moisture and direct sunlight. No glass required — canvas is ready to display as-is.",
        "faq_hints":   ["canvas material and frame", "size options", "hanging hardware", "print longevity", "gifting"],
        "quality_h2_hint": "artist-grade canvas, giclée print, solid pine frame",
    },
    "rug": {
        "keywords":    ["rug", "area rug", "floor mat", "carpet"],
        "label":       "Rug / Area Rug",
        "item_word":   "rug",
        "material":    "Soft-pile woven construction with a custom full-surface print. Non-slip latex backing keeps it securely in place on hard floors. Vibrant, color-accurate print that resists fading with normal use.",
        "use_case":    "Living room, bedroom, gaming room, office, home décor accent, gifting",
        "styling":     "Place under a coffee table, beside a bed, or at an entryway. Layer over carpet for a bold look or anchor a seating area on hard floors.",
        "size_note":   "Available in multiple sizes. Measure your floor space before ordering. Larger rugs anchor a room better; smaller rugs work as accents.",
        "care":        "Vacuum regularly. Spot clean with a damp cloth and mild detergent. Avoid harsh chemicals. Some sizes are machine washable — check product listing.",
        "faq_hints":   ["print quality on fabric", "non-slip backing", "size options", "care and cleaning", "room styling"],
        "quality_h2_hint": "soft-pile weave, non-slip backing, fade-resistant full-surface print",
    },
    "phone case": {
        "keywords":    ["phone case", "iphone case", "samsung case", "mobile case", "case"],
        "label":       "Phone Case",
        "item_word":   "phone case",
        "material":    "Slim, hard-shell polycarbonate construction with a vibrant full-wrap custom print. Precise cutouts for all ports, buttons, and cameras. Provides solid drop protection while adding a layer of personal style.",
        "use_case":    "Daily phone protection, self-expression, fan display, gifting",
        "styling":     "Let your case reflect your personality — it's the accessory you carry everywhere. Pairs with any outfit or occasion.",
        "size_note":   "Available for a range of iPhone and Samsung models. Double-check your exact model number before ordering.",
        "care":        "Wipe clean with a slightly damp cloth. Remove case periodically to clean underneath. Avoid harsh solvents on the print.",
        "faq_hints":   ["device compatibility", "print durability", "drop protection level", "case thickness", "gifting"],
        "quality_h2_hint": "hard-shell protection, precision fit, vibrant full-wrap print",
    },

    # ── Fallback ──────────────────────────────────────────────────────────────
    "_default": {
        "keywords":    [],
        "label":       "Product",
        "item_word":   "product",
        "material":    "Premium materials and advanced printing technology deliver a vibrant, durable design built to last.",
        "use_case":    "Everyday use, gifting, self-expression, fan display",
        "styling":     "Versatile enough for any setting — casual or curated.",
        "size_note":   "Available in multiple options — check the product listing for details.",
        "care":        "Follow care instructions included with the product.",
        "faq_hints":   ["print/design quality", "product options", "care", "gifting", "what makes it unique"],
        "quality_h2_hint": "premium materials, durable design, built to last",
    },
}


def detect_product_type(product_name: str) -> dict:
    """
    Detect product type từ tên sản phẩm.
    Trả về PRODUCT_CONTEXT entry phù hợp nhất.
    Fallback về "_default" nếu không match.
    """
    name_lower = product_name.lower()

    # Sort theo keyword length giảm dần để match dài nhất trước
    # (tránh "mug" match trước "coffee mug")
    sorted_types = sorted(
        [(k, v) for k, v in PRODUCT_CONTEXT.items() if k != "_default"],
        key=lambda x: max((len(kw) for kw in x[1]["keywords"]), default=0),
        reverse=True,
    )

    for type_key, ctx in sorted_types:
        for kw in ctx["keywords"]:
            # Word boundary check cho keyword ngắn (≤6 chars) tránh substring match
            # Ví dụ: "mug" không match "smuggler", "tee" không match "teeth"
            if len(kw.strip()) <= 5:
                pattern = rf"(?<![a-zA-Z]){re.escape(kw.strip())}(?![a-zA-Z])"
                if re.search(pattern, name_lower):
                    print(f"[ProductType] Detected: {ctx['label']} (matched: '{kw}')")
                    return ctx
            elif kw in name_lower:
                print(f"[ProductType] Detected: {ctx['label']} (matched: '{kw}')")
                return ctx

    print(f"[ProductType] No match — using default for: {product_name[:60]}")
    return PRODUCT_CONTEXT["_default"]


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

# ── Bước 1: AI tự chọn external link phù hợp nhất ─────────────────────────────
SYSTEM_EXTERNAL_RESOLVER = """You are an SEO expert. Given a product name, find the single most relevant external authority URL to cite in the product description.

Return ONLY a JSON object with exactly 2 keys:
{"url": "https://...", "anchor_hint": "short natural phrase describing this topic"}

Rules:
- Choose the URL that best matches the product PRIMARY topic/niche
- Prefer specific entity pages over generic hub pages
- Allowed sources:
    Wikipedia        → any topic (sports, music, film, history, pop culture, anime)
    Rolling Stone    → music artists, bands, albums, rock/pop culture
    Billboard        → music charts, pop/hip-hop/country artists
    IMDb             → movies, TV shows, actors, directors
    Rotten Tomatoes  → film and TV reviews
    MyAnimeList      → anime series, manga titles
    ESPN             → professional sports teams, athletes, leagues
    Britannica       → broad historical/cultural topics
    KnowYourMeme     → internet memes, viral trends
- For crossover products (e.g. "Peanuts x UConn basketball shirt"):
    → If sports team is the main subject → use sports URL
    → If the character/IP is the main subject → use character/pop culture URL
    → If genuinely both → pick whichever the design emphasizes more
- anchor_hint: a 3-6 word natural phrase that could work as anchor text inline
  (e.g. "the legacy of college basketball", "what Peanuts meant to a generation")
  NOT: "this link", "here", "learn more", "popular culture"
- Return ONLY the JSON object, nothing else.
"""

# {store_name} và {shortcode} được .format() trước khi gửi API
SYSTEM_DESC_TEMPLATE = '''\
You are an expert SEO copywriter for {store_name}, a Print-on-Demand store selling custom-printed products across apparel, accessories, and home goods.
Your task: Write a WooCommerce product description in HTML — MINIMUM 630 words, TARGET 640-650 words.
⚠️ WORD COUNT IS MANDATORY: Counting only visible text (no HTML tags). Fewer than 630 words = FAIL.
Return ONLY raw HTML. No JSON, no markdown, no text outside HTML.
Allowed tags: <h2> <p> <strong> <br> <a>. Links: plain <a href="..."> only.

IMPORTANT: Use the PRODUCT CONTEXT block provided in the user message to write accurate, product-specific content.
Do NOT assume the product is a shirt unless it is explicitly a shirt.
Adapt material description, styling tips, FAQ questions, and care instructions to match the actual product type.

━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — DETECT (do not output):
━━━━━━━━━━━━━━━━━━━━━━━
NICHE CONTEXT will be provided in the user message via NICHE PROFILE block.
Use it to guide every writing decision below.

STEP A — PARSE (do not output):
  Extract 2-4 CORE KEYWORDS from the product title:
  - Remove filler words: shirt, hoodie, mug, gift, perfect, funny, cute, design
  - Keep: entities (names, teams, breeds), events (anniversary, Christmas, game day),
           identities (mom, veteran, teacher), concepts (freedom, independence, loyalty)
  Example: "250 Years America Anniversary 250th Independence Day Freedom Shirt"
  → Core keywords: ["250 Years", "Independence Day", "America", "Freedom"]

STEP B — CONTEXT (do not output):
  Identify from the NICHE PROFILE block:
  - What is the main subject (team, breed, holiday, person, concept)?
  - What is the emotional angle (pride, humor, nostalgia, identity)?
  - Who is the audience (fan, owner, profession, family role)?

STEP C — H2 ANGLE (do not output):
  Choose ONE angle for the first H2 from the niche profile h2_angles.
  The H2 MUST:
  ✓ Contain at least 1-2 core keywords (NOT the full product name)
  ✓ Add a semantic phrase that gives meaning beyond description
  ✓ Feel written by an insider of this niche, NOT a seller
  ✓ Be 5-12 words total
  The H2 MUST NOT:
  ✗ Repeat the full product title
  ✗ Use generic phrases (speaks volumes, true fans, must have, stands out)
  ✗ Sound like a marketing tagline

  FORMULA: [1-2 core keywords] + [semantic meaning phrase from niche angle]
  Example product: "250 Years America Anniversary 250th Independence Day Freedom Shirt"
  Core keywords extracted: "250 Years", "Independence Day"
  Niche angle: historical milestone
  ✓ GOOD H2: "250 Years of Independence — A Milestone Americans Actually Feel"
  ✓ GOOD H2: "Independence Day Legacy Written in Red, White, and Blue"
  ✗ BAD H2:  "250 Years America Anniversary 250th Independence Day Freedom Shirt" (full title)
  ✗ BAD H2:  "250 Years America Anniversary 250th Independence Day Freedom Shirt That Speaks Volumes"

VOICE TABLE (based on niche detected):
  music      → fan who owns the vinyl. Ref: wikipedia.org, rollingstone.com, billboard.com
  anime      → fandom insider since before mainstream. Ref: wikipedia.org, myanimelist.net
  movie      → someone who never skips the credits. Ref: imdb.com, wikipedia.org, rottentomatoes.com
  sports     → fan in the front row. Ref: espn.com, wikipedia.org, nfl.com, nba.com, mlb.com, nhl.com
  political  → proud American who knows the history. Ref: wikipedia.org
  meme       → got the joke before it went viral. Ref: wikipedia.org, knowyourmeme.com
  nurse      → colleague who worked the overnight shift. Ref: wikipedia.org
  teacher    → educator who shows up every single day. Ref: wikipedia.org
  fishing    → angler who was out at 5am and loved it. Ref: wikipedia.org
  hunting    → hunter who knows the land by heart. Ref: wikipedia.org
  camping    → someone who unplugs and lives for the trail. Ref: wikipedia.org
  farming    → raised on a farm, carries that identity. Ref: wikipedia.org
  military   → veteran who served and wears it with pride. Ref: wikipedia.org
  gym        → lifter who is there before most people wake up. Ref: wikipedia.org
  gaming     → gamer with 500+ hours logged. Ref: wikipedia.org
  beer       → craft beer fan who knows every style. Ref: wikipedia.org
  coffee     → person for whom coffee is a personality trait. Ref: wikipedia.org
  family     → someone who wears their family role as a badge. Ref: wikipedia.org
  christmas  → decorates November 1st, has opinions on eggnog. Ref: wikipedia.org
  halloween  → has costume planned months in advance. Ref: wikipedia.org
  dog        → dog owner who talks to their dog like a person. Ref: wikipedia.org, akc.org
  cat        → cat owner who knows the cat is in charge. Ref: wikipedia.org
  horse      → equestrian who considers the stable a second home. Ref: wikipedia.org
  bird       → birder with a life list and binoculars. Ref: wikipedia.org
  motivational → coach who means every word and has lived the grind. Ref: wikipedia.org
  vintage    → prefers the original to the remaster. Ref: wikipedia.org
  general    → confident insider tone. Ref: wikipedia.org

━━━━━━━━━━━━━━━━━━━━━━━
NICHE CONSISTENCY (HARD RULE — AUTO-FAIL IF BROKEN):
━━━━━━━━━━━━━━━━━━━━━━━
You MUST stay strictly within the detected niche throughout the ENTIRE description.

- niche = music/fan  → reference artist, song, album, concert, fan culture ONLY
  ✗ NEVER: shift, break room, hospital, coworker, workplace
- niche = sports     → reference team, game, player, fan identity ONLY
  ✗ NEVER: unrelated professions, generic lifestyle scenarios
- niche = anime/movie → reference characters, scenes, fandom knowledge ONLY
  ✗ NEVER: job context, shift, office, generic life advice
- niche = nurse/job  → shift, patient, coworker context is OK
- niche = general    → stay product-focused, identity-focused
  ✗ NEVER: invent fictional job scenarios

If ANY sentence drifts outside the niche → REWRITE that sentence before outputting.

━━━━━━━━━━━━━━━━━━━━━━━
VOICE RULES:
━━━━━━━━━━━━━━━━━━━━━━━
FORBIDDEN PHRASES — auto-fail if any appear:
  ✗ "perfect for those who" / "a must-have for" / "captures the essence of"
  ✗ "not just a shirt" / "not just an item" / "not just a piece"
  ✗ "live life to the fullest" / "speaks volumes about"
  ✗ "let your apparel reflect" / "is your new wardrobe essential"
  ✗ ANY variant of "[X] is more than just [clothing/apparel/garment/item of clothing]"
  ✗ "tribute to" / "celebration of" / "perfectly merging" / "standout tee"
  ✗ sizes: NEVER write "S to XXL", "small to XXL", "S through XXL" — sizes are unknown
  ✗ "official" / "officially licensed" / "official license" / "licensed" / "official merchandise" /
    "licensed product" — this is independent fan-inspired merchandise, NOT an officially
    licensed product. NEVER claim or imply official/licensed status anywhere in the copy.

INSTEAD:
  ✓ Specific situations: "If you grew up blasting rock in your room..."
  ✓ Insider references: "the kind of shirt that makes other fans nod"
  ✓ Direct second-person: "You already know what this shirt means"

━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURE:
━━━━━━━━━━━━━━━━━━━━━━━
RANK MATH:
  • Focus Keyword = product name → appears 5-7x, in first paragraph, in first H2
  • Total: MINIMUM 630 words (target 640-650). Count only visible text, not HTML tags.
  • If a section feels short, ADD 1 extra sentence — never cut content to save space.

OUTPUT ORDER — follow exactly:
  1. <p>[OPENING HOOK ~80w]</p>     ← MUST be FIRST element, BEFORE any H2
  2. <h2>[Product name + suffix]</h2>
  3. {shortcode}
  4. <p>[DESIGN paragraph 1]</p>
  5. <p>[DESIGN paragraph 2 + external link]</p>
  6. <h2>[QUALITY H2]</h2>
  ... rest of structure

⛔ CRITICAL: First element MUST be <p>...</p> — NOT <h2>.
   If output starts with <h2> → INVALID, hook is missing.

FORBIDDEN first H2 — these will trigger auto-retry:
  ✗ "[Name]" alone — always add suffix
  ✗ "[Name] That Speaks Volumes" — generic filler
  ✗ "[Name] For True Patriots/Fans" — generic
  ✗ "[Name] You Need" / "[Name] Must Have" — generic CTA
  ✗ "[Name] Stands Out" / "[Name] Make a Statement" — generic
  ✗ "[Name] Wear Your Beliefs/Pride" — generic
  ✗ "Unmatched Quality..." / "Quality You Can Trust" — section header, not product H2
  ✗ Any suffix under 2 meaningful words

  REQUIRED: suffix must be 2-5 words, niche-specific, fan-voice
  GOOD examples:
  ✓ "[Name] Real Fans Recognize"
  ✓ "[Name] — Tour Era Energy"
  ✓ "[Name] Every Patriot Needs in Their Closet"
  ✓ "[Name] That Drops Every Rally Room"
  ✓ "[Name] Built for the Front Row"

[OPENING HOOK] ~80w
⛔ MANDATORY: MUST be wrapped in <p>...</p> tags. MUST come BEFORE first <h2>.
WRONG: <h2>Product Name</h2> ← starts with H2, no hook
RIGHT: <p>Hook text here...</p> then <h2>...</h2>

<p>[Product name in first 20 words. Fan voice, high-impact. MUST be inside <p> tags.]</p>

<h2>[Product name + niche-matched suffix — no word overlap with product name]</h2>
{shortcode}

[DESIGN] ~140w
<p>[75w: Specific visual details — exact colors, text elements, layout. One cultural reaction.]</p>
<p>[65w: Deeper cultural reference. Inline EXTERNAL LINK naturally — see LINKS section below.]</p>

[QUALITY] ~110w
<h2>[Quality H2 — use PRODUCT CONTEXT quality_h2_hint as inspiration, add niche flavor]</h2>
<p>[55w: Use the material description from PRODUCT CONTEXT. Be specific about what makes this product durable and high-quality.]</p>
<p>[55w: {store_name} quality commitment — direct and confident, not corporate-speak. Reference the product type naturally.]</p>

[AUDIENCE + STYLING] ~120w
<h2>[Niche-specific audience H2]</h2>
<p>[55w: Who this is for. Specific identity, not generic. Reference the product type naturally.]</p>
<p>[65w: Use styling/use-case from PRODUCT CONTEXT. 2-3 concrete tips relevant to this product type. Inline INTERNAL LINK naturally — see LINKS section below.]</p>

[FAQ] ~90w — EXACT FORMAT REQUIRED:
<h2>[Creative niche-flavored FAQ title]</h2>
<p><strong>Q1: [specific question about this design or niche — or use faq_hints from PRODUCT CONTEXT]?</strong><br>A1: [2-sentence answer. Use product-accurate facts from PRODUCT CONTEXT. No invented sizes or shipping.]</p>
<p><strong>Q2: [question about print quality or material]?</strong><br>A2: [2-sentence answer.]</p>
<p><strong>Q3: [question about styling or occasion]?</strong><br>A3: [2-sentence answer.]</p>
<p><strong>Q4: [question about care instructions]?</strong><br>A4: [2-sentence answer.]</p>
<p><strong>Q5: [question about what makes this unique]?</strong><br>A5: [2-sentence answer.]</p>
ABSOLUTE RULE: Every single Q&A must be ONE <p>...</p> block containing <strong>Q:</strong><br>A:
WRONG FORMAT (will fail):
  <strong>Q1: question?</strong>
  A1: answer.
RIGHT FORMAT:
  <p><strong>Q1: question?</strong><br>A1: answer.</p>

[CTA] ~80w
<h2>[Urgent CTA H2 — niche voice, scarcity]</h2>
<p>[80w: 3-4 sentences. Niche identity. Urgency. Mention {store_name}.]</p>

━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES:
━━━━━━━━━━━━━━━━━━━━━━━
1. {shortcode} placement: immediately after first H2, before first content paragraph
2. Never invent sizes or specific measurements unless explicitly stated in PRODUCT CONTEXT. Never invent shipping times.
3. ANCHOR TEXT: no word duplication with surrounding sentence
   WRONG: "the culture of <a>basketball culture</a>"
   RIGHT: "a sport built on <a>grit and tradition</a>"
4. Return ONLY raw HTML
'''

SYSTEM_SNIPPET_TEMPLATE = '''\
Write a Rank Math SEO meta description for a WooCommerce product.
Return ONLY a JSON object: {{"meta":"..."}}

Requirements:
- Exactly 150-160 characters (count carefully)
- Must contain "{store_name}"
- MUST contain the EXACT product name as given
- No single or double quotes inside the meta text

NICHE VOICE:
  Rock/Music → passionate fan tone
  Meme/Humor → playful insider tone
  Anime      → enthusiastic fandom tone
  Sports     → hype/pride tone
  Nurse/Job  → proud insider tone
  General    → confident specific tone

FORBIDDEN: "perfect for making a bold fashion statement" / "a must-have for anyone who loves"
FORBIDDEN: "official" / "officially licensed" / "licensed" — this is independent fan-inspired
  merchandise, NOT an officially licensed product. Never imply official/licensed status.

FORMULA: [niche hook ~30c] + [EXACT product name] + from {store_name} + [niche detail ~20c]
COUNT characters before submitting.
'''


# ══════════════════════════════════════════════════════════════════════════════
# SEOGenerator
# ══════════════════════════════════════════════════════════════════════════════

class SEOGenerator:
    def __init__(self, openai_key: str, model: str = "gpt-4o",
                 store_name: str = "", shortcode: str = "[thien_display_single_image]"):
        self.openai_key = openai_key
        self.model      = model
        self.store_name = store_name or "our store"
        self.shortcode  = shortcode or "[thien_display_single_image]"

    def _system_desc(self) -> str:
        return SYSTEM_DESC_TEMPLATE.format(
            store_name=self.store_name,
            shortcode=self.shortcode,
        )

    def _system_snippet(self) -> str:
        return SYSTEM_SNIPPET_TEMPLATE.format(store_name=self.store_name)

    # ── OpenAI call ────────────────────────────────────────────────────────────

    def _call_openai(self, system, user, image_b64="",
                     temperature=0.7, max_tokens=5000, json_mode=False) -> str:
        messages = [{"role": "system", "content": system}]
        if image_b64:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": user},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}", "detail": "auto"
                }},
            ]})
        else:
            messages.append({"role": "user", "content": user})

        payload = {"model": self.model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.openai_key}",
                     "Content-Type": "application/json; charset=utf-8"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=120,
        )
        if r.status_code != 200:
            try:    err = r.json()["error"]["message"]
            except: err = r.text[:300]
            raise Exception(f"OpenAI error {r.status_code}: {err}")
        return r.json()["choices"][0]["message"]["content"] or ""

    def _detect_niche_ai(self, product_name: str) -> str:
        """
        Dùng AI để detect niche chính xác — không bị giới hạn bởi keyword list.
        Fallback về link_resolver.detect_niche() nếu API fail.
        """
        from link_resolver import detect_niche as detect_niche_kw
        try:
            raw = self._call_openai(
                system=NICHE_DETECT_SYSTEM,
                user=f'Product: "{product_name}"',
                temperature=0,
                max_tokens=10,
                json_mode=False,
            )
            niche = raw.strip().lower().split()[0]
            valid = {"music", "anime", "movie", "sports", "political",
                     "meme", "nurse", "motivational", "vintage", "dog", "cat", "general"}
            if niche in valid:
                print(f"[NicheAI] {product_name[:40]} → {niche}")
                return niche
        except Exception as e:
            print(f"[NicheAI] fallback to keyword ({e})")
        return detect_niche_kw(product_name)

    def _resolve_external_link(self, product_name: str, category: str = "") -> dict:
        """
        Bước 1: Gọi AI để xác định external link phù hợp nhất cho sản phẩm.
        Trả về {"url": str, "anchor_hint": str}
        Fallback về Wikipedia Popular_culture nếu AI fail.
        """
        fallback = {
            "url": "https://en.wikipedia.org/wiki/Popular_culture",
            "anchor_hint": "pop culture"
        }
        try:
            user_msg = f'Product name: "{product_name}"'
            if category:
                user_msg += f'\nCategory: {category}'
            raw = self._call_openai(
                system=SYSTEM_EXTERNAL_RESOLVER,
                user=user_msg,
                temperature=0.2,
                max_tokens=120,
                json_mode=True,
            )
            data = json.loads(raw)
            url  = data.get("url", "").strip()
            hint = data.get("anchor_hint", "").strip()
            if url and url.startswith("http"):
                return {"url": url, "anchor_hint": hint or "related topic"}
        except Exception as e:
            print(f"[ExternalLink] fallback ({e})")
        return fallback

    @staticmethod
    def image_to_b64(image_path: str, max_dim: int = 512) -> str:
        try:
            from PIL import Image as PILImage
            import io
            with PILImage.open(image_path) as img:
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.thumbnail((max_dim, max_dim), PILImage.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=80)
                return base64.b64encode(buf.getvalue()).decode()
        except Exception:
            return ""

    # ── Generate description ───────────────────────────────────────────────────

    def generate_description(self, product_name: str, category: str = "",
                              image_path: str = "",
                              link_config: dict | None = None,
                              round_robin_index: int = 0) -> str:
        """
        Generate HTML description.
        link_config: từ credentials.get_link_config(store_url)
        round_robin_index: vị trí trong pool (quản lý bởi BulkSEOWorker)
        """
        resolved  = resolve(product_name, link_config, round_robin_index)
        cat_line  = f"Category: {category}" if category else ""

        # ── Detect product type ───────────────────────────────────────────────
        ptype_ctx = detect_product_type(product_name)

        # ── Bước 0: AI detect niche (chính xác hơn keyword-based) ────────────
        ai_niche = self._detect_niche_ai(product_name)
        # Override niche trong resolved nếu AI detect khác keyword
        if ai_niche != resolved["niche"]:
            print(f"[NicheAI] Override: {resolved['niche']} → {ai_niche}")
            resolved = dict(resolved)
            resolved["niche"] = ai_niche

        # ── Bước 1: AI xác định external link phù hợp ────────────────────────
        ext = self._resolve_external_link(product_name, category)
        external_url   = ext["url"]
        external_hint  = ext["anchor_hint"]

        # ── Build internal link instruction ───────────────────────────────────
        if resolved["internal_url"]:
            _mode = resolved.get("internal_mode", "category")
            if _mode == "product":
                _anchor_rule = (
                    f"  ANCHOR RULE — PRODUCT mode:\n"
                    f"    Anchor MUST use key words from the linked product title above.\n"
                    f"    GOOD: title='Ariana Grande My Everything Lilac Poster T-Shirt'\n"
                    f"    → anchor: 'the Ariana Grande My Everything Lilac Poster T-Shirt'\n"
                    f"    BAD (BANNED): 'the rest of the gear', 'check out more', 'complete your look'"
                )
            else:
                _anchor_rule = (
                    f"  ANCHOR RULE — CATEGORY mode:\n"
                    f"    Anchor MUST naturally reference the category: '{resolved['internal_title']}'.\n"
                    f"    GOOD: 'our {resolved['internal_title']} collection', 'more {resolved['internal_title']} gifts'\n"
                    f"    BAD (BANNED): invent a different URL, use unrelated category name"
                )
            internal_instruction = (
                f"INTERNAL LINK (use this EXACT URL — do NOT change or invent another URL):\n"
                f"  URL: {resolved['internal_url']}\n"
                f"  Category/Title: \"{resolved['internal_title']}\"\n"
                f"{_anchor_rule}\n"
                f"  Embed naturally in the Audience/Styling section as inline link."
            )
        else:
            internal_instruction = (
                "INTERNAL LINK: None available for this product — skip the internal link entirely. "
                "Do NOT invent a URL."
            )

        user_text = (
            f"Product name: {product_name}\n"
            f"{cat_line}\n\n"
            f"DETECTED CONTEXT (do not output):\n"
            f"  Niche: {resolved['niche']}"
            + (f" | Occasion: {resolved['occasion']}" if resolved["occasion"] else "")
            + (f" | Sport: {resolved['sport']}" if resolved["sport"] else "")
            + "\n\n"
            f"NICHE PROFILE (use this to control voice, angle, and H2):\n"
            f"  Niche        : {ai_niche}\n"
            f"  Angle        : {get_niche_profile(ai_niche)['angle']}\n"
            f"  Emotion      : {get_niche_profile(ai_niche)['emotion']}\n"
            f"  Write from POV of: {get_niche_profile(ai_niche)['pov']}\n"
            f"  Context refs : {', '.join(get_niche_profile(ai_niche)['context_refs'][:5])}\n"
            f"  H2 angles    : {', '.join(get_niche_profile(ai_niche)['h2_angles'])}\n"
            f"  Voice rule   : {get_niche_profile(ai_niche)['voice_rule']}\n\n"
            f"PRODUCT CONTEXT (use this for accurate product-specific writing):\n"
            f"  Product type : {ptype_ctx['label']}\n"
            f"  Item word    : Use '{ptype_ctx['item_word']}' instead of 'shirt' when referring to this product\n"
            f"  Material     : {ptype_ctx['material']}\n"
            f"  Use case     : {ptype_ctx['use_case']}\n"
            f"  Styling tips : {ptype_ctx['styling']}\n"
            f"  Size note    : {ptype_ctx['size_note']}\n"
            f"  Care         : {ptype_ctx['care']}\n"
            f"  FAQ hints    : {', '.join(ptype_ctx['faq_hints'])}\n"
            f"  Quality H2   : {ptype_ctx['quality_h2_hint']}\n\n"
            f"OPENING HOOK STYLE (use exactly this format):\n"
            f"  {resolved['hook_style']}\n"
            f"  FORBIDDEN opening: 'If you [verb] [topic], the [Product] is your [noun]'\n\n"
            f"EXTERNAL LINK (use this exact URL — do not change it):\n"
            f"  URL: {external_url}\n"
            f"  Suggested anchor topic: \"{external_hint}\"\n"
            f"  Rule: Use the suggested topic as inspiration, NOT verbatim as anchor.\n"
            f"  Write an anchor that fits naturally mid-sentence in the Design section.\n"
            f"  GOOD anchors: 'the legacy of college basketball', 'what made Peanuts iconic', 'decades of Snoopy fandom'\n"
            f"  BAD anchors: 'this link', 'here', 'learn more', 'popular culture', any generic phrase\n"
            f"  Embed inline — never as end-of-sentence standalone click.\n\n"
            f"{internal_instruction}\n\n"
            f"CRITICAL RULES:\n"
            f'1. Focus Keyword = "{product_name}" — must appear 5-7 times\n'
            f"2. Focus Keyword in first paragraph (first 20 words)\n"
            f"3. Focus Keyword in the FIRST H2 heading\n"
            f"4. {self.shortcode} immediately after first H2\n"
            f"5. Never invent sizes (S to XXL) or shipping times\n"
            f"6. Return ONLY raw HTML\n\n"
            f"Write the FULL HTML description for: {product_name}\n"
            f"WORD COUNT REQUIREMENT: minimum 630 visible words (target 640-650).\n"
            f"Count: Opening~80w + Design~140w + Quality~110w + Audience~120w + FAQ~90w + CTA~80w = 620w base.\n"
            f"Expand each section slightly if needed to reach 630+ words."
        ).strip()

        image_b64 = self.image_to_b64(image_path) if image_path else ""

        # Retry logic:
        #   - Niche/structure/anchor: tối đa 3 lần
        #   - Word count: tối đa 1 lần retry riêng (tiết kiệm token)
        max_attempts   = 3
        wc_retry_done  = False   # word count chỉ retry 1 lần duy nhất
        base_prompt    = user_text
        for attempt in range(1, max_attempts + 1):
            html = self._call_openai(self._system_desc(), user_text, image_b64,
                                      temperature=0.7 + (attempt - 1) * 0.05,
                                      max_tokens=5000)
            html = re.sub(r"```[a-z]*\n?", "", html).strip()

            # Chỉ check các lỗi ảnh hưởng SEO thật sự
            # Bỏ forbidden phrases + generic writing (không ảnh hưởng SEO, tốn token)
            niche_v     = check_hook_niche(html, resolved["niche"])
            structure_v = check_structure(html, self.shortcode, product_name)
            anchor_v    = check_anchor_quality(html)
            license_v   = check_licensing_claims(html)

            internal_title = resolved.get("internal_title", "")
            internal_url   = resolved.get("internal_url", "")

            # ── Word count check — chỉ retry 1 lần ──────────────────────────
            wc = count_words_html(html)
            wc_v = []
            if wc < 630:
                if not wc_retry_done:
                    wc_v = [f"word_count_low:{wc}"]
                    print(f"[SEO] Word count: {wc} words (need ≥630) — sẽ retry 1 lần")
                else:
                    print(f"[SEO] Word count: {wc} words (vẫn thiếu nhưng đã dùng hết wc retry — bỏ qua)")
            else:
                print(f"[SEO] Word count: {wc} words ✓")

            critical_violations = niche_v + structure_v + anchor_v + wc_v + license_v

            if not critical_violations:
                return html

            print(f"[SEO] Attempt {attempt}: {len(critical_violations)} critical issue(s): {critical_violations[:4]}")
            if attempt < max_attempts:
                instructions = []

                if niche_v:
                    drift_words = [v.split(":")[1].strip() for v in niche_v if ":" in v]
                    instructions.append(
                        f"NICHE DRIFT — Remove context words: {', '.join(drift_words[:3])}. "
                        f"Rewrite opening <p> in {resolved['niche']} fan voice only."
                    )

                if [v for v in structure_v if "faq_format" in v]:
                    instructions.append(
                        "FAQ FORMAT — Every Q&A MUST use exactly: "
                        "<p><strong>Q1: question?</strong><br>A1: answer.</p> "
                        "No standalone <strong> tags outside <p>."
                    )

                if [v for v in structure_v if "missing_opening_hook" in v]:
                    instructions.append(
                        f"MISSING HOOK — Output MUST start with <p>opening hook</p> BEFORE first <h2>. "
                        f"First element cannot be <h2>. "
                        f"Write an 80-word fan-voice opening paragraph first, "
                        f"then <h2>{product_name} [suffix]</h2>."
                    )

                if [v for v in structure_v if "missing_links" in v or "missing_external" in v]:
                    instructions.append(
                        "MISSING LINKS — Need 1 external authority link "
                        "(wikipedia/espn/rollingstone etc.) AND 1 internal product link."
                    )

                h2_errors = [v for v in structure_v if "h2_no_suffix" in v
                             or "h2_weak_suffix" in v or "h2_generic_suffix" in v]
                if h2_errors:
                    instructions.append(
                        f"H2 SUFFIX ERROR — First H2 has a bad or missing suffix.\n"
                        f"  Current issue: {h2_errors[0]}\n"
                        f"  RULE: Product name + niche-specific suffix (2-5 meaningful words).\n"
                        f"  GOOD examples:\n"
                        f"  - '{product_name} That Real Fans Recognize'\n"
                        f"  - '{product_name} — Tour Era Energy'\n"
                        f"  - '{product_name} Every Fan Needs'\n"
                        f"  BAD examples (rejected):\n"
                        f"  - '{product_name}' (name alone)\n"
                        f"  - '{product_name} Tee' (suffix too short)\n"
                        f"  - '{product_name} Quality You Can Trust' (generic)\n"
                        f"  Pick a suffix that matches the detected niche: {resolved['niche']}"
                    )

                if license_v:
                    instructions.append(
                        f"LICENSING CLAIM — Found forbidden word(s): {', '.join(v.split(':')[1] for v in license_v)}. "
                        f"This is independent fan-inspired merchandise, NOT an officially licensed product. "
                        f"Remove every use of 'official'/'officially'/'license'/'licensed'/'licensing' "
                        f"anywhere in the HTML — rephrase those sentences without claiming official/licensed status."
                    )

                if anchor_v:
                    if internal_title and internal_url:
                        instructions.append(
                            f"BAD ANCHOR — Internal link anchor is generic. "
                            f"The linked product title is: '{internal_title}'. "
                            f"Anchor MUST use this title, e.g. 'the {internal_title}' "
                            f"or key words from it. "
                            f"NEVER use: 'the rest of the...', 'check out more', 'see more'."
                        )
                    else:
                        instructions.append(
                            "BAD ANCHOR — Use specific product title words as anchor. "
                            "NEVER use generic phrases like 'the rest of the...'."
                        )

                if wc_v:
                    short_by = 630 - wc
                    instructions.append(
                        f"WORD COUNT TOO SHORT — Current: {wc} words. Need at least 630. "
                        f"You are {short_by} words short. "
                        f"Expand these sections to add more content:\n"
                        f"  • Opening hook: add 1-2 sentences of fan context (~15-20w)\n"
                        f"  • Design section: add 1 more specific visual/cultural detail (~20w)\n"
                        f"  • FAQ: expand each answer by 1 sentence (~30w total)\n"
                        f"  • CTA: add 1 urgency sentence (~15w)\n"
                        f"Do NOT add filler. Every added sentence must be specific and on-niche."
                    )
                    wc_retry_done = True  # đánh dấu đã dùng wc retry

                fix_block = "\n".join(f"  {i+1}. {inst}" for i, inst in enumerate(instructions))
                user_text = base_prompt + f"""

⛔ RETRY #{attempt} — Fix these CRITICAL SEO issues:
{fix_block}

Return the COMPLETE corrected HTML."""

        # Trả về bài cuối dù vẫn còn violation (đã thử hết)
        print(f"[SEO] Warning: returning after {max_attempts} attempts, some violations may remain")
        return html

    # ── Generate snippet ───────────────────────────────────────────────────────

    def generate_snippet(self, product_name: str, existing_description: str = "") -> str:
        context   = existing_description[:400] if existing_description else product_name
        user_text = (
            f'Product name (MUST appear verbatim): "{product_name}"\n'
            f"Context: {context}\n\n"
            f'Write meta 150-160 chars. Must include exact product name "{product_name}" '
            f'and "{self.store_name}".'
        )
        raw = self._call_openai(self._system_snippet(), user_text,
                                 temperature=0.5, max_tokens=250, json_mode=True)
        try:
            meta = json.loads(raw).get("meta", "")
        except Exception:
            m    = re.search(r'"meta"\s*:\s*"([^"]+)"', raw)
            meta = m.group(1) if m else ""
        if not meta:
            raise Exception("Không parse được snippet từ AI response")
        return self._fix_meta(meta, product_name)

    def _fix_meta(self, meta: str, product_name: str) -> str:
        meta = meta.strip()
        store = self.store_name
        if store not in meta:
            meta = meta.rstrip(".") + f" from {store}."
        if len(meta) > 160:
            meta = meta[:157]
            pos  = meta.rfind(" ")
            if pos > 130: meta = meta[:pos]
            meta = meta.rstrip(" .,") + "."
        if len(meta) < 140:
            meta = meta.rstrip(".") + f" Shop now at {store}."
        return meta[:160].strip()

    # ── Generate + update WooCommerce ─────────────────────────────────────────

    def generate_and_update(self, wc_api, product_id: int, product_name: str,
                             category: str = "", image_path: str = "",
                             link_config: dict | None = None,
                             round_robin_index: int = 0,
                             progress_callback=None) -> dict:
        def _p(msg):
            if progress_callback: progress_callback(msg)

        result = {"success": False, "description": "", "snippet": "", "error": ""}

        # Step 1: description
        try:
            _p(f"🤖 Generating description: {product_name}...")
            desc = self.generate_description(
                product_name, category, image_path, link_config, round_robin_index
            )
            result["description"] = desc
            _p(f"✓ Description done ({len(desc)} chars)")
        except Exception as e:
            result["error"] = f"Description error: {e}"; return result

        # Step 2: snippet
        try:
            _p(f"🤖 Generating snippet: {product_name}...")
            plain   = re.sub(r"<[^>]+>", " ", desc)
            plain   = re.sub(r"\s+", " ", plain).strip()
            snippet = self.generate_snippet(product_name, plain[:400])
            result["snippet"] = snippet
            _p(f"✓ Snippet done ({len(snippet)} chars)")
        except Exception as e:
            result["error"] = f"Snippet error: {e}"; return result

        # Step 3: update WooCommerce
        try:
            _p(f"📡 Updating WooCommerce #{product_id}...")
            plain_for_score = re.sub(r"<[^>]+>", " ", desc)
            word_count      = len(plain_for_score.split())
            est_score       = min(85, 60
                                  + (10 if word_count >= 600 else 0)
                                  + (10 if snippet else 0)
                                  + (5 if product_name.lower() in plain_for_score.lower() else 0))
            update_res = wc_api.update_product(product_id, {
                "description": desc,
                "meta_data": [
                    {"key": "rank_math_description",   "value": snippet},
                    {"key": "rank_math_focus_keyword", "value": product_name},
                    {"key": "rank_math_seo_score",     "value": str(est_score)},
                    {"key": "rank_math_robots",        "value": ["index", "follow"]},
                ],
            })
            if not update_res["success"]:
                raise Exception(update_res["error"])
            result["success"] = True
            _p(f"✅ Done: {product_name} (est. score ~{est_score})")
        except Exception as e:
            result["error"] = f"WooCommerce update error: {e}"

        return result


# ══════════════════════════════════════════════════════════════════════════════
# BulkSEOWorker — quản lý round-robin index
# ══════════════════════════════════════════════════════════════════════════════


# Web version — BulkSEOWorker được thay bằng Celery task
class BulkSEOWorker:
    pass

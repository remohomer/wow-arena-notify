# core/tag_detector.py — v5 ✅
"""
Full-border detection for QueuePopNotify RimFrame Edition
Works with WoW Arena Notify v4.20+
"""

from PIL import Image


def _detect_border_color(img):
    w, h = img.size
    sampling = 10  # check every Nth pixel for performance

    border_pixels = []

    # top & bottom borders
    for x in range(0, w, sampling):
        border_pixels.append(img.getpixel((x, 0)))
        border_pixels.append(img.getpixel((x, h - 1)))

    # left & right borders
    for y in range(0, h, sampling):
        border_pixels.append(img.getpixel((0, y)))
        border_pixels.append(img.getpixel((w - 1, y)))

    # Analyze samples
    green_hits = 0
    red_hits = 0

    for (r, g, b) in border_pixels:
        if g > 200 and r < 50 and b < 50:
            green_hits += 1
        if r > 200 and g < 50 and b < 50:
            red_hits += 1

    if green_hits > 3:  # ≥ 4 matching samples to detect POP
        return "arena_pop"
    if red_hits > 3:  # ≥ 4 matching samples to detect ENTER/EXPIRE
        return "arena_stop"

    return None


def detect_tag(path: str) -> str | None:
    try:
        img = Image.open(path).convert("RGB")
        return _detect_border_color(img)
    except Exception:
        return None

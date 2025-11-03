# -*- coding: utf-8 -*-
from PIL import Image
from infrastructure.logger import logger

def _detect_border_color(img):
    w, h = img.size
    sampling = 10

    border_pixels = []
    for x in range(0, w, sampling):
        border_pixels.append(img.getpixel((x, 0)))
        border_pixels.append(img.getpixel((x, h - 1)))
    for y in range(0, h, sampling):
        border_pixels.append(img.getpixel((0, y)))
        border_pixels.append(img.getpixel((w - 1, y)))

    green_hits = red_hits = 0
    for px in border_pixels:
        r, g, b = px
        if g > 200 and r < 50 and b < 50:
            green_hits += 1
        if r > 200 and g < 50 and b < 50:
            red_hits += 1

    if green_hits > 3:
        return "arena_pop"
    if red_hits > 3:
        return "arena_stop"
    return None

def detect_tag(path: str) -> str | None:
    try:
        img = Image.open(path).convert("RGB")
        return _detect_border_color(img)
    except Exception as e:
        logger.dev(f"detect_tag failed for {path}: {e}")
        return None

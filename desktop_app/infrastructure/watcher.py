# -*- coding: utf-8 -*-
"""
Filesystem helpers:
- Resolve WoW Screenshots folder (cached)
- Enumerate screenshots
- Backup new screenshots to AppData on app start
"""

import os
import shutil
import time
from pathlib import Path
from functools import lru_cache
from typing import Optional, Tuple, List

from infrastructure.logger import logger

# ---------- Paths ----------
def get_backup_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local"))
    d = base / "WoWArenaNotify" / "screenshots_backup"
    d.mkdir(parents=True, exist_ok=True)
    return d

@lru_cache(maxsize=1)
def resolve_screenshots_folder(base: str) -> Optional[Path]:
    base = Path(base or "")
    if not base.exists():
        logger.user("📁❓ Screenshots folder not set yet.")
        return None

    candidates = [
        base / "_classic_" / "Screenshots",
        base / "_classic_era_" / "Screenshots",
        base / "_classic_ptr_" / "Screenshots",
        base / "_retail_" / "Screenshots",
        base / "Screenshots",
    ]
    for c in candidates:
        if c.exists():
            # one-time informative log
            logger.user(f"📁 Screenshots folder: {c}")
            return c

    logger.user("No Screenshots folder found under the selected WoW path.")
    return None

# ---------- Enumeration ----------
def _is_screenshot(p: Path) -> bool:
    if not p.is_file():
        return False
    ext = p.suffix.lower()
    return ext in (".png", ".jpg", ".jpeg", ".tga", ".bmp")

def list_screenshots(dir_path: Path) -> List[Path]:
    try:
        return sorted([p for p in dir_path.iterdir() if _is_screenshot(p)], key=lambda x: x.stat().st_mtime)
    except Exception:
        return []

def get_latest_screenshot_info(base_wow_folder: str) -> Tuple[Optional[Path], Optional[float]]:
    folder = resolve_screenshots_folder(base_wow_folder)
    if not folder:
        return None, None
    shots = list_screenshots(folder)
    if not shots:
        return None, None
    p = shots[-1]
    try:
        return p, p.stat().st_mtime
    except Exception:
        return None, None

# ---------- Backup on start ----------
def safe_copy(src: Path, dst: Path) -> bool:
    try:
        if not dst.exists():
            shutil.copy2(src, dst)
            return True
    except Exception:
        pass
    return False

def backup_all_screenshots(base_wow_folder: str) -> None:
    folder = resolve_screenshots_folder(base_wow_folder)
    if not folder:
        return

    dst_root = get_backup_dir()
    copied = 0
    skipped = 0

    for p in list_screenshots(folder):
        dst = dst_root / p.name
        if safe_copy(p, dst):
            copied += 1
        else:
            skipped += 1

    logger.user(f"Backup complete. Copied:{copied}, Skipped:{skipped}, From:{folder}")

# -*- coding: utf-8 -*-
# ✅ Persistent desktop_id (UUID4)
# ✅ Safe load/save with fallback defaults
# ✅ Quiet save (no spam)
# ✅ English logs only

import json
import os
import uuid
from pathlib import Path
from typing import Dict
from infrastructure.logger import logger


def get_appdata_dir() -> Path:
    """Return AppData\\Local\\WoWArenaNotify (create if missing)."""
    appdata = Path(os.getenv("APPDATA") or Path.home() / "AppData/Roaming")
    local_appdata = Path(os.getenv("LOCALAPPDATA", appdata))
    app_dir = local_appdata / "WoWArenaNotify"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


APP_DIR: Path = get_appdata_dir()
CONFIG_FILE: Path = APP_DIR / "config.json"

# Expose the path to logger and others
os.environ["WOW_ARENA_NOTIFY_CONFIG"] = str(CONFIG_FILE.resolve())


# -------------------------------------------------------
# Default config (dodałem first_run=True)
# -------------------------------------------------------
DEFAULT_CFG: Dict[str, object] = {
    "game_folder": "",
    "countdown_time": 36,
    "pairing_id": "",
    "device_id": "",
    "device_secret": "",
    "desktop_id": "",
    "delay_offset": 2,
    "first_run": True,   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
}


def ensure_desktop_id(cfg: dict) -> dict:
    """Generate persistent local desktop_id if missing."""
    if not cfg.get("desktop_id"):
        cfg["desktop_id"] = str(uuid.uuid4())
        save_config(cfg)
        logger.info(f"💻 Generated new desktop_id: {cfg['desktop_id']}")
    return cfg


def load_config() -> dict:
    """Load config from disk or use defaults."""
    data: Dict[str, object] = {}

    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            logger.info("⚠ No config.json found — using defaults.")
    except Exception as e:
        logger.warning(f"⚠ Could not read config.json: {e}")
        data = {}

    # Remove legacy keys
    for legacy_key in ["firebase_sa_path", "rtdb_url"]:
        if legacy_key in data:
            data.pop(legacy_key, None)
            logger.info(f"🧹 Removed legacy field '{legacy_key}'.")

    cfg = {**DEFAULT_CFG, **data}
    cfg = ensure_desktop_id(cfg)

    # Save if file missing (first run)
    if not CONFIG_FILE.exists():
        save_config(cfg)

    logger.dev(f"⚙️ Config loaded from {CONFIG_FILE}")
    return cfg


def save_config(cfg: dict):
    """Save config silently (no user spam)."""
    try:
        for k, v in DEFAULT_CFG.items():
            cfg.setdefault(k, v)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Failed to save config.json: {e}")

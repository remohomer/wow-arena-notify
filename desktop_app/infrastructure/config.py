# -*- coding: utf-8 -*-
# ✅ Persistent desktop_id (UUID4)
# ✅ Safe load/save with fallback defaults
# ✅ Protect non-empty keys from being overwritten by empty values
# ✅ Atomic writes

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
# Default config
# -------------------------------------------------------
DEFAULT_CFG: Dict[str, object] = {
    "game_folder": "",
    "countdown_time": 36,
    "pairing_id": "",
    "device_id": "",
    "device_secret": "",
    "desktop_id": "",
    "delay_offset": 2,
    "first_run": True,
}

_PROTECTED_KEYS = ("pairing_id", "device_id", "device_secret", "game_folder")


def _atomic_write(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def ensure_desktop_id(cfg: dict) -> dict:
    """Generate persistent local desktop_id if missing."""
    if not cfg.get("desktop_id"):
        cfg["desktop_id"] = str(uuid.uuid4())
        # zapis będzie wykonany przez save_config wywołane wyżej w call-site
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
    for legacy_key in ("firebase_sa_path", "rtdb_url"):
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


def save_config(cfg: dict, *, protect: bool = True):
    """
    Save config with protections:
    - If protect=True (default), do NOT overwrite non-empty fields in existing config
      with empty strings from 'cfg' (guards against accidental wipes on error paths).
    - Atomic write.
    """
    try:
        # ensure all keys exist
        for k, v in DEFAULT_CFG.items():
            cfg.setdefault(k, v)

        if protect and CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    old = json.load(f)
            except Exception:
                old = {}

            # don't let empty overwrite non-empty
            for k in _PROTECTED_KEYS:
                new_val = cfg.get(k)
                old_val = old.get(k)
                if (not new_val) and old_val:
                    cfg[k] = old_val

            # desktop_id must persist if already present
            if not cfg.get("desktop_id") and old.get("desktop_id"):
                cfg["desktop_id"] = old["desktop_id"]

        text = json.dumps(cfg, indent=4, ensure_ascii=False)
        _atomic_write(CONFIG_FILE, text)

    except Exception as e:
        logger.error(f"❌ Failed to save config.json: {e}")

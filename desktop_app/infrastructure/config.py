# file: desktop_app/infrastructure/config.py
# ✅ Generates persistent desktop_id (UUID4)
# ✅ Cleans legacy keys automatically
# ✅ Safe load/save with fallback defaults
# ✅ Compatible with all modules (pairing, watcher, ui)

import json
import os
import uuid
from pathlib import Path
from typing import Dict
from infrastructure.logger import logger

# -------------------------------------------------------
# 📂 Lokalizacja pliku konfiguracyjnego
# C:\Users\<USER>\AppData\Local\WoWArenaNotify\config.json
# -------------------------------------------------------

def get_appdata_dir() -> Path:
    """Zwraca ścieżkę do folderu AppData\\Local\\WoWArenaNotify (tworzy jeśli nie istnieje)."""
    appdata = Path(os.getenv("APPDATA") or Path.home() / "AppData/Roaming")
    local_appdata = Path(os.getenv("LOCALAPPDATA", appdata))
    app_dir = local_appdata / "WoWArenaNotify"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


APP_DIR: Path = get_appdata_dir()
CONFIG_FILE: Path = APP_DIR / "config.json"

# 🔹 Udostępnij ścieżkę w zmiennej środowiskowej
os.environ["WOW_ARENA_NOTIFY_CONFIG"] = str(CONFIG_FILE.resolve())

# -------------------------------------------------------
# ⚙️ Konfiguracja domyślna
# -------------------------------------------------------

DEFAULT_CFG: Dict[str, object] = {
    "game_folder": "",
    "countdown_time": 40,
    "pairing_id": "",
    "device_id": "",
    "device_secret": "",
    "desktop_id": "",        # zostanie wygenerowany automatycznie
    "run_in_background": False,
    "debug_mode": "true"
}

# -------------------------------------------------------
# ⚙️ Główne funkcje
# -------------------------------------------------------

def ensure_desktop_id(cfg: dict) -> dict:
    """Generuje lokalny identyfikator komputera, jeśli nie istnieje."""
    if not cfg.get("desktop_id"):
        cfg["desktop_id"] = str(uuid.uuid4())
        save_config(cfg)
        logger.info(f"💻 Generated new desktop_id: {cfg['desktop_id']}")
    return cfg


def load_config() -> dict:
    """Wczytuje konfigurację z pliku lub tworzy nową z wartości domyślnych."""
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

    # Usuń przestarzałe pola
    for legacy_key in ["firebase_sa_path", "rtdb_url"]:
        if legacy_key in data:
            data.pop(legacy_key, None)
            logger.info(f"🧹 Removed legacy field '{legacy_key}' from config.")

    # Uzupełnij brakujące wartości domyślne
    cfg = {**DEFAULT_CFG, **data}

    # Wygeneruj desktop_id jeśli brakuje
    cfg = ensure_desktop_id(cfg)

    # Zapisz nowy plik jeśli jeszcze nie istnieje
    if not CONFIG_FILE.exists():
        save_config(cfg)

    logger.info(f"✅ Config loaded from {CONFIG_FILE}")
    return cfg


def save_config(cfg: dict):
    """Zapisuje konfigurację do pliku AppData (bezpiecznie, z fallbackiem)."""
    try:
        # Dopilnuj wszystkich kluczy
        for k, v in DEFAULT_CFG.items():
            cfg.setdefault(k, v)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 Config saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"❌ Failed to save config.json: {e}")

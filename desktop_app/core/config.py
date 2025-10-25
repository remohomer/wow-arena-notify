import json
import os
from pathlib import Path
from typing import Dict
from core.logger import logger

# -------------------------------------------------------
# 📂 Lokalizacja configa: C:\Users\<USER>\AppData\Local\WoWArenaNotify\
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

# 🔹 Ustaw zmienną środowiskową (dla innych modułów / narzędzi)
os.environ["WOW_ARENA_NOTIFY_CONFIG"] = str(CONFIG_FILE.resolve())

# -------------------------------------------------------
# ⚙️ Konfiguracja domyślna
# -------------------------------------------------------

DEFAULT_CFG: Dict[str, object] = {
    "game_folder": "",
    "countdown_time": 40,
    "pairing_id": "",
    "debug_mode": "true"
}

# -------------------------------------------------------
# ⚙️ Wczytywanie / zapisywanie konfiguracji
# -------------------------------------------------------

def load_config() -> dict:
    """Wczytuje konfigurację z pliku AppData lub tworzy domyślną."""
    data: Dict[str, object] = {}
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            logger.info("⚠ No config.json found — using defaults.")
    except Exception as e:
        logger.warning(f"⚠ Could not read config.json: {e}")

    # Usuń stare pola (legacy)
    for legacy in ["firebase_sa_path", "rtdb_url"]:
        if legacy in data:
            data.pop(legacy, None)
            logger.info(f"🧹 Removed legacy field '{legacy}' from config.")

    # Uzupełnij brakujące klucze i zapisz
    cfg = {**DEFAULT_CFG, **data}
    # Zapisz tylko, jeśli plik nie istnieje (pierwsze uruchomienie)
    if not CONFIG_FILE.exists():
        save_config(cfg)
    logger.info(f"✅ Config loaded from {CONFIG_FILE}")
    return cfg


def save_config(cfg: dict):
    """Zapisuje konfigurację do pliku AppData."""
    try:
        # Uzupełnij brakujące klucze na wypadek starszych wersji
        for k, v in DEFAULT_CFG.items():
            cfg.setdefault(k, v)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 Config saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"❌ Failed to save config.json: {e}")

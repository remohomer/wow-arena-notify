import json
import os
import shutil
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
FIREBASE_FILE: Path = APP_DIR / "firebase-service-account.json"

# 🔹 Ustaw zmienną środowiskową (dla innych modułów / narzędzi)
os.environ["WOW_ARENA_NOTIFY_CONFIG"] = str(CONFIG_FILE.resolve())

# -------------------------------------------------------
# 🔍 Wyszukiwanie i kopiowanie pliku Firebase
# -------------------------------------------------------

def ensure_firebase_key() -> str:
    """Zapewnia, że plik firebase-service-account.json istnieje w AppData."""
    if FIREBASE_FILE.exists():
        return str(FIREBASE_FILE.resolve())

    search_paths = [
        Path("core/push/wow-arena-notify-firebase-adminsdk-fbsvc-6768698cac.json"),
        Path("core/push/firebase-service-account.json"),
        Path("core/firebase-service-account.json"),
        Path("core/wow-arena-notify-firebase-adminsdk-fbsvc-6768698cac.json"),
    ]

    for path in search_paths:
        if path.exists():
            try:
                shutil.copy(path, FIREBASE_FILE)
                logger.info(f"📁 Copied Firebase key from {path} → {FIREBASE_FILE}")
                return str(FIREBASE_FILE.resolve())
            except Exception as e:
                logger.warning(f"⚠ Failed to copy Firebase key: {e}")
                # użyj ścieżki źródłowej jako fallback
                return str(path.resolve())

    logger.warning("⚠ Firebase key not found in any known location.")
    # mimo wszystko zwraca ścieżkę docelową (umożliwia późniejsze podmiany)
    return str(FIREBASE_FILE.resolve())


# -------------------------------------------------------
# ⚙️ Konfiguracja domyślna
# -------------------------------------------------------

DEFAULT_CFG: Dict[str, object] = {
    "game_folder": "",
    "countdown_time": 40,
    "firebase_sa_path": str(FIREBASE_FILE.resolve()),
    "fcm_token": "",
    "rtdb_url": "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/",
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

    firebase_path = ensure_firebase_key()

    # Uzupełnij brakujące klucze i zaktualizuj ścieżkę Firebase
    cfg = {**DEFAULT_CFG, **data}
    cfg["firebase_sa_path"] = firebase_path

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

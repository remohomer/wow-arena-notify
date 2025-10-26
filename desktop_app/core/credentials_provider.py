# core/credentials_provider.py — v2 (2025-10-26)
# ✅ Centralized, secure configuration provider
# ✅ No Firebase service JSON dependency
# ✅ Loads all from .env or system environment
# ✅ Shared by all desktop modules

import os
from dotenv import load_dotenv
from core.logger import logger


class CredentialsProvider:
    """
    Central configuration & credential access for WoW Arena Notify (Desktop).
    -------------------------------------------------------------------------
    Loads values from `.env` or system environment:
      - WOW_SECRET (shared HMAC secret)
      - RTDB_URL   (Firebase Realtime Database URL)
      - PAIR_DEVICE_URL (Cloud Function endpoint for pairing)
      - PUSH_ARENA_URL  (Cloud Function endpoint for event push)
    """

    DEFAULT_RTDB_URL = "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"
    DEFAULT_PAIR_DEVICE_URL = "https://us-central1-wow-arena-notify.cloudfunctions.net/pairDevice"
    DEFAULT_PUSH_ARENA_URL = "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena"

    def __init__(self):
        # Load .env if available
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"🌍 Loaded environment variables from {env_path}")
        else:
            logger.warning("⚠️ .env file not found; relying on system environment variables.")

        # Core values
        self.WOW_SECRET = os.getenv("WOW_SECRET", "").strip()
        self.RTDB_URL = os.getenv("RTDB_URL", self.DEFAULT_RTDB_URL).strip()
        self.PAIR_DEVICE_URL = os.getenv("PAIR_DEVICE_URL", self.DEFAULT_PAIR_DEVICE_URL).strip()
        self.PUSH_ARENA_URL = os.getenv("PUSH_ARENA_URL", self.DEFAULT_PUSH_ARENA_URL).strip()

        # Validation
        if not self.WOW_SECRET:
            logger.error("❌ Missing WOW_SECRET — HMAC verification may fail.")
        if not self.RTDB_URL:
            logger.error("❌ Missing RTDB_URL — RTDB connection may fail.")

    # --- Accessors ---
    def get_secret(self) -> str:
        """Return the sanitized WOW_SECRET (no quotes or newlines)."""
        clean = self.WOW_SECRET.strip().strip('"').strip("'").replace("\r", "")
        if clean != self.WOW_SECRET:
            logger.info("🔑 WOW_SECRET normalized (quotes/whitespace removed).")
        return clean

    def get_rtdb_url(self) -> str:
        """Return Firebase RTDB URL."""
        return self.RTDB_URL

    def get_pair_device_url(self) -> str:
        """Return Cloud Function URL for device pairing."""
        return self.PAIR_DEVICE_URL

    def get_push_arena_url(self) -> str:
        """Return Cloud Function URL for event pushes."""
        return self.PUSH_ARENA_URL

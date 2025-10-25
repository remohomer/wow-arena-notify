# core/credentials_provider.py
import os
import json
from dotenv import load_dotenv
from core.logger import logger


class CredentialsProvider:
    """
    Provides access to environment-level configuration and credentials
    used by WoW Arena Notify Desktop App.

    Loads configuration from `.env` file or system environment:
      - WOW_SECRET (shared HMAC secret)
      - FIREBASE_SERVICE_ACCOUNT (path or inline JSON)
      - RTDB_URL (Firebase Realtime Database URL)
    """

    def __init__(self):
        # Locate and load .env file
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"🔐 Loaded environment variables from {env_path}")
        else:
            logger.warning("⚠️ .env file not found; expecting env vars in system environment.")

        # Load key environment variables
        self.WOW_SECRET = os.getenv("WOW_SECRET")
        self.RTDB_URL = os.getenv(
            "RTDB_URL",
            "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/",
        )
        self.SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT")

        # Validate presence
        if not self.WOW_SECRET:
            logger.error("❌ Missing WOW_SECRET in environment.")
        if not self.RTDB_URL:
            logger.error("❌ Missing RTDB_URL in environment.")

    # --- HMAC Secret ---
    def get_env_secret(self) -> str:
        """
        Returns the global WOW_SECRET used for HMAC signing.
        """
        return self.WOW_SECRET

    # --- Firebase credentials ---
    def get_credentials(self) -> dict:
        """
        Returns Firebase Admin SDK credentials as dict.

        If FIREBASE_SERVICE_ACCOUNT points to a JSON file → loads it.
        If FIREBASE_SERVICE_ACCOUNT contains JSON text → parses it directly.
        """
        if not self.SERVICE_ACCOUNT_PATH:
            logger.warning("⚠️ FIREBASE_SERVICE_ACCOUNT not defined; using empty creds.")
            return {}

        try:
            if os.path.exists(self.SERVICE_ACCOUNT_PATH):
                with open(self.SERVICE_ACCOUNT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("✅ Loaded Firebase credentials from file.")
                    return data
            else:
                data = json.loads(self.SERVICE_ACCOUNT_PATH)
                logger.info("✅ Loaded Firebase credentials from inline JSON.")
                return data
        except Exception as e:
            logger.error(f"❌ Failed to load Firebase credentials: {e}")
            return {}

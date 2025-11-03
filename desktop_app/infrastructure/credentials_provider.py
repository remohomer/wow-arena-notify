# -*- coding: utf-8 -*-
# Centralized env loader (no secrets in logs)
import os
from dotenv import load_dotenv
from infrastructure.logger import logger

class CredentialsProvider:
    DEFAULT_RTDB_URL = "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"
    DEFAULT_PAIR_DEVICE_URL = "https://us-central1-wow-arena-notify.cloudfunctions.net/pairDevice"
    DEFAULT_PUSH_ARENA_URL = "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena"

    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.dev(f"Loaded .env from {env_path}")

        self.WOW_SECRET = os.getenv("WOW_SECRET", "").strip()
        self.RTDB_URL = os.getenv("RTDB_URL", self.DEFAULT_RTDB_URL).strip()
        self.PAIR_DEVICE_URL = os.getenv("PAIR_DEVICE_URL", self.DEFAULT_PAIR_DEVICE_URL).strip()
        self.PUSH_ARENA_URL = os.getenv("PUSH_ARENA_URL", self.DEFAULT_PUSH_ARENA_URL).strip()

        if not self.WOW_SECRET:
            logger.user("Missing WOW_SECRET (push may fail).")
        if not self.RTDB_URL:
            logger.user("Missing RTDB_URL (RTDB may be unavailable).")

    def get_secret(self) -> str:
        # sanitize (strip quotes/newlines)
        clean = self.WOW_SECRET.strip().strip('"').strip("'").replace("\r", "")
        return clean

    def get_rtdb_url(self) -> str:
        return self.RTDB_URL

    def get_pair_device_url(self) -> str:
        return self.PAIR_DEVICE_URL

    def get_push_arena_url(self) -> str:
        return self.PUSH_ARENA_URL

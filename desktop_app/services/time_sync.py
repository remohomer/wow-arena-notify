# file: desktop_app/services/time_sync.py
# ✅ Uses CredentialsProvider.get_rtdb_url()
# ✅ Graceful fallback to local clock
# ✅ Clean logging

import time
import requests
from infrastructure.logger import logger
from infrastructure.credentials_provider import CredentialsProvider

_CACHE_TTL = 300  # seconds
_last_offset = 0
_last_sync_time = 0


def get_firebase_server_time(cfg: dict = None) -> int:
    """
    Return current Firebase server time in ms.
    Falls back to local clock if RTDB unavailable.
    """
    try:
        provider = CredentialsProvider()
        rtdb_url = provider.get_rtdb_url()
        if not rtdb_url:
            logger.warning("⚠️ No RTDB URL configured → using local clock.")
            return int(time.time() * 1000)

        # Try lightweight REST time sync
        ts_url = f"{rtdb_url}/.info/serverTimeOffset.json"
        resp = requests.get(ts_url, timeout=5)
        if resp.ok:
            offset_ms = int(resp.text)
            server_time = int(time.time() * 1000) + offset_ms
            logger.info(f"🕒 Firebase REST offset: {offset_ms} ms → serverNow ≈ {server_time}")
            return server_time
        else:
            logger.warning(f"⚠️ Could not fetch server offset (HTTP {resp.status_code}) → fallback to local.")
            return int(time.time() * 1000)

    except Exception as e:
        logger.warning(f"⚠️ get_firebase_server_time(): using local clock (reason: {e})")
        return int(time.time() * 1000)


def get_server_offset(cfg: dict = None) -> int:
    """
    Return cached or live server offset (ms).
    Uses REST-based .info/serverTimeOffset, no Admin SDK.
    """
    global _last_offset, _last_sync_time

    now = time.time()
    if now - _last_sync_time < _CACHE_TTL:
        return _last_offset

    try:
        provider = CredentialsProvider()
        rtdb_url = provider.get_rtdb_url()
        if not rtdb_url:
            logger.warning("⚠️ No RTDB URL set → offset = 0 ms")
            return 0

        ts_url = f"{rtdb_url}/.info/serverTimeOffset.json"
        resp = requests.get(ts_url, timeout=5)
        if resp.ok:
            _last_offset = int(resp.text)
            _last_sync_time = now
            logger.info(f"🧭 get_server_offset() → {_last_offset} ms")
            return _last_offset
        else:
            logger.warning(f"⚠️ get_server_offset(): HTTP {resp.status_code}, fallback 0")
            return 0

    except Exception as e:
        logger.warning(f"⚠️ get_server_offset(): fallback 0 (reason: {e})")
        return 0

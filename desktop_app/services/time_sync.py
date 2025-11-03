# -*- coding: utf-8 -*-
# Firebase server time via .info/serverTimeOffset, cached
import time
import requests
from infrastructure.logger import logger
from infrastructure.credentials_provider import CredentialsProvider

_CACHE_TTL = 300
_last_offset = 0
_last_sync_time = 0

def get_firebase_server_time(cfg: dict = None) -> int:
    try:
        provider = CredentialsProvider()
        rtdb_url = provider.get_rtdb_url()
        if not rtdb_url:
            return int(time.time() * 1000)

        ts_url = f"{rtdb_url}/.info/serverTimeOffset.json"
        resp = requests.get(ts_url, timeout=5)
        if resp.ok:
            offset_ms = int(resp.text)
            return int(time.time() * 1000) + offset_ms
        return int(time.time() * 1000)
    except Exception:
        return int(time.time() * 1000)

def get_server_offset(cfg: dict = None) -> int:
    global _last_offset, _last_sync_time
    now = time.time()
    if now - _last_sync_time < _CACHE_TTL:
        return _last_offset
    try:
        provider = CredentialsProvider()
        rtdb_url = provider.get_rtdb_url()
        if not rtdb_url:
            return 0
        ts_url = f"{rtdb_url}/.info/serverTimeOffset.json"
        resp = requests.get(ts_url, timeout=5)
        if resp.ok:
            _last_offset = int(resp.text)
            _last_sync_time = now
            return _last_offset
        return 0
    except Exception:
        return 0

# -*- coding: utf-8 -*-
# RTDB REST write (fallback / complement to pushArena)
import time
import requests
from typing import Optional
from infrastructure.logger import logger
from services.time_sync import get_firebase_server_time
from infrastructure.credentials_provider import CredentialsProvider

def _safe_token_for_path(token: str) -> str:
    return (token or "").replace(":", "_")

def send_arena_event(
    event_type: str,
    duration_sec: int,
    pairing_id: str,
    event_id: str,
    cfg: Optional[dict] = None,
) -> dict | None:
    creds = CredentialsProvider()
    rtdb_url = creds.get_rtdb_url()
    if not rtdb_url:
        logger.user("RTDB URL not configured.")
        return None
    if not pairing_id:
        logger.dev("send_arena_event called with empty pairing_id")
        return None

    try:
        safe_token = _safe_token_for_path(pairing_id)
        path_url = f"{rtdb_url.rstrip('/')}/arena_events/{safe_token}/current.json"

        server_now_ms = get_firebase_server_time(cfg=cfg)
        adjusted_seconds = max(int(duration_sec), 0)
        ends_at_ms = server_now_ms + adjusted_seconds * 1000

        payload = {
            "schema": "1",
            "type": event_type,
            "eventId": event_id,
            "endsAt": ends_at_ms,
            "timestamp": server_now_ms,
            "updatedAt": int(time.time() * 1000),
        }

        logger.dev(f"RTDB PUT {event_type} endsAt={ends_at_ms} url={path_url}")
        resp = requests.put(path_url, json=payload, timeout=5)
        if resp.ok:
            logger.dev("RTDB write OK")
            return payload

        logger.user(f"RTDB write rejected ({resp.status_code})")
        logger.dev(resp.text[:200])
        return None

    except Exception as e:
        logger.user("RTDB write error")
        logger.dev(f"RTDB exception: {e}")
        return None

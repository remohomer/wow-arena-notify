# core/push/arena_realtime.py — v3 (2025-10-26)
# ✅ No service account required
# ✅ Uses CredentialsProvider for RTDB URL
# ✅ Pure HTTPS (REST) write to Firebase
# ✅ Fully compatible with old function signature

import time
import requests
from typing import Optional
from core.logger import logger
from core.time_sync import get_firebase_server_time
from core.credentials_provider import CredentialsProvider


def _safe_token_for_path(token: str) -> str:
    """Firebase RTDB paths cannot contain ':', so replace with '_'."""
    return (token or "").replace(":", "_")


def send_arena_event(
    event_type: str,
    duration_sec: int,
    pairing_id: str,
    event_id: str,
    cfg: Optional[dict] = None,
) -> dict | None:
    """
    Publish an arena event to Firebase Realtime Database using REST API.
    Uses Firebase server time (from .info/serverTimeOffset).
    Returns the payload on success.
    """

    creds = CredentialsProvider()
    rtdb_url = creds.get_rtdb_url()

    if not rtdb_url:
        logger.error("❌ No RTDB_URL available in environment or defaults.")
        return None
    if not pairing_id:
        logger.warning("⚠ Empty pairing_id passed to send_arena_event().")
        return None

    try:
        safe_token = _safe_token_for_path(pairing_id)
        base_url = rtdb_url.rstrip("/")
        path_url = f"{base_url}/arena_events/{safe_token}/current.json"

        # Calculate server-aligned timestamps
        server_now_ms = get_firebase_server_time(cfg=cfg)
        adjusted_seconds = max(int(duration_sec), 0)
        ends_at_ms = server_now_ms + adjusted_seconds * 1000

        payload = {
            "schema": "1",
            "type": event_type,
            "eventId": event_id,
            "endsAt": ends_at_ms,
            "timestamp": server_now_ms,  # write time in server clock
            "updatedAt": int(time.time() * 1000),  # 🔹 NEW — ensures onDataChange always fires
        }
        logger.info(
            f"📨 RTDB REST → {event_type} (id={event_id}) "
            f"@ /arena_events/{safe_token}/current (serverNow={server_now_ms}, updatedAt={payload['updatedAt']})"
        )

        resp = requests.put(path_url, json=payload, timeout=5)
        if resp.ok:
            logger.info(
                f"📨 RTDB REST → {event_type} (id={event_id}) "
                f"@ /arena_events/{safe_token}/current (serverNow={server_now_ms})"
            )
            return payload
        else:
            logger.error(
                f"❌ RTDB REST write failed ({resp.status_code}): {resp.text[:120]}"
            )
            return None

    except Exception as e:
        logger.error(f"❌ RTDB write failed ({event_type}, eventId={event_id}): {e}")
        return None

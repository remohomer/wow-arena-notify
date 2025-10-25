"""
Realtime Database event publisher (pure, no config I/O inside).

Writes (mirror/fallback) to:
  /arena_events/<safe_token>/current
Payload is aligned to Firebase server time.
"""

from __future__ import annotations
import time
from typing import Optional
from core.logger import logger
from core.time_sync import get_firebase_server_time

try:
    import firebase_admin
    from firebase_admin import credentials, db
except Exception as e:
    firebase_admin = None
    credentials = None
    db = None
    logger.error(f"❌ Firebase Admin SDK not available for RTDB: {e}")

_rtdb_app = None


def _ensure_rtdb(cfg: dict) -> Optional[object]:
    """Initialize Firebase Admin app with RTDB once per process."""
    global _rtdb_app
    if _rtdb_app is not None:
        return _rtdb_app

    if firebase_admin is None:
        logger.error("❌ Firebase Admin SDK is not installed (RTDB).")
        return None

    sa_path = cfg.get("firebase_sa_path", "")
    rtdb_url = cfg.get("rtdb_url", "")
    if not sa_path or not rtdb_url:
        logger.error("❌ Missing 'firebase_sa_path' or 'rtdb_url' in config.")
        return None

    try:
        cred = credentials.Certificate(sa_path)
        _rtdb_app = firebase_admin.initialize_app(
            cred, {"databaseURL": rtdb_url}, name="rtdb"
        )
        logger.info(f"✅ Firebase RTDB initialized ({rtdb_url})")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase RTDB: {e}")
        _rtdb_app = None

    return _rtdb_app


def _safe_token_for_path(token: str) -> str:
    """Firebase RTDB paths cannot contain ':', so replace with '_'."""
    return (token or "").replace(":", "_")


def send_arena_event(
    event_type: str,
    duration_sec: int,
    user_token: str,
    event_id: str,
    cfg: dict,
) -> dict | None:
    """
    Publish an arena event to Firebase Realtime Database using Firebase server time.
    Returns the payload on success.
    """
    app = _ensure_rtdb(cfg)
    if app is None:
        return None

    if not user_token:
        logger.warning("⚠ Empty user_token passed to send_arena_event().")
        return None

    try:
        safe_token = _safe_token_for_path(user_token)
        path = f"arena_events/{safe_token}/current"
        ref = db.reference(path, app=app)

        server_now_ms = get_firebase_server_time(cfg=cfg)
        adjusted_seconds = max(int(duration_sec), 0)
        ends_at_ms = server_now_ms + adjusted_seconds * 1000

        payload = {
            "schema": "1",
            "type": event_type,
            "eventId": event_id,
            "endsAt": ends_at_ms,
            "timestamp": server_now_ms,  # write time in server clock
        }

        ref.set(payload)
        logger.info(f"📨 RTDB → {event_type} (id={event_id}) at /{path} (serverNow={server_now_ms})")
        return payload

    except Exception as e:
        logger.error(f"❌ RTDB write failed ({event_type}, eventId={event_id}): {e}")
        return None
"""
Firebase Cloud Messaging (FCM) sender for WoW Arena Notify.
- Data-only messages
- High priority + TTL (reliable delivery in Doze)
- Server-time aligned endsAt (Firebase clock)
- Includes desktopOffset for Android time-diff diagnostics
- Simple retry with backoff
"""

import time
import uuid
from typing import Optional

from core.logger import logger
from core.time_sync import get_firebase_server_time, get_server_offset

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception as e:
    firebase_admin = None
    credentials = None
    messaging = None
    logger.error(f"❌ Firebase Admin SDK not available: {e}")

_firebase_app = None


# -------------------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------------------
def _ensure_firebase_app(cfg: dict):
    """Initialize Firebase Admin if not already initialized."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    if firebase_admin is None:
        logger.error("❌ Firebase Admin SDK is not installed.")
        return None

    sa_path = cfg.get("firebase_sa_path", "")
    if not sa_path:
        logger.error("❌ Missing firebase_sa_path in config.")
        return None

    try:
        cred = credentials.Certificate(sa_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin initialized (FCM).")
        return _firebase_app
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase Admin: {e}")
        return None


# -------------------------------------------------------------------------
# RETRY WRAPPER
# -------------------------------------------------------------------------
def _send_with_retry(message, app, attempts: int = 3, base_sleep: float = 1.0) -> Optional[str]:
    """Send FCM with simple exponential backoff. Returns message_id or None."""
    for i in range(1, attempts + 1):
        try:
            msg_id = messaging.send(message, app=app)
            return msg_id
        except Exception as e:
            err = str(e)
            logger.warning(f"⚠️ FCM send attempt {i}/{attempts} failed: {err}")
            # common permanent errors → don't retry further
            if "registration-token-not-registered" in err or "InvalidArgument" in err:
                break
            time.sleep(base_sleep * (2 ** (i - 1)))
    return None


# -------------------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------------------
def send_fcm_message(
    event_type: str,
    seconds: int,
    event_id: str = None,
    user_token: str = None,
    cfg: dict = None,
) -> bool:
    """
    Sends a direct FCM push (data-only) to Android.
    Expected by ArenaMessagingService in the mobile app.
    Includes desktopOffset to compare with Android offset (for sync accuracy).
    """
    if not cfg:
        logger.error("❌ send_fcm_message() called without config (cfg).")
        return False

    app = _ensure_firebase_app(cfg)
    if app is None:
        return False

    user_token = (user_token or cfg.get("fcm_token", "")).strip()
    if not user_token:
        logger.error("❌ Missing FCM token in config.")
        return False

    event_id = event_id or str(uuid.uuid4())

    # ✅ Get true Firebase server time and local offset difference
    server_time_ms = get_firebase_server_time(cfg=cfg)
    desktop_offset_ms = get_server_offset(cfg)
    local_now = int(time.time() * 1000)
    local_server_now = local_now + desktop_offset_ms

    adjusted_seconds = max(int(seconds), 0)
    ends_at_ms = server_time_ms + adjusted_seconds * 1000

    # 🧮 Prepare payload for Android app
    payload = {
        "schema": "1",
        "type": event_type,
        "eventId": event_id,
        "endsAt": str(ends_at_ms),
        "duration": str(adjusted_seconds),
        "sentAtMs": str(server_time_ms),
        "desktopOffset": str(desktop_offset_ms),  # 🔥 Added for sync diagnostics
    }

    # 🕒 Detailed debug output
    logger.info("────────────────────────────────────────────────────────────")
    logger.info(f"🔎 FCM DEBUG DIAGNOSTICS ({event_type.upper()}):")
    logger.info(f"  🖥️ Desktop offset: {desktop_offset_ms} ms")
    logger.info(f"  🕒 Local now: {local_now}")
    logger.info(f"  🌍 Firebase server now: {server_time_ms}")
    logger.info(f"  💻 Local+offset (est. server): {local_server_now}")
    logger.info(f"  🎯 endsAt (server-based): {ends_at_ms}")
    logger.info("────────────────────────────────────────────────────────────")
    logger.info(
        f"🕒 FCM payload → type={event_type}, dur={adjusted_seconds}s, "
        f"endsAt={ends_at_ms} (serverNow={server_time_ms}, offset={desktop_offset_ms})"
    )

    try:
        # 🚀 High-priority, short TTL to beat Doze
        android_cfg = messaging.AndroidConfig(
            priority="high",
            ttl=max(20, adjusted_seconds + 5),
            direct_boot_ok=True,
        )

        message = messaging.Message(token=user_token, data=payload, android=android_cfg)
        msg_id = _send_with_retry(message, app=app, attempts=3, base_sleep=1.0)

        if msg_id:
            logger.info(f"📨 FCM → {event_type} sent (eventId={event_id}) → msgId={msg_id}")
            return True

        logger.error(f"❌ FCM send failed after retries ({event_type}, eventId={event_id})")
        return False

    except Exception as e:
        logger.error(f"❌ FCM unexpected error ({event_type}, eventId={event_id}): {e}")
        return False

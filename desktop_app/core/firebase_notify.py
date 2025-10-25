"""
Firebase Cloud Messaging (FCM) sender for WoW Arena Notify.
Securely communicates with Cloud Function `pushArena`.

✅ Features:
- Sends event payloads (arena_pop, arena_stop) via HTTPS
- Authenticated using HMAC-SHA256 with WOW_SECRET
- Includes desktopOffset and server-aligned endsAt
- Backward-compatible with old GUI (user_token arg kept)
"""

import time
import uuid
import hmac
import hashlib
import json
import requests
from typing import Optional
from core.logger import logger
from core.time_sync import get_firebase_server_time, get_server_offset
from core.credentials_provider import CredentialsProvider

# Remote push endpoint (Firebase Cloud Function)
FIREBASE_PUSH_URL = "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena"


# -------------------------------------------------------------------------
# HMAC SIGNATURE
# -------------------------------------------------------------------------
def _generate_signature(secret: str, message: str) -> str:
    """Generate HMAC-SHA256 signature for canonical JSON payload."""
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


# -------------------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------------------
def send_fcm_message(
    event_type: str,
    seconds: int,
    event_id: Optional[str] = None,
    user_token: Optional[str] = None,  # legacy param for GUI compatibility
    pairing_id: str = "test_desktop",
    cfg: Optional[dict] = None,
) -> bool:
    """
    Sends an event (arena_pop, arena_stop) to Cloud Function `pushArena`
    using HMAC authentication and consistent JSON serialization.
    """

    if not cfg:
        logger.error("❌ send_fcm_message() called without config (cfg).")
        return False

    # --- Load shared secret ---
    provider = CredentialsProvider()
    secret = provider.get_env_secret()

    if not secret:
        logger.error("❌ Missing WOW_SECRET in environment.")
        return False

    logger.info(f"🔐 WOW_SECRET length: {len(secret)} chars")

    # --- Generate event metadata ---
    event_id = event_id or str(uuid.uuid4())
    server_time_ms = get_firebase_server_time(cfg=cfg)
    desktop_offset_ms = get_server_offset(cfg)
    local_now_ms = int(time.time() * 1000)
    adjusted_seconds = max(int(seconds), 0)
    ends_at_ms = server_time_ms + adjusted_seconds * 1000

    # --- Build canonical payload ---
    payload = {
        "schema": "1",
        "type": event_type,
        "event": event_type,
        "pairing_id": pairing_id,
        "eventId": event_id,
        "start_time": str(server_time_ms),
        "endsAt": str(ends_at_ms),
        "duration": str(adjusted_seconds),
        "sentAtMs": str(server_time_ms),
        "desktopOffset": str(desktop_offset_ms),
    }

    msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    signature = _generate_signature(secret, msg)
    msg_bytes = msg.encode("utf-8")

    # --- Diagnostic logs ---
    logger.info("────────────────────────────────────────────────────────────")
    logger.info(f"🔎 PUSH DIAGNOSTICS ({event_type.upper()}):")
    logger.info(f"  🕒 Server time: {server_time_ms}")
    logger.info(f"  🖥️ Desktop offset: {desktop_offset_ms} ms")
    logger.info(f"  🎯 endsAt: {ends_at_ms}")
    logger.info(f"  🔑 eventId: {event_id}")
    logger.info(f"  📦 Payload length: {len(msg_bytes)} bytes")
    logger.info("────────────────────────────────────────────────────────────")
    logger.info(f"🧾 Canonical JSON → {msg}")
    logger.info(f"🔐 FULL HMAC: {signature}")
    logger.info(f"🔐 HMAC (short): {signature[:16]}...{signature[-16:]}")
    logger.info(f"🧾 RAW JSON BYTES: {list(msg_bytes)[:100]}")
    logger.info(f"🧾 RAW JSON LAST: {list(msg_bytes)[-20:]}")
    logger.info(f"🧩 SECRET BYTES START: {list(secret.encode())[:20]}")

    # --- HTTPS POST ---
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": str(len(msg_bytes)),
        "X-Signature": signature,
    }

    try:
        logger.info(f"🌍 Sending pushArena → {FIREBASE_PUSH_URL}")
        response = requests.post(
            FIREBASE_PUSH_URL,
            headers=headers,
            data=msg_bytes,
            timeout=10,
        )

        if response.status_code == 200:
            logger.info(f"✅ pushArena OK: event={event_type}, id={event_id}")
            return True
        else:
            logger.error(f"❌ pushArena rejected ({response.status_code}): {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ pushArena HTTPS error: {str(e)}")
        return False

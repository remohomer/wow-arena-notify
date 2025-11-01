# file: desktop_app/services/firebase_notify.py
# ✅ Dynamic pushArena URL (from CredentialsProvider)
# ✅ Secure HMAC-SHA256 signature
# ✅ Full diagnostics and clean fallback
# ✅ Works without local Firebase credentials file

import time
import uuid
import hmac
import hashlib
import json
import requests
from typing import Optional
from infrastructure.logger import logger
from services.time_sync import get_firebase_server_time, get_server_offset
from infrastructure.credentials_provider import CredentialsProvider


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

    # --- Load shared secret and push URL ---
    creds = CredentialsProvider()
    secret = creds.get_secret()
    push_url = creds.get_push_arena_url()

    if not secret:
        logger.error("❌ Missing WOW_SECRET in environment.")
        return False
    if not push_url:
        logger.error("❌ Missing PUSH_ARENA_URL in environment or defaults.")
        return False

    # --- Generate event metadata ---
    event_id = event_id or str(uuid.uuid4())
    server_time_ms = get_firebase_server_time(cfg=cfg)
    desktop_offset_ms = get_server_offset(cfg)
    adjusted_seconds = max(int(seconds), 0)
    ends_at_ms = server_time_ms + adjusted_seconds * 1000

    # --- Build canonical payload ---
    payload = {
        "schema": "1",
        "type": str(event_type),
        "event": str(event_type),
        "pairing_id": str(pairing_id),
        "eventId": str(event_id),
        "start_time": str(server_time_ms),
        "endsAt": str(ends_at_ms),
        "duration": str(adjusted_seconds),
        "sentAtMs": str(server_time_ms),
        "desktopOffset": str(desktop_offset_ms),
    }

    msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    signature = _generate_signature(secret, msg)
    msg_bytes = msg.encode("utf-8")

    # --- Diagnostics ---
    secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:16]
    logger.info("────────────────────────────────────────────────────────────")
    logger.info(f"🔎 PUSH DIAGNOSTICS ({event_type.upper()}):")
    logger.info(f"  🌐 pushArena URL: {push_url}")
    logger.info(f"  🔑 CLIENT SECRET HASH: {secret_hash}")
    logger.info(f"  🕒 Server time: {server_time_ms}")
    logger.info(f"  🖥️ Desktop offset: {desktop_offset_ms} ms")
    logger.info(f"  🎯 endsAt: {ends_at_ms}")
    logger.info(f"  🔑 eventId: {event_id}")
    logger.info(f"  📦 Payload length: {len(msg_bytes)} bytes")
    logger.info("────────────────────────────────────────────────────────────")
    logger.info(f"🧾 Canonical JSON → {msg}")
    logger.info(f"🔐 FULL HMAC: {signature}")
    logger.info(f"🔐 HMAC (short): {signature[:16]}...{signature[-16:]}")

    # --- HTTPS POST ---
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Signature": signature,
    }

    try:
        logger.info(f"🌍 Sending pushArena → {push_url}")
        response = requests.post(
            push_url,
            data=msg_bytes,
            headers=headers,
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

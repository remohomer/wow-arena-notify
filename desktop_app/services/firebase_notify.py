# -*- coding: utf-8 -*-
"""
Clean pushArena sender with:
 - minimal user logs
 - optional developer diagnostics
 - full payload only on error
"""

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
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


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

    Minimal logs for normal operation.
    Extra diagnostics only in debug_mode.
    """

    if not cfg:
        logger.error("❌ send_fcm_message() missing config.")
        return False

    # --- Load shared secret and push URL ---
    creds = CredentialsProvider()
    secret = creds.get_secret()
    push_url = creds.get_push_arena_url()

    if not secret:
        logger.error("❌ Environment: WOW_SECRET missing.")
        return False
    if not push_url:
        logger.error("❌ PUSH_ARENA_URL missing.")
        return False

    # --- Metadata ---
    event_id = event_id or str(uuid.uuid4())
    server_time_ms = get_firebase_server_time(cfg=cfg)
    desktop_offset_ms = get_server_offset(cfg)
    adjusted_seconds = max(int(seconds), 0)
    ends_at_ms = server_time_ms + adjusted_seconds * 1000

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

    # Canonical JSON
    msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    signature = _generate_signature(secret, msg)
    msg_bytes = msg.encode("utf-8")

    secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]

    logger.dev(f"pushArena event_type={event_type} adjusted_seconds={adjusted_seconds}s")
    logger.dev(f"id={event_id} url={push_url} len={len(msg_bytes)} off={desktop_offset_ms} secret={secret_hash}")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Signature": signature,
    }

    try:
        response = requests.post(
            push_url,
            data=msg_bytes,
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            logger.dev("POST OK (200)")
            return True

        # ------------------ ERROR DETAIL ------------------
        logger.error(f"❌ pushArena rejected ({response.status_code})")
        logger.dev(f"resp: {response.text}")

        # Full payload only when error:
        logger.dev(f"payload: {msg}")
        logger.dev(f"hmac: {signature}")

        return False

    except Exception as e:
        logger.error(f"❌ pushArena HTTPS error: {str(e)}")

        logger.dev(f"payload: {msg}")
        logger.dev(f"hmac: {signature}")

        return False

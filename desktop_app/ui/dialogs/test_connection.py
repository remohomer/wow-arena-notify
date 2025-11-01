# file: desktop_app/ui/dialogs/test_connection.py
# ✅ Uses CredentialsProvider.get_push_arena_url()
# ✅ Canonical HMAC signing (same as firebase_notify)
# ✅ Improved logging & error clarity

import json
import hmac
import hashlib
import uuid
import requests
from PySide6.QtWidgets import QMessageBox
from infrastructure.config import load_config
from infrastructure.logger import logger
from infrastructure.credentials_provider import CredentialsProvider


def run_test(parent=None):
    """
    Sends a lightweight test event via Cloud Function (pushArena).
    Uses WOW_SECRET (HMAC authentication) and pairing_id (no FCM token needed).
    """

    logger.info("🚦 Test connection clicked.")

    try:
        # --- Load config & pairing ID ---
        cfg = load_config()
        pairing_id = cfg.get("pairing_id", "").strip()

        if not pairing_id:
            QMessageBox.warning(
                parent,
                "Test Connection",
                "⚠ No pairing ID found.\nPlease pair your phone first (Pair device).",
            )
            return

        # --- Load environment & credentials ---
        provider = CredentialsProvider()
        secret = provider.get_secret()
        push_url = provider.get_push_arena_url()

        if not secret:
            QMessageBox.warning(
                parent,
                "Missing Secret",
                "⚠ No WOW_SECRET found in environment.\nCloud push cannot be authenticated.",
            )
            return

        # --- Build minimal payload ---
        event_id = str(uuid.uuid4())
        payload = {
            "schema": "1",
            "event": "test_connection",
            "type": "test_connection",
            "pairing_id": pairing_id,
            "eventId": event_id,
            "duration": "0",
            "start_time": "0",
            "sentAtMs": "0",
        }

        # --- Canonical JSON & HMAC ---
        canonical_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
        signature = hmac.new(secret.encode("utf-8"), canonical_json.encode("utf-8"), hashlib.sha256).hexdigest()
        secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:16]

        # --- Logging ---
        logger.info("──────────────────────────────────────────────")
        logger.info("🔎 TEST CONNECTION PAYLOAD:")
        logger.info(canonical_json)
        logger.info(f"🔑 CLIENT SECRET HASH: {secret_hash}")
        logger.info(f"🔐 HMAC: {signature[:16]}...{signature[-16:]}")
        logger.info(f"🌍 pushArena URL: {push_url}")
        logger.info("──────────────────────────────────────────────")

        # --- Send request ---
        response = requests.post(
            push_url,
            data=canonical_json.encode("utf-8"),  # surowy JSON w bajtach
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Signature": signature,
            },
            timeout=10,
        )

        # --- Response handling ---
        if response.status_code == 200:
            logger.info(f"✅ Test push sent successfully: {response.text}")
            QMessageBox.information(parent, "Test Connection", "✅ Test message sent successfully!")
        else:
            logger.error(f"❌ Test push failed ({response.status_code}): {response.text}")
            QMessageBox.warning(
                parent,
                "Test Connection",
                f"❌ Request failed ({response.status_code}):\n{response.text[:500]}",
            )

    except Exception as e:
        logger.exception("❌ Test connection failed.")
        QMessageBox.critical(parent, "Error", f"Failed to send test message:\n{e}")

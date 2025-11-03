# file: desktop_app/ui/dialogs/test_connection.py
# ✅ Sanitized logging
# ✅ No secrets, URLs, pairing_id leaks

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
    Sanitized logs (no secrets, URLs, pairing_id, HMAC fragments).
    """

    logger.info("🔌 Test connection triggered.")

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

        # --- Credentials ---
        provider = CredentialsProvider()
        secret = provider.get_secret()
        push_url = provider.get_push_arena_url()

        if not secret:
            QMessageBox.warning(
                parent,
                "Missing Secret",
                "⚠ No WOW_SECRET found in environment.",
            )
            return

        # --- Payload ---
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

        canonical_json = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
            sort_keys=True
        )

        signature = hmac.new(
            secret.encode("utf-8"),
            canonical_json.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # --- Sanitized Logging ---
        logger.info("📡 Sending test connection event...")
        logger.dev(f"🧾 Payload schema: {payload['schema']}")
        logger.dev(f"📨 Event ID: {event_id}")

        # --- Send request ---
        response = requests.post(
            push_url,
            data=canonical_json.encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Signature": signature,
            },
            timeout=10,
        )

        # --- Response handling ---
        if response.status_code == 200:
            logger.info("✅ Test push sent successfully.")
            QMessageBox.information(
                parent,
                "Test Connection",
                "✅ Test message sent successfully!",
            )
        else:
            logger.error(f"❌ Test push failed ({response.status_code})")
            QMessageBox.warning(
                parent,
                "Test Connection",
                f"❌ Request failed ({response.status_code})",
            )

    except Exception as e:
        logger.exception("❌ Test connection failed (sanitized).")
        QMessageBox.critical(parent, "Error", f"Failed to send test message:\n{e}")

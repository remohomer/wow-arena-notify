import json
import hmac
import hashlib
import os
import uuid
import requests
from PySide6.QtWidgets import QMessageBox
from core.config import load_config
from core.logger import logger
from core.credentials_provider import CredentialsProvider


def run_test(parent=None):
    """
    Sends a lightweight test event via Cloud Function (pushArena).
    Uses WOW_SECRET (HMAC authentication) and pairing_id (no FCM token needed).
    """
    try:
        cfg = load_config()
        pairing_id = cfg.get("pairing_id", "").strip()

        if not pairing_id:
            QMessageBox.warning(
                parent,
                "Test Connection",
                "⚠ No pairing ID found.\nPlease pair your phone first (Pair device).",
            )
            return

        # --- Load environment & secret ---
        provider = CredentialsProvider()
        secret = provider.get_env_secret()
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
            "pairing_id": pairing_id,
            "event": "test_connection",
            "type": "test_connection",
            "schema": "1",
            "duration": "0",
            "start_time": "0",
            "sentAtMs": "0",
            "eventId": event_id,
        }

        # --- Canonical JSON (sorted keys for deterministic HMAC) ---
        canonical_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
        signature = hmac.new(secret.encode("utf-8"), canonical_json.encode("utf-8"), hashlib.sha256).hexdigest()

        # --- Logging ---
        logger.info("──────────────────────────────────────────────")
        logger.info("🔎 TEST CONNECTION PAYLOAD:")
        logger.info(canonical_json)
        logger.info(f"🔐 WOW_SECRET length: {len(secret)}")
        logger.info(f"🔐 HMAC: {signature}")
        logger.info("──────────────────────────────────────────────")

        # --- Send request ---
        res = requests.post(
            "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena",
            data=canonical_json.encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Signature": signature,
            },
            timeout=10,
        )

        # --- Response handling ---
        if res.status_code == 200:
            logger.info(f"✅ Test push sent successfully: {res.text}")
            QMessageBox.information(parent, "Test Connection", "✅ Test message sent successfully!")
        else:
            logger.error(f"❌ Test push failed ({res.status_code}): {res.text}")
            QMessageBox.warning(parent, "Test Connection", f"❌ Request failed:\n{res.text}")

    except Exception as e:
        logger.exception("❌ Test connection failed.")
        QMessageBox.critical(parent, "Error", f"Failed to send test message:\n{e}")

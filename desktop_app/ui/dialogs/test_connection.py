import uuid
from PySide6.QtWidgets import QMessageBox
from core.config import load_config
from core.firebase_notify import send_fcm_message
from core.push.arena_realtime import _ensure_rtdb, send_arena_event
from core.logger import logger


def run_test(parent=None):
    """
    Sends a lightweight test event to verify pairing + FCM + RTDB.
    Uses the same production path (FCM data-only + RTDB).
    """
    try:
        cfg = load_config()
        user_token = cfg.get("fcm_token", "").strip()
        if not user_token:
            QMessageBox.warning(
                parent,
                "Test Connection",
                "No paired device token.\nPlease pair your phone first (Pair device).",
            )
            return

        event_id = str(uuid.uuid4())

        # RTDB init (named app to coexist with FCM)
        _ensure_rtdb(cfg)

        # Send both: FCM (Android service) + RTDB (Realtime listener)
        send_ok = send_fcm_message("test_connection", 0, event_id, user_token, cfg)
        payload = send_arena_event("test_connection", 0, user_token, event_id, cfg)

        if send_ok and payload:
            logger.info("✅ Test connection event sent successfully (FCM + RTDB).")
            QMessageBox.information(
                parent,
                "Test Connection",
                "✅ Test message sent.\n\nCheck your phone (toast/log) for confirmation.",
            )
        else:
            logger.warning(f"⚠ Test partially sent (FCM={send_ok}, RTDB={'OK' if payload else 'FAIL'}).")
            QMessageBox.warning(
                parent,
                "Test Connection",
                f"⚠ Test partially sent.\nFCM: {'OK' if send_ok else 'FAIL'}\nRTDB: {'OK' if payload else 'FAIL'}",
            )

    except Exception as e:
        logger.exception("❌ Test connection failed.")
        QMessageBox.critical(parent, "Error", f"Failed to send test message:\n{e}")

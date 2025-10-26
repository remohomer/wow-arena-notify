# ui/tabs/tester_tab.py — v3 (2025-10-26)
# ✅ No Firebase Admin SDK dependency
# ✅ Uses CredentialsProvider + REST time sync
# ✅ Fix: removed undefined user_token
# ✅ Full compatibility with refactored backend

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox, QMessageBox
from PySide6.QtCore import Qt, QTimer
from core.firebase_notify import send_fcm_message
from core.logger import logger
from core.time_sync import get_server_offset, get_firebase_server_time
from core.credentials_provider import CredentialsProvider
import time
import uuid
import threading


class TesterTab(QWidget):
    def __init__(self, parent=None, cfg=None):
        super().__init__(parent)
        self.parent = parent
        self.cfg = cfg or {}
        self.test_timer = None
        self.current_event_id = None
        self.init_ui()

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("⚙️ WoW Arena Notify — Tester")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ddd;")

        desc = QLabel(
            "This tool simulates Arena Queue events and checks synchronization between:\n"
            "💻 Desktop → 🔥 Firebase → 📱 Android\n\n"
            "Use Debug Test for precise timing diagnostics."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #aaa; font-size: 12px;")

        self.time_input = QSpinBox()
        self.time_input.setRange(5, 120)
        self.time_input.setValue(5)
        self.time_input.setSuffix(" s")
        self.time_input.setAlignment(Qt.AlignCenter)

        # --- Buttons ---
        remote_btn = QPushButton("🔁 Run Full Remote Test (auto stop)")
        remote_btn.setStyleSheet("background-color: #9C27B0; color: white; font-size: 14px; padding: 8px;")
        remote_btn.clicked.connect(self.run_full_test)

        debug_btn = QPushButton("🧠 Full Debug Timing Test (offset diff)")
        debug_btn.setStyleSheet("background-color: #607D8B; color: white; font-size: 14px; padding: 8px;")
        debug_btn.clicked.connect(self.run_debug_timing_test)

        clock_btn = QPushButton("🕒 Check Clock Sync (Firebase)")
        clock_btn.setStyleSheet("background-color: #2196F3; color: white; font-size: 14px; padding: 8px;")
        clock_btn.clicked.connect(self.check_clock_sync)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.time_input)
        layout.addWidget(remote_btn)
        layout.addWidget(debug_btn)
        layout.addWidget(clock_btn)

    # -------------------------------------------------------------------------
    # FULL REMOTE TEST
    # -------------------------------------------------------------------------
    def run_full_test(self):
        """Run full remote test cycle (arena_pop → arena_stop)."""
        seconds = self.time_input.value()
        self.current_event_id = str(uuid.uuid4())

        logger.info(f"🧪 Starting full remote test ({seconds}s) id={self.current_event_id}")
        QMessageBox.information(
            self, "Full Test", f"🚀 Remote test started!\nArena pop → auto stop after {seconds}s."
        )

        # Timing diagnostic
        offset_ms = get_server_offset(self.cfg)
        local_now = int(time.time() * 1000)
        server_now = local_now + offset_ms
        ends_at = server_now + seconds * 1000

        logger.info("────────────────────────────────────────────────────────────")
        logger.info("🔎 DEBUG TIMING CHECK:")
        logger.info(f"  🖥️ Desktop offset: {offset_ms} ms")
        logger.info(f"  🕒 Local time: {local_now}")
        logger.info(f"  🌍 Server time: {server_now}")
        logger.info(f"  🎯 endsAt (server-based): {ends_at}")
        logger.info("────────────────────────────────────────────────────────────")

        try:
            send_fcm_message("arena_pop", seconds, cfg=self.cfg)
            logger.info("🟢 arena_pop sent successfully")
        except Exception as e:
            logger.error(f"❌ Failed to send arena_pop: {e}")
            QMessageBox.warning(self, "Error", f"Failed to send arena_pop:\n{e}")
            return

        # Auto-stop after countdown
        if self.test_timer:
            self.test_timer.stop()

        self.test_timer = QTimer(self)
        self.test_timer.setSingleShot(True)
        self.test_timer.timeout.connect(self.finish_full_test)
        self.test_timer.start(seconds * 1000)

    def finish_full_test(self):
        """Send arena_stop after countdown time elapsed."""
        try:
            send_fcm_message("arena_stop", 0, cfg=self.cfg)
            logger.info("🛑 arena_stop sent (auto after test)")
            QMessageBox.information(self, "Full Test", "✅ Auto arena_stop sent — test complete!")
        except Exception as e:
            logger.error(f"❌ Failed to send arena_stop: {e}")
            QMessageBox.warning(self, "Error", f"Failed to send arena_stop:\n{e}")
        finally:
            self.test_timer = None

    # -------------------------------------------------------------------------
    # DEBUG TIMING TEST
    # -------------------------------------------------------------------------
    def run_debug_timing_test(self):
        """Run deep timing comparison with offset diff."""
        seconds = self.time_input.value()
        test_id = str(uuid.uuid4())

        offset_ms = get_server_offset(self.cfg)
        local_now = int(time.time() * 1000)
        server_now = local_now + offset_ms
        ends_at = server_now + seconds * 1000

        logger.info("───────────────────────────────────────────────")
        logger.info(f"🧠 Full Debug Timing Test ({seconds}s) id={test_id}")
        logger.info(f"🕒 Local now: {local_now}")
        logger.info(f"🌍 Server now: {server_now}")
        logger.info(f"🖥️ Desktop offset: {offset_ms}")
        logger.info(f"🎯 endsAt: {ends_at}")
        logger.info("───────────────────────────────────────────────")

        try:
            send_fcm_message("arena_pop", seconds, cfg=self.cfg)
            logger.info("🟢 Debug arena_pop sent (offset diff mode)")
        except Exception as e:
            logger.error(f"❌ Failed to send debug arena_pop: {e}")
            return

        def delayed_stop():
            time.sleep(seconds + 5)
            try:
                send_fcm_message("arena_stop", 0, cfg=self.cfg)
                logger.info("🛑 Debug arena_stop sent (auto)")
                logger.info("✅ Debug test finished successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to send debug arena_stop: {e}")

        threading.Thread(target=delayed_stop, daemon=True).start()

    # -------------------------------------------------------------------------
    # CLOCK SYNC
    # -------------------------------------------------------------------------
    def check_clock_sync(self):
        """Check local vs Firebase server time offset."""
        try:
            provider = CredentialsProvider()
            rtdb_url = provider.get_rtdb_url()
            offset_ms = get_server_offset(self.cfg)
            local_time = int(time.time() * 1000)
            server_time = local_time + offset_ms

            logger.info("───────────────────────────────────────────────")
            logger.info(f"🕒 Clock sync check ({rtdb_url})")
            logger.info(f"  Local time: {local_time}")
            logger.info(f"  Offset: {offset_ms} ms")
            logger.info(f"  Server ≈ {server_time}")
            logger.info("───────────────────────────────────────────────")

            QMessageBox.information(
                self,
                "Clock Sync Check",
                f"🕒 Firebase Clock Sync:\n\n"
                f"RTDB URL: {rtdb_url}\n"
                f"Local time: {local_time}\n"
                f"Offset: {offset_ms} ms\n"
                f"Server time ≈ {server_time}\n\n"
                f"{'✅ Clock is well-synced.' if abs(offset_ms) < 300 else '⚠️ Noticeable drift detected!'}"
            )

        except Exception as e:
            logger.error(f"❌ Clock sync check failed: {e}")
            QMessageBox.warning(self, "Error", f"Failed to check clock sync:\n{e}")

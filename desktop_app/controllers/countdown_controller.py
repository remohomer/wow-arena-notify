# file: desktop_app/controllers/countdown_controller.py

from PySide6.QtCore import QTimer
from infrastructure.logger import logger
from infrastructure.config import load_config

class CountdownController:
    def __init__(self, main_window):
        self.main = main_window
        self.timer = None
        self.remaining = 0
        self.running = False

    def start(self, seconds: int):
        """
        Start a countdown using the *latest* values stored in config.json.
        This allows runtime changes without restarting the app.
        """
        try:
            self.stop()

            # ✅ Always refresh config dynamically
            cfg = load_config()
            configured = int(cfg.get("countdown_time", seconds))
            self.remaining = max(configured, 1)  # fallback sanity

            self.running = True

            self.main.queue_tab.start_countdown_ui(self.remaining)
            self.main.queue_tab.update_countdown_ui(self.remaining)

            self.timer = QTimer(self.main)
            self.timer.timeout.connect(self._tick)
            self.timer.start(1000)

            logger.user(f"⏱ Countdown started: {self.remaining}s")

        except Exception as e:
            logger.error(f"❌ CountdownController.start(): {e}")

    def _tick(self):
        try:
            if not self.running:
                return

            self.remaining -= 1

            if self.remaining > 0:
                self.main.queue_tab.update_countdown_ui(self.remaining)
                return

            # == 0 seconds ==
            self.stop(hide_only=False)
            self.main.queue_tab.set_status("⚔️ FIGHT!", "#ff4444", big=True)

            # Auto-restore listening mode after 2s
            def restore():
                if self.main.listener and self.main.listener.is_running:
                    self.main.queue_tab.set_listening(True)

            fin = QTimer(self.main)
            fin.setSingleShot(True)
            fin.timeout.connect(restore)
            fin.start(2000)

        except Exception as e:
            logger.error(f"❌ CountdownController._tick(): {e}")

    def stop(self, hide_only: bool = True):
        try:
            if self.timer:
                self.timer.stop()
                self.timer = None

            self.running = False
            self.main.queue_tab.stop_countdown_ui(reset_status_to_listening=False)

        except Exception as e:
            logger.error(f"❌ CountdownController.stop(): {e}")

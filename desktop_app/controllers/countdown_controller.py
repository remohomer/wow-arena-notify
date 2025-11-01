# file: desktop_app/controllers/countdown_controller.py

from PySide6.QtCore import QTimer
from infrastructure.logger import logger

class CountdownController:
    def __init__(self, main_window):
        self.main = main_window
        self.timer = None
        self.remaining = 0
        self.running = False

    def start(self, seconds: int):
        try:
            self.stop()
            self.remaining = max(int(seconds), 1)
            self.running = True

            self.main.home_tab.start_countdown_ui(self.remaining)
            self.main.home_tab.update_countdown_ui(self.remaining)

            self.timer = QTimer(self.main)
            self.timer.timeout.connect(self._tick)
            self.timer.start(1000)
            logger.info(f"⏱ Countdown started: {self.remaining}s")
        except Exception as e:
            logger.error(f"❌ CountdownController.start(): {e}")

    def _tick(self):
        try:
            if not self.running:
                return

            self.remaining -= 1

            if self.remaining > 0:
                self.main.home_tab.update_countdown_ui(self.remaining)
                return

            # == 0 ==
            self.stop(hide_only=False)
            self.main.home_tab.set_status("⚔️ FIGHT!", "#ff4444", big=True)

            def restore():
                if self.main.listener and self.main.listener.is_running:
                    self.main.home_tab.set_listening(True)

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
            self.main.home_tab.stop_countdown_ui(reset_status_to_listening=False)
        except Exception as e:
            logger.error(f"❌ CountdownController.stop(): {e}")

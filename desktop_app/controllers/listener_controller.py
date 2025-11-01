# file: desktop_app/controllers/listener_controller.py

import time
from PySide6.QtCore import QTimer
from infrastructure.logger import logger
from infrastructure.watcher import get_latest_screenshot_info
from infrastructure.utils import PrintScreenListener
from services import arena_logic

class ListenerController:
    def __init__(self, main):
        self.main = main
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_screenshots)

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.animate_status)

        self.print_listener = PrintScreenListener()
        self.reset_runtime_state()

    def reset_runtime_state(self):
        self.is_running = False
        self.last_screenshot_time = None
        self.high_watermark = 0
        self.app_start_time = time.time()
        self._recent = {}
        self._cooldown_until = 0
        self.pulse_state = False

    # ------------------------------
    def start(self):
        self.reset_runtime_state()
        self.is_running = True
        self.main.home_tab.set_listening(True)

        _, self.last_screenshot_time = get_latest_screenshot_info(self.main.game_folder)
        self.high_watermark = self.last_screenshot_time or 0

        self.timer.start(1000)
        self.pulse_timer.start(500)

    def stop(self):
        self.is_running = False
        self.main.home_tab.set_listening(False)
        self.main.home_tab.set_paused_status()
        self.timer.stop()
        self.pulse_timer.stop()
        self.main.countdown.stop()

    # ------------------------------
    def animate_status(self):
        if not self.is_running:
            return
        lbl = self.main.home_tab.status_label
        txt = lbl.text().rstrip('.')
        if "FIGHT" in lbl.text():
            return
        lbl.setText(txt + '.' if not self.pulse_state else txt)
        self.pulse_state = not self.pulse_state

    # ------------------------------
    def check_screenshots(self):
        if not self.is_running or not self.main.game_folder:
            return

        now = time.time()
        if now < self._cooldown_until:
            return

        path, ts = get_latest_screenshot_info(self.main.game_folder)
        if not path or not ts:
            return
        if ts < self.app_start_time or ts <= self.high_watermark:
            return

        # debounce by size & time
        try:
            size = path.stat().st_size
            prev = self._recent.get(str(path))
            if prev and prev[0] == size and abs(now - prev[2]) < 3:
                return
            self._recent[str(path)] = (size, ts, now)
        except:
            pass

        self._cooldown_until = now + 1
        self.high_watermark = ts
        self.last_screenshot_time = ts

        if self.print_listener.is_recent(ts):
            return

        result = arena_logic.process_screenshot_event(
            path, self.main.cfg, app_start_time=self.app_start_time
        )

        if result == "arena_pop":
            self.main.home_tab.set_status("⚔️ Arena queue popped!", "#ffaa00", big=False)

            # używamy wartości policzonej przez arena_logic
            adjusted = max(int(self.main.cfg.get("countdown_time", 40))
                           - int(self.main.cfg.get("delay_offset", 2))
                           - 1, 1)

            self.main.countdown.start(adjusted)

        elif result == "arena_stop":
            self.main.countdown.stop()
            self.main.home_tab.set_status("⚔️ FIGHT!", "#ff4444", big=True)
            QTimer.singleShot(2000, self.restore_status)

    def restore_status(self):
        # poprawka: countdown.running, nie .active
        if self.is_running and not self.main.countdown.running:
            self.main.home_tab.set_listening(True)

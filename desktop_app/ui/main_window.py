import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit, QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, Qt

from core.config import load_config, save_config
from core.watcher import get_latest_screenshot_info
from core.utils import PrintScreenListener
from core.logger import logger
from core import arena_logic

from ui.tabs.home_tab import HomeTab
from ui.tabs.logs_tab import LogsTab          # zakładam, że ten plik już masz
from ui.tabs.tester_tab import TesterTab      # opcjonalny tester


class MainWindow(QWidget):
    """Main application window for WoW Arena Notify."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WoW Arena Notify")
        self.setFixedSize(480, 460)

        # App icon
        icon_path = None
        try:
            if hasattr(sys, "_MEIPASS"):
                cand = Path(sys._MEIPASS) / "icon.ico"
                if cand.exists():
                    icon_path = cand
            if icon_path is None:
                cand = Path("icon.ico")
                if cand.exists():
                    icon_path = cand
            if icon_path is None:
                cand = Path.cwd() / "ui" / "icon.ico"
                if cand.exists():
                    icon_path = cand
            if icon_path:
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                logger.warning("⚠️ icon.ico not found!")
        except Exception as e:
            logger.warning(f"⚠️ Failed to set window icon: {e}")

        # --- App state ---
        self.cfg = load_config()
        self.game_folder = self.cfg.get("game_folder", "")
        self.countdown_value = 0
        self.is_running = False
        self.is_countdown_active = False
        self.pulse_state = False
        self.last_screenshot_time = None
        self.high_watermark = 0
        self.app_start_time = time.time()

        # Lightweight UI dedup safeguard
        self._recent_files = {}
        self._cooldown_until = 0

        # --- Timers ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_screenshots)
        self.countdown_timer = None
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.animate_status)

        # --- Tabs ---
        self.tabs = QTabWidget(self)
        self.home_tab = HomeTab(self, self.cfg)
        self.logs_tab = LogsTab(self)  # ma w środku QPlainTextEdit i podpina logger
        self.tester_tab = TesterTab(self, self.cfg)  # jeśli masz tester jako zakładkę

        self.tabs.addTab(self.home_tab, "🏠 Home")
        self.tabs.addTab(self.logs_tab, "🧾 Logs")
        self.tabs.addTab(self.tester_tab, "🧪 Tester")

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        # sygnał Start/Stop z zakładki Home
        self.home_tab.toggleRequested.connect(self.toggle_listening)

        self.load_styles()

        # WoW folder – jeśli brak, poproś użytkownika
        if not self.game_folder:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            QMessageBox.information(self, "Select game folder",
                                    "Please select your World of Warcraft folder.")
            folder = QFileDialog.getExistingDirectory(self, "Select your World of Warcraft folder")
            if folder:
                self.game_folder = folder
                self.cfg["game_folder"] = folder
                save_config(self.cfg)
                self.home_tab.folder_label.setText(f"Game folder: {folder}")
                _, self.last_screenshot_time = get_latest_screenshot_info(self.game_folder)
                self.high_watermark = self.last_screenshot_time or 0

        # PrintScreen listener
        self.print_listener = PrintScreenListener()

        # Start + tray
        self.start_listening()
        self.init_tray_icon()

    # -------------------------------
    # Styles
    # -------------------------------
    def load_styles(self):
        try:
            candidates = [
                Path(__file__).parent / "styles.qss",
                Path.cwd() / "ui" / "styles.qss",
                Path.cwd() / "styles.qss",
            ]
            for p in candidates:
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        self.setStyleSheet(f.read())
                    logger.info(f"🎨 Loaded style: {p}")
                    return
            logger.warning("⚠ Could not find styles.qss.")
        except Exception as e:
            logger.warning(f"⚠ Could not load style: {e}")

    # -------------------------------
    # Start/Stop
    # -------------------------------
    def start_listening(self):
        self.app_start_time = time.time()
        self.is_running = True
        self.home_tab.set_listening(True)
        self.pulse_timer.start(500)
        _, self.last_screenshot_time = get_latest_screenshot_info(self.game_folder)
        self.high_watermark = self.last_screenshot_time or 0
        self.timer.start(1000)
        logger.info("🎧 Listener started automatically.")

    def stop_listening(self):
        self.is_running = False
        self.home_tab.set_listening(False)
        self.timer.stop()
        self.pulse_timer.stop()
        self.stop_countdown()
        logger.info("⏹ Listener stopped manually.")

    def toggle_listening(self):
        if self.is_running:
            self.stop_listening()
        else:
            self.start_listening()

    def animate_status(self):
        if not self.is_running:
            return
        try:
            lbl = self.home_tab.status_label
            txt = lbl.text().rstrip('.')
            lbl.setText(txt if self.pulse_state else txt + '.')
            self.pulse_state = not self.pulse_state
        except Exception as e:
            logger.warning(f"⚠️ animate_status error: {e}")

    # -------------------------------
    # Screenshot watcher
    # -------------------------------
    def check_screenshots(self):
        if not self.is_running or not self.game_folder:
            return

        now = time.time()
        if now < self._cooldown_until:
            return

        latest_path, latest_time = get_latest_screenshot_info(self.game_folder)
        if not latest_path or not latest_time:
            return
        if latest_time < self.app_start_time or latest_time <= self.high_watermark:
            return

        # UI debouncing
        try:
            size = latest_path.stat().st_size
            key = str(latest_path)
            prev = self._recent_files.get(key)
            if prev and prev[0] == size and abs(now - prev[2]) < 3:
                logger.debug(f"⏸ UI debounce ignored duplicate: {key}")
                return
            self._recent_files[key] = (size, latest_time, now)
        except Exception as e:
            logger.warning(f"⚠ Could not stat file {latest_path}: {e}")

        self._cooldown_until = now + 1
        self.high_watermark = latest_time
        self.last_screenshot_time = latest_time

        if self.print_listener.is_recent(latest_time):
            logger.info("⏸ Ignored user's PrintScreen.")
            return

        try:
            result = arena_logic.process_screenshot_event(
                latest_path,
                self.cfg,
                app_start_time=self.app_start_time
            )

            if result == "arena_pop":
                logger.info("🟢 Queue-pop detected → starting countdown.")
                self.home_tab.set_status("⚔️ Arena popup detected!", "#ffaa00")
                adjusted = max(int(self.home_tab.time_input.value()) - 4, 1)
                self.start_countdown(adjusted)

            elif result == "arena_stop":
                logger.info("🛑 Arena start detected → stopping countdown.")
                self.home_tab.set_status("🏁 Arena start detected (countdown stopped).", "#ffaa00")
                self.stop_countdown()

        except Exception as e:
            logger.error(f"⚠️ Error checking screenshots: {e}")
        finally:
            try:
                arena_logic.delete_screenshot_later(latest_path)
            except Exception:
                pass

    # -------------------------------
    # Countdown
    # -------------------------------
    def start_countdown(self, seconds: int):
        self.countdown_value = int(seconds)
        self.is_countdown_active = True
        self.home_tab.start_countdown_ui(self.countdown_value)

        if self.countdown_timer:
            self.countdown_timer.stop()
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_progress)
        self.countdown_timer.start(1000)
        logger.info(f"⏳ Countdown started: {self.countdown_value}s")

    def update_progress(self):
        if not self.is_countdown_active:
            return
        current = self.home_tab.progress.value() + 1
        self.home_tab.update_countdown_ui(current)
        if current >= self.home_tab.progress.maximum():
            self.stop_countdown()
            self.home_tab.set_status("⌛ Countdown finished!", "#ff0000")

    def stop_countdown(self):
        if self.countdown_timer:
            self.countdown_timer.stop()
            self.countdown_timer = None
        self.is_countdown_active = False
        self.home_tab.stop_countdown_ui(reset_status_to_listening=True)
        self.app_start_time = time.time()
        logger.info("🛑 Countdown stopped.")

    # -------------------------------
    # Tray
    # -------------------------------
    def init_tray_icon(self):
        try:
            icon_path = None
            if hasattr(sys, "_MEIPASS"):
                cand = Path(sys._MEIPASS) / "icon.ico"
                if cand.exists():
                    icon_path = cand
            if icon_path is None:
                cand = Path("icon.ico")
                if cand.exists():
                    icon_path = cand
            if icon_path is None:
                cand = Path.cwd() / "ui" / "icon.ico"
                if cand.exists():
                    icon_path = cand
            if not icon_path:
                logger.error("❌ Tray icon not found.")
                return

            icon = QIcon(str(icon_path))
            self.tray_icon = QSystemTrayIcon(icon, self)
            self.tray_icon.setToolTip("WoW Arena Notify — running in background")

            tray_menu = QMenu()
            show_action = QAction("🪄 Show window", self)
            quit_action = QAction("❌ Exit application", self)
            show_action.triggered.connect(self.restore_from_tray)
            quit_action.triggered.connect(self.quit_app)
            tray_menu.addAction(show_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_activated)
            QTimer.singleShot(1500, self.tray_icon.show)
        except Exception as e:
            logger.error(f"⚠ Failed to create tray icon: {e}")

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.restore_from_tray()

    from PySide6.QtWidgets import QMessageBox

    def closeEvent(self, event):
        """Ask user whether to exit or minimize to tray."""
        msg = QMessageBox(self)
        msg.setWindowTitle("WoW Arena Notify")
        msg.setText("Do you want to close the application or keep it running in the background?")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText("❌ Exit")
        msg.button(QMessageBox.No).setText("🪄 Minimize to tray")
        msg.button(QMessageBox.Cancel).setText("Cancel")

        result = msg.exec()

        if result == QMessageBox.No:  # minimize
            event.ignore()
            self.hide()
            try:
                if hasattr(self, "tray_icon"):
                    self.tray_icon.showMessage(
                        "WoW Arena Notify",
                        "The app is still running in the background. Click the tray icon to restore it.",
                        QSystemTrayIcon.Information,
                        3000,
                    )
            except Exception:
                pass
            logger.info("💤 App minimized to tray by user choice.")
        elif result == QMessageBox.Yes:  # exit
            event.accept()
            self.quit_app()
        else:  # cancel
            event.ignore()


    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        logger.info("🪄 Restored window from tray.")

    def quit_app(self):
        try:
            summary = arena_logic.session_summary_string()
            logger.info(summary)
        except Exception:
            pass
        logger.info("👋 Closing application…")
        try:
            self.timer.stop()
            if self.countdown_timer:
                self.countdown_timer.stop()
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()
        except Exception:
            pass
        QApplication.quit()

# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import json
import requests

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QApplication, QMessageBox, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer, QObject, QEvent

from infrastructure.config import load_config, save_config
from infrastructure.logger import logger
from infrastructure.credentials_provider import CredentialsProvider

from controllers.listener_controller import ListenerController
from controllers.countdown_controller import CountdownController
from controllers.tray_controller import TrayController

from ui.style_loader import apply_styles

from ui.tabs.queue_tab import QueueTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.tester_tab import TesterTab
from ui.tabs.pairing_tab import PairingTab
from ui.tabs.settings_tab import SettingsTab


BASE_DIR = Path(
    getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent)
)


# ----------------------------- Broadcast poller
class BroadcastPoller(QObject):
    def __init__(self, label: QLabel, interval_ms: int = 7000, parent: QObject | None = None):
        super().__init__(parent)
        self.label = label
        self.interval_ms = max(1500, int(interval_ms))
        self._last_payload = None

        creds = CredentialsProvider()
        self.rtdb_url = (creds.get_rtdb_url() or "").rstrip("/")
        if not self.rtdb_url:
            logger.user("RTDB URL not configured; broadcast bar disabled.")
            self.label.hide()
            return

        self.timer = QTimer(self)
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._tick)

        self._tick()
        self.timer.start()

    def _tick(self):
        try:
            url = f"{self.rtdb_url}/broadcast.json"
            resp = requests.get(url, timeout=5)

            if not resp.ok:
                self._show_offline_status()
                return

            data = resp.json() if resp.text else {}
            if not isinstance(data, dict):
                data = {}

            # If unchanged, skip UI updates
            if json.dumps(data, sort_keys=True) == json.dumps(self._last_payload or {}, sort_keys=True):
                return

            self._last_payload = data

            msg = data.get("message", "") or ""
            lvl = data.get("level", "info") or "info"
            color = data.get("color", "").strip() or None

            if not msg.strip():
                self.label.hide()
                return

            self._apply_broadcast(msg, lvl, color)

        except Exception as e:
            logger.dev(f"broadcast poll error: {e}")
            self._show_offline_status()

    def _apply_broadcast(self, msg, lvl, color):
        self.label.show()
        self.label.setText(msg)
        self.label.setProperty("level", lvl)

        # Inline only for info override
        if color and lvl == "info":
            self.label.setStyleSheet(f"color:{color};")
        else:
            self.label.setStyleSheet("")

        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)
        self.label.update()


    def _show_offline_status(self):
        offline_payload = {"message": "⚠️ Lost connection to server…", "level": "critical"}
        # Skip spam
        if offline_payload == self._last_payload:
            return

        self._last_payload = offline_payload
        self._apply_broadcast("⚠️ Lost connection to server…", "critical", None)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WoW Arena Notify")
        self.setFixedSize(480, 460)

        icon_path = BASE_DIR / "icon.ico"
        if not icon_path.exists():
            icon_path = Path.cwd() / "ui" / "icon.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        self.cfg = load_config()
        self.game_folder = self.cfg.get("game_folder", "")

        self.listener = ListenerController(self)
        self.countdown = CountdownController(self)
        self.tray = TrayController(self)

        # Broadcast bar
        self.broadcastBar = QLabel("", self)
        self.broadcastBar.setObjectName("broadcastBar")
        self.broadcastBar.setFixedHeight(24)
        self.broadcastBar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.broadcastBar.setProperty("level", "info")
        self.broadcastBar.hide()

        TITLEBAR_GAP = 8
        self.broadcastBar.move(0, TITLEBAR_GAP)
        self.broadcastBar.setFixedWidth(self.width())
        self.broadcastBar.raise_()

        # marquee
        self._scroll_offset = 0
        self._hover_pause = False

        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(50)
        self._scroll_timer.timeout.connect(self._scroll_text)
        self._scroll_timer.start()

        self.broadcastBar.installEventFilter(self)

        # tabs
        self.tabs = QTabWidget(self)
        self.tabs.setTabPosition(QTabWidget.North)

        self.queue_tab = QueueTab(self, self.cfg)
        self.pairing_tab = PairingTab(self)
        self.logs_tab = LogsTab(self)
        self.tester_tab = TesterTab(self, self.cfg)
        self.settings_tab = SettingsTab(self)

        self.tabs.addTab(self.queue_tab, "🕒 Queue")
        self.tabs.addTab(self.pairing_tab, "🔗 Pairing")
        self.tabs.addTab(self.logs_tab, "🧾 Logs")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        if self.cfg.get("debug_mode", False):
            self.tabs.addTab(self.tester_tab, "🧪 Tester")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 40, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.tabs)

        self._resizeTimer = QTimer(self)
        self._resizeTimer.setInterval(200)
        self._resizeTimer.timeout.connect(lambda:
                                          self.broadcastBar.setFixedWidth(self.width()))
        self._resizeTimer.start()

        self.queue_tab.toggleRequested.connect(self.toggle_listening)
        self.queue_tab.resetRequested.connect(self.handle_reset)

        apply_styles(self)

        # # FIRST-RUN SETUP
        if not self.game_folder:
            self.request_game_folder()

        QTimer.singleShot(300, self.listener.start)
        self.tray.init_tray(icon_path)

        self._broadcast = BroadcastPoller(self.broadcastBar, interval_ms=7000, parent=self)

    # Hover pause
    def eventFilter(self, obj, event):
        if obj == self.broadcastBar:
            if event.type() == QEvent.Enter:
                self._hover_pause = True
            elif event.type() == QEvent.Leave:
                self._hover_pause = False
        return super().eventFilter(obj, event)

    def _scroll_text(self):
        if self._hover_pause:
            return

        text_width = self.broadcastBar.fontMetrics().horizontalAdvance(self.broadcastBar.text())
        label_width = self.broadcastBar.width()

        if text_width <= label_width:
            self.broadcastBar.setAlignment(Qt.AlignCenter)
            return

        self.broadcastBar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._scroll_offset = (self._scroll_offset + 2) % (text_width + 20)

        self.broadcastBar.setStyleSheet(
            self.broadcastBar.styleSheet() +
            f"; padding-left: {-self._scroll_offset}px;"
        )

    def toggle_listening(self):
        if self.listener.is_running:
            self.listener.stop()
        else:
            self.listener.start()

    def request_game_folder(self):
        # don't trigger if wizard already handled setup
        from infrastructure.config import load_config
        cfg = load_config()
        if not cfg.get("first_run", False) and self.game_folder:
            return
        from PySide6.QtWidgets import QFileDialog
        QMessageBox.information(self, "Select game folder", "Select your WoW directory.")
        folder = QFileDialog.getExistingDirectory(self, "Select your WoW folder")
        if folder:
            self.game_folder = folder
            self.cfg["game_folder"] = folder
            save_config(self.cfg)

    def handle_reset(self):
        self.countdown.stop()
        self.queue_tab.reset_ui()

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.listener.stop()
        self.countdown.stop()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle("WoW Arena Notify")
        msg.setText("Exit or minimize to tray?")
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.No | QMessageBox.Yes)
        msg.button(QMessageBox.Cancel).setText("Cancel")
        msg.button(QMessageBox.No).setText("🪄 Minimize to tray")
        msg.button(QMessageBox.Yes).setText("❌ Exit")

        res = msg.exec()
        if res == QMessageBox.No:
            event.ignore()
            self.hide()
        elif res == QMessageBox.Yes:
            event.accept()
            self.quit_app()
        else:
            event.ignore()

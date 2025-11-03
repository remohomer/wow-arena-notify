# file: desktop_app/ui/main_window.py

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QApplication, QMessageBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from infrastructure.config import load_config, save_config
from infrastructure.logger import logger

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
    getattr(sys, "_MEIPASS",
    Path(__file__).resolve().parent.parent.parent)
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WoW Arena Notify")
        self.setFixedSize(480, 460)

        # ------------- ICON
        icon_path = BASE_DIR / "icon.ico"
        if not icon_path.exists():
            icon_path = Path.cwd() / "ui" / "icon.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        # ------------- CONFIG
        self.cfg = load_config()
        self.game_folder = self.cfg.get("game_folder", "")

        # ------------- CONTROLLERS
        self.listener = ListenerController(self)
        self.countdown = CountdownController(self)
        self.tray = TrayController(self)

        # ------------- TABS
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
        root.addWidget(self.tabs)

        self.queue_tab.toggleRequested.connect(self.toggle_listening)
        self.queue_tab.resetRequested.connect(self.handle_reset)

        apply_styles(self)

        if not self.game_folder:
            self.request_game_folder()

        self.listener.start()
        self.tray.init_tray(icon_path)

    # ------------------------------ toggle
    def toggle_listening(self):
        if self.listener.is_running:
            self.listener.stop()
        else:
            self.listener.start()

    # ------------------------------ game folder
    def request_game_folder(self):
        from PySide6.QtWidgets import QFileDialog
        QMessageBox.information(self, "Select game folder", "Select your WoW directory.")
        folder = QFileDialog.getExistingDirectory(self, "Select your WoW folder")
        if folder:
            self.game_folder = folder
            self.cfg["game_folder"] = folder
            save_config(self.cfg)

    # ------------------------------ reset
    def handle_reset(self):
        self.countdown.stop()
        self.queue_tab.reset_ui()

    # ------------------------------ tray restore
    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ------------------------------ quit
    def quit_app(self):
        self.listener.stop()
        self.countdown.stop()
        self.tray.hide()
        QApplication.quit()

    # ------------------------------ close event
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

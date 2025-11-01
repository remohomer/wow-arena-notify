# file: desktop_app/controllers/tray_controller.py

from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon
from infrastructure.logger import logger

class TrayController:
    def __init__(self, main):
        self.main = main
        self.tray = None

    def init_tray(self, base_icon):
        icon = QIcon(str(base_icon))
        self.tray = QSystemTrayIcon(icon, self.main)

        menu = QMenu()
        show = QAction("🪄 Show window", self.main)
        quit = QAction("❌ Exit", self.main)
        show.triggered.connect(self.main.restore_from_tray)
        quit.triggered.connect(self.main.quit_app)
        menu.addAction(show)
        menu.addSeparator()
        menu.addAction(quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)
        self.tray.show()

    def _activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.main.restore_from_tray()

    def hide(self):
        if self.tray:
            self.tray.hide()

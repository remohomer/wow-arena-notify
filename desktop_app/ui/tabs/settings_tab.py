# ui/tabs/settings_tab.py — v1 (2025-10-27)
# ✅ Moved game folder + countdown time here
# ✅ Clean, minimal settings layout

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpinBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from core.config import load_config, save_config
from core.logger import logger
from core.watcher import get_latest_screenshot_info


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # === Game folder ===
        self.folder_label = QLabel(f"Game folder: {self.cfg.get('game_folder', '[not selected]')}")
        self.folder_label.setAlignment(Qt.AlignCenter)

        btn_folder = QPushButton("Change game folder")
        btn_folder.clicked.connect(self.select_folder)

        # === Countdown time ===
        time_layout = QHBoxLayout()
        lbl_time = QLabel("Countdown time (seconds):")
        self.spin_time = QSpinBox()
        self.spin_time.setRange(5, 120)
        self.spin_time.setValue(self.cfg.get("countdown_time", 40))
        self.spin_time.valueChanged.connect(self.on_countdown_changed)

        time_layout.addWidget(lbl_time)
        time_layout.addWidget(self.spin_time)

        layout.addWidget(self.folder_label)
        layout.addWidget(btn_folder)
        layout.addLayout(time_layout)
        layout.addStretch()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select your World of Warcraft folder")
        if not folder:
            return
        try:
            self.cfg["game_folder"] = folder
            save_config(self.cfg)
            self.folder_label.setText(f"Game folder: {folder}")
            _, ts = get_latest_screenshot_info(folder) or (None, None)
            logger.info(f"📁 Game folder set to: {folder} ({ts})")
        except Exception as e:
            logger.error(f"❌ Failed to select game folder: {e}")
            QMessageBox.warning(self, "Error", f"Could not save selected folder:\n{e}")

    def on_countdown_changed(self, value: int):
        self.cfg["countdown_time"] = int(value)
        save_config(self.cfg)
        logger.info(f"⏱ Countdown time set to {value}s")

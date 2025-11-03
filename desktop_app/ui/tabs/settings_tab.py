# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpinBox,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from infrastructure.config import load_config, save_config
from infrastructure.logger import logger
from infrastructure.watcher import get_latest_screenshot_info, resolve_screenshots_folder, list_screenshots
from services.tag_detector import detect_tag
from infrastructure.utils import safe_delete

from ui.toast import Toast

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.cfg = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        # === Game folder ===
        self.folder_label = QLabel(
            f"Game folder: {self.cfg.get('game_folder', '[not selected]')}"
        )
        self.folder_label.setAlignment(Qt.AlignCenter)

        btn_folder = QPushButton("Change game folder")
        btn_folder.clicked.connect(self.select_folder)

        # === Countdown duration ===
        time_layout = QHBoxLayout()
        lbl_time = QLabel("Countdown time (seconds):")
        self.spin_time = QSpinBox()
        self.spin_time.setRange(1, 40)  # ✅ ograniczenie 1–40
        self.spin_time.setValue(self.cfg.get("countdown_time", 38))
        self.spin_time.valueChanged.connect(self.on_countdown_changed)
        time_layout.addWidget(lbl_time)
        time_layout.addWidget(self.spin_time)

        # === Delay subtract ===
        delay_layout = QHBoxLayout()
        lbl_delay = QLabel("Screenshots delay (seconds):")
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(2, 5)  # ✅ ograniczenie 2–5
        self.spin_delay.setValue(self.cfg.get("delay_offset", 2))
        self.spin_delay.valueChanged.connect(self.on_delay_changed)
        delay_layout.addWidget(lbl_delay)
        delay_layout.addWidget(self.spin_delay)

        # === Clean tagged screenshots ===
        self.btn_clean = QPushButton("🧹 Clean tagged screenshots (bordered)")
        self.btn_clean.setStyleSheet("font-weight:600; padding:6px;")
        self.btn_clean.clicked.connect(self.clean_tagged_screenshots)

        # === Reset defaults ===
        self.btn_reset = QPushButton("↩️ Restore defaults")
        self.btn_reset.clicked.connect(self.restore_defaults)
        self.btn_reset.setStyleSheet("font-weight:600; padding:6px;")

        layout.addSpacing(10)
        layout.addWidget(self.folder_label)
        layout.addWidget(btn_folder)
        layout.addLayout(time_layout)
        layout.addLayout(delay_layout)
        layout.addWidget(self.btn_clean)
        layout.addWidget(self.btn_reset)
        layout.addStretch()

    # ---------------------------------------------------------------------
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select your World of Warcraft folder"
        )
        if not folder:
            return
        try:
            self.cfg["game_folder"] = folder
            save_config(self.cfg)
            self.folder_label.setText(f"Game folder: {folder}")
            _, ts = get_latest_screenshot_info(folder) or (None, None)
            logger.dev(f"📂 WoW folder selected: {folder}")
        except Exception as e:
            logger.user("Could not save selected folder.")
            QMessageBox.warning(
                self, "Error", f"Could not save selected folder:\n{e}"
            )

    # ---------------------------------------------------------------------
    def on_countdown_changed(self, value: int):
        value = max(1, min(40, value))
        self.cfg["countdown_time"] = int(value)
        save_config(self.cfg)
        logger.user(f"⏱ Countdown time set to {value}s")

    # ---------------------------------------------------------------------
    def on_delay_changed(self, value: int):
        value = max(2, min(5, value))
        self.cfg["delay_offset"] = int(value)
        save_config(self.cfg)
        logger.user(f"📁 Screenshot delay set to {value}s")

    # ---------------------------------------------------------------------
    def restore_defaults(self):
        DEFAULT_COUNTDOWN = 38
        DEFAULT_DELAY = 2

        self.cfg["countdown_time"] = DEFAULT_COUNTDOWN
        self.cfg["delay_offset"] = DEFAULT_DELAY
        save_config(self.cfg)

        self.spin_time.setValue(DEFAULT_COUNTDOWN)
        self.spin_delay.setValue(DEFAULT_DELAY)

        logger.user("↩️ Settings restored to defaults")
        Toast(self, "Defaults restored ✓")

    # ---------------------------------------------------------------------
    def clean_tagged_screenshots(self):
        folder = resolve_screenshots_folder(self.cfg.get("game_folder", ""))
        if not folder:
            QMessageBox.information(self, "Cleanup", "No Screenshots folder found.")
            return

        shots = list_screenshots(folder)
        if not shots:
            QMessageBox.information(self, "Cleanup", "📭 No screenshots found.")
            return

        removed = 0
        kept = 0
        for img in shots:
            tag = detect_tag(str(img))
            if tag in ("arena_pop", "arena_stop"):
                safe_delete(img)
                removed += 1
            else:
                kept += 1

        logger.user(f"🧹 Cleanup finished. Removed:{removed}, Kept:{kept}")
        QMessageBox.information(
            self, "Cleanup",
            f"Removed tagged: {removed}\nKept: {kept}"
        )

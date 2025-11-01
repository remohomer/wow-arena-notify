# file: desktop_app/ui/tabs/settings_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpinBox,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from infrastructure.config import load_config, save_config
from infrastructure.logger import logger
from infrastructure.watcher import get_latest_screenshot_info

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
        self.spin_time.setRange(5, 120)
        self.spin_time.setValue(self.cfg.get("countdown_time", 39))
        self.spin_time.valueChanged.connect(self.on_countdown_changed)

        time_layout.addWidget(lbl_time)
        time_layout.addWidget(self.spin_time)

        # === Delay subtract ===
        delay_layout = QHBoxLayout()
        lbl_delay = QLabel("Subtract delay (seconds):")
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(2, 10)
        self.spin_delay.setValue(self.cfg.get("delay_offset", 2))
        self.spin_delay.valueChanged.connect(self.on_delay_changed)

        delay_layout.addWidget(lbl_delay)
        delay_layout.addWidget(self.spin_delay)

        # === Reset defaults button ===
        self.btn_reset = QPushButton("↩️ Restore defaults")
        self.btn_reset.clicked.connect(self.restore_defaults)
        self.btn_reset.setStyleSheet("font-weight:600; padding:6px;")

        layout.addSpacing(10)
        layout.addWidget(self.folder_label)
        layout.addWidget(btn_folder)
        layout.addLayout(time_layout)
        layout.addLayout(delay_layout)
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
            logger.info(f"📁 Game folder set to: {folder} ({ts})")
        except Exception as e:
            logger.error(f"❌ Failed to select game folder: {e}")
            QMessageBox.warning(
                self, "Error", f"Could not save selected folder:\n{e}"
            )

    # ---------------------------------------------------------------------
    def on_countdown_changed(self, value: int):
        self.cfg["countdown_time"] = int(value)
        save_config(self.cfg)
        logger.info(f"⏱ Countdown time set to {value}s")

    # ---------------------------------------------------------------------
    def on_delay_changed(self, value: int):
        self.cfg["delay_offset"] = int(value)
        save_config(self.cfg)
        logger.info(f"⚙️ Delay offset set to {value}s (plus 1s fixed)")

    # ---------------------------------------------------------------------
    def restore_defaults(self):
        DEFAULT_COUNTDOWN = 38
        DEFAULT_DELAY = 2

        self.cfg["countdown_time"] = DEFAULT_COUNTDOWN
        self.cfg["delay_offset"] = DEFAULT_DELAY
        save_config(self.cfg)

        # Update UI widgets
        self.spin_time.setValue(DEFAULT_COUNTDOWN)
        self.spin_delay.setValue(DEFAULT_DELAY)

        logger.info("🔁 Settings restored: countdown=39, delay_offset=2")

        # ✅ tiny toast confirmation
        Toast(self, "Defaults restored ✓")

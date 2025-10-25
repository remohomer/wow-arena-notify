from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox, QHBoxLayout,
    QSpacerItem, QSizePolicy, QCheckBox, QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from core.config import save_config
from core.watcher import get_latest_screenshot_info
from core.logger import logger
from ui.dialogs import pair_device, how_it_works, test_connection


class HomeTab(QWidget):
    # Sygnał, który informuje MainWindow, że użytkownik kliknął Start/Stop.
    # MainWindow zareaguje i przełączy słuchanie.
    toggleRequested = Signal()

    def __init__(self, parent, cfg):
        super().__init__(parent)
        self.parent = parent
        self.cfg = cfg
        self._listening = False
        self._countdown_total = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # --- Folder selection ---
        self.folder_label = QLabel(f"Game folder: {self.cfg.get('game_folder', '[not selected]')}")
        self.folder_label.setAlignment(Qt.AlignCenter)

        folder_btn = QPushButton("Change game folder")
        folder_btn.clicked.connect(self.select_folder)

        # --- Countdown time ---
        time_layout = QHBoxLayout()
        time_label = QLabel("Countdown time (seconds):")
        self.time_input = QSpinBox()
        self.time_input.setRange(5, 120)
        self.time_input.setValue(self.cfg.get("countdown_time", 40))
        self.time_input.valueChanged.connect(self.on_countdown_changed)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_input)

        # --- Progress + status ---
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)

        self.status_label = QLabel("Starting listener…")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #ffaa00; font-weight:600;")

        # --- Control buttons ---
        self.start_stop_btn = QPushButton("⏸ Stop")
        self.start_stop_btn.clicked.connect(self.toggleRequested.emit)

        info_btn = QPushButton("❔ How it works")
        info_btn.clicked.connect(lambda: how_it_works.show_info(self))

        pair_btn = QPushButton("🔗 Pair device (QR)")
        pair_btn.clicked.connect(lambda: pair_device.show_pairing_dialog(self))

        test_btn = QPushButton("📡 Test connection")
        test_btn.clicked.connect(lambda: test_connection.run_test(self))

        row1 = QHBoxLayout()
        row1.addWidget(self.start_stop_btn)
        row1.addWidget(info_btn)

        row2 = QHBoxLayout()
        row2.addWidget(pair_btn)
        row2.addWidget(test_btn)

        # --- Background checkbox ---
        self.run_bg_checkbox = QCheckBox("Leave in background after closing")
        self.run_bg_checkbox.setChecked(self.cfg.get("run_in_background", False))
        self.run_bg_checkbox.stateChanged.connect(self.toggle_run_in_background)

        # --- Assemble ---
        layout.addWidget(self.folder_label)
        layout.addWidget(folder_btn)
        layout.addLayout(time_layout)
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addWidget(self.run_bg_checkbox)

    # ===== Public API wywoływane przez MainWindow =====

    def set_listening(self, is_on: bool):
        """Aktualizuje stan UI (tekst przycisku i status) zgodnie ze stanem słuchania."""
        self._listening = bool(is_on)
        self.start_stop_btn.setText("⏸ Stop" if is_on else "▶ Start")
        if is_on:
            self.set_status("Listening for arena queue popups…", "#4cff4c")
        else:
            self.set_status("⏸ Application stopped.", "#ff5555")

    def set_status(self, text: str, color_hex: str):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color:{color_hex}; font-weight:600;")

    def start_countdown_ui(self, seconds: int):
        self._countdown_total = max(int(seconds), 0)
        self.progress.setVisible(True)
        self.progress.setMaximum(self._countdown_total)
        self.progress.setValue(0)
        self.progress.setFormat(f"Entering arena in {self._countdown_total}s…")

    def update_countdown_ui(self, current_value: int):
        # current_value = ile sekund już upłynęło (MainWindow zarządza timerem)
        self.progress.setValue(current_value)
        remaining = max(self._countdown_total - current_value, 0)
        self.progress.setFormat(f"Entering arena in {remaining}s…")

    def stop_countdown_ui(self, reset_status_to_listening: bool = True):
        self.progress.setVisible(False)
        if reset_status_to_listening and self._listening:
            self.set_status("Listening for arena queue popups…", "#4cff4c")

    # ===== Handlers (wewnętrzne) =====

    def select_folder(self):
        from PySide6.QtWidgets import QFileDialog  # lokalny import (pyinstaller-friendly)
        folder = QFileDialog.getExistingDirectory(self, "Select your World of Warcraft folder")
        if folder:
            self.cfg["game_folder"] = folder
            save_config(self.cfg)
            self.folder_label.setText(f"Game folder: {folder}")
            _, ts = get_latest_screenshot_info(folder)
            logger.info(f"📁 Game folder set to: {folder} ({ts})")

    def on_countdown_changed(self, value: int):
        self.cfg["countdown_time"] = int(value)
        save_config(self.cfg)
        logger.info(f"⏱ Countdown time set to {value}s (saved)")

    def toggle_run_in_background(self, state):
        new_val = bool(state)
        if self.cfg.get("run_in_background") == new_val:
            return
        self.cfg["run_in_background"] = new_val
        save_config(self.cfg)
        logger.info(f"⚙ run_in_background set to {new_val}")

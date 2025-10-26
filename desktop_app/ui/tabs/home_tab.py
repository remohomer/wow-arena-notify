# ui/tabs/home_tab.py — v7 (2025-10-27)
# ✅ Minimal Home tab for listener control
# ✅ Buttons anchored at bottom
# ✅ Ready for new styles.qss

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from ui.dialogs import how_it_works


class HomeTab(QWidget):
    toggleRequested = Signal()

    def __init__(self, parent, cfg):
        super().__init__(parent)
        self.cfg = cfg
        self._listening = False
        self._countdown_total = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # === STATUS ===
        self.status_label = QLabel("Initializing listener…")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #ffaa00; font-weight:600; font-size:14px;")

        # === PROGRESS BAR ===
        self.progress = QProgressBar()
        self.progress.hide()
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)

        # === SPACER ===
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addSpacerItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # === BUTTONS (bottom row) ===
        self.btn_toggle = QPushButton("▶ Start")
        self.btn_toggle.setObjectName("mainButton")
        self.btn_toggle.clicked.connect(self.toggleRequested.emit)

        btn_info = QPushButton("❔ How it works")
        btn_info.setObjectName("secondaryButton")
        btn_info.clicked.connect(lambda: how_it_works.show_info(self))

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_info)
        row.addWidget(self.btn_toggle)

        layout.addLayout(row)
        layout.addStretch()

    # === Listener UI ===
    def set_listening(self, active: bool):
        """Toggle start/stop listener visuals."""
        self._listening = active
        self.btn_toggle.setText("⏸ Stop" if active else "▶ Start")
        color = "#4cff4c" if active else "#ff5555"
        text = "Listening for arena queue popups…" if active else "⏸ Application stopped."
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color:{color}; font-weight:600; font-size:14px;")

    def start_countdown_ui(self, seconds: int):
        """Initialize countdown progress bar."""
        self._countdown_total = max(int(seconds), 0)
        self.progress.show()
        self.progress.setMaximum(self._countdown_total)
        self.progress.setValue(0)
        self.progress.setFormat(f"Entering arena in {self._countdown_total}s…")

    def update_countdown_ui(self, value: int):
        """Update countdown progress each second."""
        self.progress.setValue(value)
        remaining = max(self._countdown_total - value, 0)
        self.progress.setFormat(f"Entering arena in {remaining}s…")

    def stop_countdown_ui(self, reset_status_to_listening: bool = True):
        """Hide progress and restore listening label."""
        self.progress.hide()
        if reset_status_to_listening and self._listening:
            self.set_listening(True)

# === Status helper (for arena events) ===
    def set_status(self, text: str, color: str = "#ffaa00"):
        """Updates status label color and text (used by main_window)."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color:{color}; font-weight:600; font-size:14px;")
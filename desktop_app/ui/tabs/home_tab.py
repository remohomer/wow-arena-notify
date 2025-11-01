# file: desktop_app/ui/tabs/home_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from pathlib import Path
import sys

BASE_DIR = Path(getattr(sys, "_MEIPASS",
         Path(__file__).resolve().parent.parent.parent))
PORTAL_IMAGE_PATH = BASE_DIR / "assets" / "portal_icon.png"


class HomeTab(QWidget):
    toggleRequested = Signal()
    resetRequested = Signal()

    def __init__(self, parent, cfg):
        super().__init__(parent)
        self.cfg = cfg
        self._listening = False
        self._max_seconds = 0
        self.init_ui()

    # ------------------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # Portal
        self.portal_label = QLabel(alignment=Qt.AlignCenter)
        self.portal_label.setMinimumSize(230, 230)

        if PORTAL_IMAGE_PATH.exists():
            pix = QPixmap(str(PORTAL_IMAGE_PATH))
        else:
            pix = QPixmap(240, 240)
            pix.fill(Qt.darkGray)

        img = pix.toImage().convertToFormat(QImage.Format_ARGB32)
        base_pix = QPixmap.fromImage(img).scaled(
            260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.portal_label.setPixmap(base_pix)

        layout.addStretch()
        layout.addWidget(self.portal_label, alignment=Qt.AlignCenter)

        # Status
        self.status_label = QLabel(
            "Listening for arena queue popups…",
            alignment=Qt.AlignCenter
        )
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.hide()
        self.progress.setFixedHeight(25)
        layout.addWidget(self.progress)

        layout.addSpacing(10)

        # Buttons
        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.setObjectName("secondaryButton")
        self.btn_reset.clicked.connect(self.resetRequested.emit)

        self.btn_toggle = QPushButton("▶ Start")
        self.btn_toggle.setObjectName("resumeButton")
        self.btn_toggle.clicked.connect(self.toggleRequested.emit)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.btn_reset)
        row.addWidget(self.btn_toggle)
        row.addStretch()
        layout.addLayout(row)

        layout.addStretch()

    # ------------------------------------------------------------------
    def set_listening(self, active: bool):
        self._listening = active
        if active:
            self.btn_toggle.setText("⏸ Stop")
            self.btn_toggle.setObjectName("stopButton")
            self.set_status("Listening for arena queue popups…", "#ffaa00", big=False)
        else:
            self.btn_toggle.setText("▶ Resume")
            self.btn_toggle.setObjectName("resumeButton")
            self.set_paused_status()

        self.btn_toggle.style().unpolish(self.btn_toggle)
        self.btn_toggle.style().polish(self.btn_toggle)
        self.btn_toggle.update()

    # ------------------------------------------------------------------
    def start_countdown_ui(self, seconds: int):
        """Initialize countdown UI (downward)."""
        self._max_seconds = seconds
        self.progress.setMaximum(seconds)
        # progress value == remaining seconds (counts down)
        self.progress.setValue(seconds)
        self.progress.setFormat(f"{seconds}s")
        self.progress.show()
        # tekst statusu bez sekund
        self.set_status("⚔️ Arena queue popped!", "#ffaa00", big=False)

    def update_countdown_ui(self, remaining: int):
        """Update remaining seconds on the bar (downward)."""
        if remaining < 0:
            remaining = 0
        self.progress.setValue(remaining)
        self.progress.setFormat(f"{remaining}s")

    def stop_countdown_ui(self, reset_status_to_listening=True):
        self.progress.hide()
        if reset_status_to_listening:
            self.set_status("Listening for arena queue popups…", "#ffaa00", big=False)

    # ------------------------------------------------------------------
    def set_status(self, text, color="#ffaa00", big=False):
        size = 23 if big else 15
        weight = 800 if big else 600
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color:{color};font-weight:{weight};font-size:{size}px;"
        )

    def set_paused_status(self):
        self.status_label.setText("⏸ Listening paused.")
        self.status_label.setStyleSheet(
            "color:#ff7777; font-weight:600; font-size:15px;"
        )

    # ------------------------------------------------------------------
    def reset_ui(self):
        self.progress.hide()
        self.set_status("Listening for arena queue popups…", "#ffaa00", big=False)

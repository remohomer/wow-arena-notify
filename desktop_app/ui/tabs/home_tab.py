# ui/tabs/home_tab.py — v14 (2025-10-29 final)
# ✅ Proper STOP/RESUME logic UI
# ✅ Consistent colors
# ✅ Progress bar padding fix

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QHBoxLayout, QSpacerItem, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, Signal, QEasingCurve, QPropertyAnimation,
    QParallelAnimationGroup, QAbstractAnimation
)
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

        self.init_ui()
        self._setup_animations()

    # UI
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        self.portal_label = QLabel(alignment=Qt.AlignCenter)
        self.portal_label.setMinimumSize(230, 230)

        if PORTAL_IMAGE_PATH.exists():
            pix = QPixmap(str(PORTAL_IMAGE_PATH))
        else:
            pix = QPixmap(240, 240); pix.fill(Qt.darkGray)

        img = pix.toImage().convertToFormat(QImage.Format_ARGB32)
        self._base_pix = QPixmap.fromImage(img)
        self._apply_pix(260)
        layout.addStretch()
        layout.addWidget(self.portal_label, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.status_label = QLabel("Initializing…", alignment=Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.hide()
        self.progress.setFixedHeight(25)
        layout.addWidget(self.progress)

        layout.addSpacing(10)

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.setObjectName("secondaryButton")
        self.btn_reset.clicked.connect(self.resetRequested.emit)

        self.btn_toggle = QPushButton("▶ Start")
        self.btn_toggle.setObjectName("mainButton")
        self.btn_toggle.clicked.connect(self.toggleRequested.emit)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.btn_reset)
        row.addWidget(self.btn_toggle)
        row.addStretch()

        layout.addLayout(row)
        layout.addStretch()

    # Anim
    def _setup_animations(self):
        eff = QGraphicsOpacityEffect()
        self.portal_label.setGraphicsEffect(eff)
        self._opacity = QPropertyAnimation(eff, b"opacity")
        self._opacity.setStartValue(0.85)
        self._opacity.setEndValue(1.0)
        self._opacity.setDuration(1600)
        self._opacity.setLoopCount(-1)

        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._opacity)

    def _apply_pix(self, size):
        scaled = self._base_pix.scaled(
            size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.portal_label.setPixmap(scaled)
        self.portal_label.setFixedSize(size, size)

    # Anim control
    def _start_anim(self):
        if self._anim_group.state() == QAbstractAnimation.Stopped:
            self._anim_group.start()

    def _stop_anim(self):
        if self._anim_group.state() != QAbstractAnimation.Stopped:
            self._anim_group.stop()

        eff = self.portal_label.graphicsEffect()
        if eff:
            eff.setOpacity(1.0)

    # UI State
    def set_listening(self, active: bool):
        self._listening = active

        if active:
            self.btn_toggle.setText("⏸ Stop")
            self.set_status("Waiting for arena popup…", "#ffaa00")
            self._start_anim()
        else:
            self.btn_toggle.setText("▶ Resume")
            self.set_status("Listener disabled.", "#ff5555")
            self._stop_anim()
            self.progress.hide()

    def reset_ui(self):
        self.set_status("Waiting for arena popup…", "#ffaa00")
        self.progress.hide()
        self._start_anim() if self._listening else self._stop_anim()

    # Countdown
    def start_countdown_ui(self, seconds: int):
        self.progress.setMaximum(seconds)
        self.progress.setValue(0)
        self.progress.show()

    def update_countdown_ui(self, value: int):
        self.progress.setValue(value)

    def stop_countdown_ui(self, reset_status_to_listening=True):
        self.progress.hide()
        if reset_status_to_listening:
            self.set_listening(self._listening)

    def set_status(self, text, color="#ffaa00"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color:{color};font-weight:600;font-size:15px;"
        )

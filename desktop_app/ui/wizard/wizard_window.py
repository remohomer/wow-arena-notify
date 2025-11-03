# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QIcon
from pathlib import Path
import sys

from ui.style_loader import apply_styles
from infrastructure.config import load_config

from ui.wizard.steps.step_welcome import StepWelcome
from ui.wizard.steps.step_game_folder import StepGameFolder
from ui.wizard.steps.step_android_app import StepAndroidApp
from ui.wizard.steps.step_pairing import StepPairing
from ui.wizard.steps.step_finish import StepFinish

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent))


class WizardWindow(QWidget):
    """
    Onboarding wizard:
      0. Welcome
      1. Game folder
      2. Android app (QR)
      3. Pairing
      4. Finish
    ESC = Back
    """
    finishedSignal = Signal()
    instance = None     # <— singleton

    def __init__(self):
        super().__init__()
        WizardWindow.instance = self   # <— save singleton

        self.setWindowTitle("First-run setup")
        self.setFixedSize(540, 460)
        icon_path = BASE_DIR / "ui" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.cfg = load_config()

        # ---------------- Header
        self.header = QLabel("Welcome", self)
        self.header.setObjectName("wizardHeader")
        self.header.setAlignment(Qt.AlignCenter)

        # ---------------- Progress
        self.progress = QLabel("", self)
        self.progress.setObjectName("wizardProgress")
        self.progress.setAlignment(Qt.AlignCenter)

        # ---------------- Steps
        self.stack = QStackedLayout()
        self.steps = [
            StepWelcome(self),
            StepGameFolder(self),
            StepAndroidApp(self),
            StepPairing(self),
            StepFinish(self),
        ]
        for s in self.steps:
            self.stack.addWidget(s)

        # ---------------- Navigation buttons
        self.btn_back = QPushButton("← Back")
        self.btn_next = QPushButton("Next →")
        self.btn_skip = QPushButton("Skip")

        self.btn_back.clicked.connect(self.on_back)
        self.btn_next.clicked.connect(self.on_next)
        self.btn_skip.clicked.connect(self.on_skip)

        nav = QHBoxLayout()
        nav.addWidget(self.btn_back)
        nav.addStretch()
        nav.addWidget(self.btn_skip)
        nav.addWidget(self.btn_next)

        # ---------------- Layout structure
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 12)
        root.setSpacing(8)
        root.addWidget(self.header)
        root.addWidget(self.progress)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#2b2623;")
        root.addWidget(line)

        content = QWidget()
        content.setLayout(self.stack)
        root.addWidget(content)
        root.addLayout(nav)

        apply_styles(self)

        self.current = 0
        self.update_ui()

        self.installEventFilter(self)

    # ---------- ESC = Back
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.on_back()
            return True
        return super().eventFilter(obj, event)

    # ---------- Step setter
    def set_step(self, i: int):
        i = max(0, min(i, len(self.steps) - 1))
        self.current = i
        self.stack.setCurrentIndex(i)
        self.update_ui()

    # ---------- UI refresher
    def update_ui(self):
        titles = [
            "Welcome",
            "Choose your WoW folder",
            "Install the Android app",
            "Pair your phone",
            "All set!",
        ]

        dots = ["○"] * len(self.steps)
        dots[self.current] = "●"
        self.header.setText(titles[self.current])
        self.progress.setText(" ".join(dots))

        # Back availability
        self.btn_back.setVisible(self.current > 0)

        # Skip available on Android App + Pairing
        self.btn_skip.setVisible(self.current in (2, 3))

        # Hide Next on GAME FOLDER step (auto-advance)
        self.btn_next.setVisible(self.current != 1)

        # Next -> Finish at last
        self.btn_next.setText("Finish" if self.current == len(self.steps)-1 else "Next →")

        step = self.steps[self.current]
        if hasattr(step, "on_enter"):
            step.on_enter()

    # ---------- Navigation
    def on_back(self):
        if self.current > 0:
            self.set_step(self.current - 1)

    def on_next(self):
        step = self.steps[self.current]
        if hasattr(step, "can_continue"):
            ok, msg = step.can_continue()
            if not ok:
                return

        if self.current == len(self.steps) - 1:
            self.finishedSignal.emit()
            return

        self.set_step(self.current + 1)

    def on_skip(self):
        self.set_step(self.current + 1)

    # ---------- public: auto advance
    def auto_next(self, delay_ms=200):
        QTimer.singleShot(delay_ms, lambda: self.on_next())

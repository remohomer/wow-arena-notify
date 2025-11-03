# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QIcon
from pathlib import Path
import sys

from ui.style_loader import apply_styles
from infrastructure.config import load_config, save_config

from ui.wizard.steps.step_welcome import StepWelcome
from ui.wizard.steps.step_game_folder import StepGameFolder
from ui.wizard.steps.step_android_app import StepAndroidApp
from ui.wizard.steps.step_pairing import StepPairing
from ui.wizard.steps.step_test_connection import StepTestConnection
from ui.wizard.steps.step_finish import StepFinish


BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent))


class WizardWindow(QWidget):
    """
    Onboarding wizard:
      0. Welcome
      1. Game folder
      2. Android app (link + QR)
      3. Pairing
      4. Connection test (no arena_pop)
      5. Finish
    ESC = Back
    """
    finishedSignal = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WoW Arena Notify — Setup")
        self.setFixedSize(540, 460)
        icon_path = BASE_DIR / "ui" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.cfg = load_config()

        # header (progress)
        self.header = QLabel("Welcome", self)
        self.header.setObjectName("wizardHeader")
        self.header.setAlignment(Qt.AlignCenter)

        # progress dots
        self.progress = QLabel("● ○ ○ ○ ○ ○", self)
        self.progress.setObjectName("wizardProgress")
        self.progress.setAlignment(Qt.AlignCenter)

        # content stack
        self.stack = QStackedLayout()
        self.steps = [
            StepWelcome(self),
            StepGameFolder(self),
            StepAndroidApp(self),
            StepPairing(self),
            StepTestConnection(self),
            StepFinish(self),
        ]
        for step in self.steps:
            self.stack.addWidget(step)

        # nav buttons
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

        # ESC = Back
        self.installEventFilter(self)

    # ---------- Event filter for ESC
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.on_back()
            return True
        return super().eventFilter(obj, event)

    def set_step(self, idx: int):
        idx = max(0, min(idx, len(self.steps) - 1))
        self.current = idx
        self.stack.setCurrentIndex(idx)
        self.update_ui()

    def update_ui(self):
        titles = [
            "Welcome",
            "Choose your WoW folder",
            "Get the Android app",
            "Pair your phone",
            "Verify connection",
            "All set!",
        ]
        dots = ["○"] * len(self.steps)
        dots[self.current] = "●"
        self.header.setText(titles[self.current])
        self.progress.setText(" ".join(dots))

        # Back availability
        self.btn_back.setEnabled(self.current > 0)

        # Skip: available from step 2 (Android app) w górę
        self.btn_skip.setVisible(self.current >= 2 and self.current < len(self.steps) - 1)

        # Next label change
        self.btn_next.setText("Finish" if self.current == len(self.steps) - 1 else "Next →")

        # allow step to refresh itself
        step = self.steps[self.current]
        if hasattr(step, "on_enter"):
            step.on_enter()

    def on_back(self):
        if self.current > 0:
            self.set_step(self.current - 1)

    def on_next(self):
        # step-level validation hook
        step = self.steps[self.current]
        if hasattr(step, "can_continue"):
            ok, msg = step.can_continue()
            if not ok:
                # step may self-notify UI; we keep it simple
                return
        if self.current == len(self.steps) - 1:
            self.finishedSignal.emit()
            return
        self.set_step(self.current + 1)

    def on_skip(self):
        # allow skipping current step (from 2..n-1)
        self.set_step(self.current + 1)

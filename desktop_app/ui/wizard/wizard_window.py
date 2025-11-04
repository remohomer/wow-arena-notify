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
    Steps:
      0 = Welcome
      1 = WoW folder
      2 = Android app
      3 = Pairing
      4 = All set
    ESC = Back
    """
    finishedSignal = Signal()
    instance = None

    def __init__(self):
        super().__init__()
        WizardWindow.instance = self

        self.setWindowTitle("First-run setup")
        self.setFixedSize(540, 460)
        icon_path = BASE_DIR / "ui" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.cfg = load_config()

        # anti-loop when auto finishing
        self.finish_jump_used = False

        # -------- header
        self.header = QLabel("Welcome", self)
        self.header.setObjectName("wizardHeader")
        self.header.setAlignment(Qt.AlignCenter)

        # -------- progress
        self.progress = QLabel("", self)
        self.progress.setObjectName("wizardProgress")
        self.progress.setAlignment(Qt.AlignCenter)

        # -------- layout stack
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

        # -------- nav buttons
        self.btn_back = QPushButton("← Back")
        self.btn_next = QPushButton("Next →")
        self.btn_skip = QPushButton("I’ll set this up later")

        self.btn_back.clicked.connect(self.on_back)
        self.btn_next.clicked.connect(self.on_next)
        self.btn_skip.clicked.connect(self.on_skip)

        nav = QHBoxLayout()
        nav.addWidget(self.btn_back)
        nav.addStretch()
        nav.addWidget(self.btn_skip)
        nav.addWidget(self.btn_next)

        # -------- root
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

    # -------- ESC = Back
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.on_back()
            return True
        return super().eventFilter(obj, event)

    # ---------------------------------------
    def set_step(self, i: int):
        i = max(0, min(i, len(self.steps) - 1))
        self.current = i
        self.stack.setCurrentIndex(i)
        self.update_ui()

    # ---------------------------------------
    def update_ui(self):
        cfg = load_config()

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

        # Back
        self.btn_back.setVisible(self.current > 0)

        # Skip ONLY on step 3
        self.btn_skip.setVisible(self.current == 3)

        # Next visibility logic:
        if self.current == 1:
            # show NEXT if folder already chosen (when returning)
            has_folder = bool(cfg.get("game_folder"))
            self.btn_next.setVisible(has_folder)
        elif self.current == 3:
            # hide NEXT (pairing auto advances)
            self.btn_next.setVisible(False)
        else:
            self.btn_next.setVisible(True)

        # Next -> Finish
        self.btn_next.setText("Finish" if self.current == len(self.steps)-1 else "Next →")

        step = self.steps[self.current]
        if hasattr(step, "on_enter"):
            step.on_enter()

    # ---------------------------------------
    def on_back(self):
        if self.current > 0:
            self.set_step(self.current - 1)

    def on_next(self):
        step = self.steps[self.current]
        if hasattr(step, "can_continue"):
            ok, msg = step.can_continue()
            if not ok:
                return

        # finish
        if self.current == len(self.steps) - 1:
            self.finishedSignal.emit()
            return

        self.set_step(self.current + 1)

    def on_skip(self):
        # skip pairing → final
        self.set_step(4)

    # ---------------------------------------
    # NORMAL auto advance (+1)
    def auto_next_normal(self, delay_ms=300):
        QTimer.singleShot(delay_ms, lambda: self.set_step(self.current + 1))

    # FINISH auto-advance (pairing)
    def auto_finish_once(self, delay_ms=900):
        if self.finish_jump_used:
            return
        self.finish_jump_used = True
        QTimer.singleShot(delay_ms, lambda: self.set_step(4))

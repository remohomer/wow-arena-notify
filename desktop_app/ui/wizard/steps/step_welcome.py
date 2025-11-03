# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class StepWelcome(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(12)

        title = QLabel("👋 Welcome to WoW Arena Notify")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:800;")

        desc = QLabel(
            "We’ll take less than a minute:\n\n"
            "• Pick your WoW folder\n"
            "• Install mobile app\n"
            "• Pair your phone\n"
            "• You’re done!"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#c9bda7;")

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(desc)
        lay.addStretch()

    def can_continue(self):
        return True, ""

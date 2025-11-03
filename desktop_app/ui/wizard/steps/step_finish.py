# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class StepFinish(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(12)

        title = QLabel("You’re all set! 🎉")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:800;")

        desc = QLabel(
            "You can re-pair or test connection anytime\n"
            "from the Pairing tab.\n\n"
            "Good luck in arenas!"
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

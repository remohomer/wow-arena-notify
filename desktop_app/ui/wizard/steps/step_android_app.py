# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtCore import QUrl
from infrastructure.logger import logger

PLAY_URL = "https://play.google.com/store/apps/details?id=pl.remoh.wowarenanotify"

class StepAndroidApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(14)

        title = QLabel("Install the Android app")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:800;")

        desc = QLabel(
            "The phone app receives arena notifications and shows the countdown.\n"
            "Install it now to continue."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#c9bda7;")

        # Link button
        btn = QPushButton("Open Google Play")
        btn.setFixedHeight(36)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PLAY_URL)))

        # Optional QR (bez zależności — placeholder jako link tekstowy / albo własny obrazek)
        hint = QLabel(f"<a href='{PLAY_URL}'>Play Store link</a>")
        hint.setOpenExternalLinks(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#ffaa00;")

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(desc)
        lay.addWidget(btn, alignment=Qt.AlignCenter)
        lay.addWidget(hint)
        lay.addStretch()

    def can_continue(self):
        return True, ""

    def on_enter(self):
        # nic — zostawiamy możliwość Skip
        pass

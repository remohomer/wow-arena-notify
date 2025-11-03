# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
import qrcode
from io import BytesIO

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

        desc = QLabel("Scan QR or click the button below.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#c9bda7;")

        btn = QPushButton("Open Google Play")
        btn.setFixedHeight(36)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PLAY_URL)))

        # QR
        qr = qrcode.QRCode(box_size=3, border=2)
        qr.add_data(PLAY_URL)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())

        qr_label = QLabel()
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(desc)
        lay.addWidget(qr_label)
        lay.addWidget(btn, alignment=Qt.AlignCenter)
        lay.addStretch()

    def can_continue(self):
        return True, ""

# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtCore import QUrl
import pyperclip
from pathlib import Path
import qrcode
from io import BytesIO


PLAY_URL = "https://play.google.com/store/apps/details?id=pl.remoh.wowarenanotify"


class DownloadAppDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Get the Android app")
        self.setFixedSize(340, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(16)

        title = QLabel("Download Android App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:800;")
        layout.addWidget(title)

        # QR
        pix = self.generate_qr()
        qr_label = QLabel()
        qr_label.setPixmap(pix)
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)

        link_label = QLabel(f"<a href='{PLAY_URL}'>{PLAY_URL}</a>")
        link_label.setOpenExternalLinks(True)
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setStyleSheet("color:#ffaa00;")
        layout.addWidget(link_label)

        # Copy button
        btn_copy = QPushButton("📋 Copy link")
        btn_copy.setFixedHeight(36)
        btn_copy.clicked.connect(self.copy_link)
        layout.addWidget(btn_copy, alignment=Qt.AlignCenter)

        # Close
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(36)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)

    def generate_qr(self):
        qr = qrcode.QRCode(box_size=5, border=2)
        qr.add_data(PLAY_URL)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        return pix

    def copy_link(self):
        pyperclip.copy(PLAY_URL)

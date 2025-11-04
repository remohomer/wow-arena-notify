# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCursor
import pyperclip
from services import pairing
from ui.dialogs.pair_device import PairDeviceDialog
from ui.dialogs import test_connection
from ui.dialogs.download_app_dialog import DownloadAppDialog


def mask(text):
    if len(text) <= 10:
        return text
    return f"{text[:6]}…{text[-4:]}"


class PairingTab(QWidget):
    deviceChanged = Signal()   # <— notify main window

    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_device = False
        self.show_desktop = False
        self.toast = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 24, 36, 24)
        self.layout.setSpacing(22)

        # Title badge + subtitle
        self.label_status = QLabel()
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet("font-size:18px; font-weight:800;")
        self.layout.addWidget(self.label_status)

        self.label_subtitle = QLabel("Securely connect your Android app to this desktop.")
        self.label_subtitle.setAlignment(Qt.AlignCenter)
        self.label_subtitle.setStyleSheet("color:#b9b1ad; font-size:12px;")
        self.layout.addWidget(self.label_subtitle)

        # Card
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color:#2e2723;
                border-radius:14px;
                border:1px solid #3b3430;
            }
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(18)

        # ======================= DEVICE =======================
        self.device_edit = QLineEdit()
        self.device_edit.setReadOnly(True)
        self.device_edit.setCursorPosition(0)
        self.device_edit.mousePressEvent = lambda e: self.copy(self.device_id)
        self.device_edit.setStyleSheet("""
            QLineEdit {
                background:#3a332f;
                border-radius:8px;
                color:#ddd;
                padding:4px 6px;
            }
        """)

        self.btn_device_copy = QPushButton("📋 Copy")
        self.btn_device_copy.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_device_copy.setFixedHeight(28)
        self.btn_device_copy.clicked.connect(lambda: self.copy(self.device_id))
        self.btn_device_copy.setStyleSheet("font-weight:600; padding:2px 8px;")

        self.btn_device_toggle = QPushButton("👁 Show")
        self.btn_device_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_device_toggle.setFixedHeight(28)
        self.btn_device_toggle.clicked.connect(self.toggle_device)
        self.btn_device_toggle.setStyleSheet("padding:2px 8px;")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("<b style='color:#ffaa00;'>Device ID:</b>"))
        row1.addStretch()
        card_layout.addLayout(row1)

        row1b = QHBoxLayout()
        row1b.addWidget(self.device_edit)
        row1b.addWidget(self.btn_device_copy)
        row1b.addWidget(self.btn_device_toggle)
        card_layout.addLayout(row1b)

        # ======================= DESKTOP =======================
        self.desktop_edit = QLineEdit()
        self.desktop_edit.setReadOnly(True)
        self.desktop_edit.setCursorPosition(0)
        self.desktop_edit.mousePressEvent = lambda e: self.copy(self.desktop_id)
        self.desktop_edit.setStyleSheet("""
            QLineEdit {
                background:#3a332f;
                border-radius:8px;
                color:#ddd;
                padding:4px 6px;
            }
        """)

        self.btn_desktop_copy = QPushButton("📋 Copy")
        self.btn_desktop_copy.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_desktop_copy.setFixedHeight(28)
        self.btn_desktop_copy.clicked.connect(lambda: self.copy(self.desktop_id))
        self.btn_desktop_copy.setStyleSheet("font-weight:600; padding:2px 8px;")

        self.btn_desktop_toggle = QPushButton("👁 Show")
        self.btn_desktop_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_desktop_toggle.setFixedHeight(28)
        self.btn_desktop_toggle.clicked.connect(self.toggle_desktop)
        self.btn_desktop_toggle.setStyleSheet("padding:2px 8px;")

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("<b style='color:#ffaa00;'>Desktop ID:</b>"))
        row2.addStretch()
        card_layout.addLayout(row2)

        row2b = QHBoxLayout()
        row2b.addWidget(self.desktop_edit)
        row2b.addWidget(self.btn_desktop_copy)
        row2b.addWidget(self.btn_desktop_toggle)
        card_layout.addLayout(row2b)

        # Helper text for unpaired state
        self.helper_label = QLabel("Install the Android app and tap Pair to connect.")
        self.helper_label.setAlignment(Qt.AlignCenter)
        self.helper_label.setStyleSheet("color:#b9b1ad; font-size:12px;")
        card_layout.addWidget(self.helper_label)

        self.layout.addWidget(self.card)
        self.layout.addStretch()

        # ---------- Buttons ----------
        row_top = QHBoxLayout()
        row_top.addStretch()

        self.btn_pair = QPushButton()
        self.btn_pair.setFixedHeight(40)
        self.btn_pair.clicked.connect(self.on_pair_click)

        self.btn_test = QPushButton("📡 Test connection")
        self.btn_test.setFixedHeight(40)
        self.btn_test.clicked.connect(lambda: test_connection.run_test(self))

        row_top.addWidget(self.btn_pair)
        row_top.addSpacing(16)
        row_top.addWidget(self.btn_test)
        row_top.addStretch()
        self.layout.addLayout(row_top)

        row_bottom = QHBoxLayout()
        row_bottom.addStretch()

        self.btn_download = QPushButton("📱 Android app")
        self.btn_download.setFixedHeight(40)
        self.btn_download.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_download.clicked.connect(self.open_download)

        row_bottom.addWidget(self.btn_download)
        row_bottom.addStretch()
        self.layout.addLayout(row_bottom)

        self.refresh_ui()

    # ======================================================================
    def refresh_ui(self):
        status = pairing.get_pairing_status()
        self.desktop_id = status.get("desktop_id", "")
        self.device_id = status.get("device_id", "")

        if status["paired"]:
            self.label_status.setText("✅ <span style='color:#77ff77;'>DEVICE CONNECTED</span>")
            self.btn_pair.setText("🗑 Unpair")
            self.btn_pair.setStyleSheet("""
                QPushButton {
                    background-color:#c0392b; color:white;
                    font-weight:700; border-radius:8px;
                    padding:0 18px;
                }
                QPushButton:hover { background:#e74c3c; }
            """)

            self.device_edit.setText(self.device_id if self.show_device else mask(self.device_id))
            self.desktop_edit.setText(self.desktop_id if self.show_desktop else mask(self.desktop_id))

            self.btn_device_toggle.setText("👁 Show" if not self.show_device else "🙈 Hide")
            self.btn_desktop_toggle.setText("👁 Show" if not self.show_desktop else "🙈 Hide")

            self.helper_label.hide()

        else:
            self.label_status.setText("❌ <span style='color:#ff7777;'>NO DEVICE PAIRED</span>")
            self.btn_pair.setText("🔗 Pair device")
            self.device_edit.setText("")
            self.desktop_edit.setText(mask(self.desktop_id))
            self.btn_device_toggle.setText("👁 Show")
            self.btn_desktop_toggle.setText("👁 Show")
            self.helper_label.show()

    # ======================================================================
    def toggle_device(self):
        self.show_device = not self.show_device
        self.refresh_ui()

    def toggle_desktop(self):
        self.show_desktop = not self.show_desktop
        self.refresh_ui()

    # ======================================================================
    def copy(self, text):
        pyperclip.copy(text)
        self.toast_msg("📋 Copied!")

    # ======================================================================
    def toast_msg(self, msg):
        if self.toast:
            self.toast.deleteLater()

        self.toast = QLabel(msg, self)
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.setStyleSheet("""
            QLabel {
                background-color:#000000bb;
                color:white;
                border-radius:8px;
                padding:6px 14px;
                font-weight:600;
            }
        """)
        self.toast.adjustSize()
        self.toast.move(
            (self.width() - self.toast.width()) // 2,
            self.height() - 98
        )
        self.toast.show()
        QTimer.singleShot(1400, lambda: self.toast.hide())

    # ======================================================================
    def on_pair_click(self):
        status = pairing.get_pairing_status()

        if status["paired"]:
            pairing.unpair_device()
            self.show_device = False
            self.show_desktop = False

            # ✅ immediate refresh
            self.refresh_ui()
            self.deviceChanged.emit()

            try:
                self.parent().refresh_status_bar()
            except:
                pass
            return

        dlg = PairDeviceDialog(self)
        dlg.exec()
        QTimer.singleShot(300, self.refresh_ui)
        QTimer.singleShot(300, lambda: self.deviceChanged.emit())

    # ======================================================================
    def open_download(self):
        dlg = DownloadAppDialog(self)
        dlg.exec()

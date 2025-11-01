# file: desktop_app/ui/tabs/pairing_tab.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSpacerItem, QSizePolicy, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
import pyperclip
from services import pairing
from ui.dialogs.pair_device import PairDeviceDialog
from ui.dialogs import test_connection


def mask(text):
    if len(text) <= 10:
        return text
    return f"{text[:6]}…{text[-4:]}"


class PairingTab(QWidget):
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

        # Title badge
        self.label_status = QLabel()
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet("font-size:18px; font-weight:800;")
        self.layout.addWidget(self.label_status)

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
        card_layout.setSpacing(16)

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

        self.device_actions = QLabel()
        self.device_actions.setCursor(QCursor(Qt.PointingHandCursor))
        self.device_actions.mousePressEvent = lambda e: self.toggle_device()
        self.device_actions.setStyleSheet("color:#ffaa00; font-size:12px;")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("<b style='color:#ffaa00;'>Device ID:</b>"))
        row1.addStretch()
        card_layout.addLayout(row1)

        row1b = QHBoxLayout()
        row1b.addWidget(self.device_edit)
        row1b.addWidget(self.device_actions)
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

        self.desktop_actions = QLabel()
        self.desktop_actions.setCursor(QCursor(Qt.PointingHandCursor))
        self.desktop_actions.mousePressEvent = lambda e: self.toggle_desktop()
        self.desktop_actions.setStyleSheet("color:#ffaa00; font-size:12px;")

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("<b style='color:#ffaa00;'>Desktop ID:</b>"))
        row2.addStretch()
        card_layout.addLayout(row2)

        row2b = QHBoxLayout()
        row2b.addWidget(self.desktop_edit)
        row2b.addWidget(self.desktop_actions)
        card_layout.addLayout(row2b)

        self.layout.addWidget(self.card)
        self.layout.addStretch()

        # Bottom buttons
        self.btn_pair = QPushButton()
        self.btn_pair.setFixedHeight(42)
        self.btn_pair.clicked.connect(self.on_pair_click)

        self.btn_test = QPushButton("📡 Test connection")
        self.btn_test.setFixedHeight(42)
        self.btn_test.clicked.connect(lambda: test_connection.run_test(self))

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.btn_pair)
        row.addWidget(self.btn_test)
        row.addStretch()
        self.layout.addLayout(row)

        self.refresh_ui()

    # ======================================================================
    def refresh_ui(self):
        status = pairing.get_pairing_status()
        self.desktop_id = status.get("desktop_id", "")
        self.device_id = status.get("device_id", "")

        if status["paired"]:
            self.label_status.setText("✅ <span style='color:#77ff77;'>DEVICE CONNECTED</span>")
            self.btn_pair.setText("🗑 Unpair device")
            self.btn_pair.setStyleSheet("""
                QPushButton {
                    background-color:#c0392b; color:white;
                    font-weight:700; border-radius:8px;
                }
                QPushButton:hover { background:#e74c3c; }
            """)

            self.device_edit.setText(self.device_id if self.show_device else mask(self.device_id))
            self.desktop_edit.setText(self.desktop_id if self.show_desktop else mask(self.desktop_id))

            self.device_actions.setText("👁 Show" if not self.show_device else "🙈 Hide")
            self.desktop_actions.setText("👁 Show" if not self.show_desktop else "🙈 Hide")

        else:
            self.label_status.setText("❌ <span style='color:#ff7777;'>NO DEVICE PAIRED</span>")
            self.btn_pair.setText("🔗 Pair device (QR)")
            self.device_edit.setText("")
            self.desktop_edit.setText(mask(self.desktop_id))
            self.device_actions.setText("")
            self.desktop_actions.setText("")

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
            self.refresh_ui()
        else:
            dlg = PairDeviceDialog(self)
            dlg.exec()
            QTimer.singleShot(300, self.refresh_ui)

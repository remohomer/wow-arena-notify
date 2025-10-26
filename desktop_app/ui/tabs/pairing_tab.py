# ui/tabs/pairing_tab.py — v3 (2025-10-27)
# ✅ Uses PairDeviceDialog (pure UI)
# ✅ Calls core.pairing for unpair/status

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer
from core import pairing
from ui.dialogs.pair_device import PairDeviceDialog
from ui.dialogs import test_connection


class PairingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        self.label_status = QLabel()
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet("font-size:13px; font-weight:600;")

        self.btn_pair = QPushButton()
        self.btn_pair.clicked.connect(self.on_pair_click)

        self.btn_test = QPushButton("📡 Test connection")
        self.btn_test.clicked.connect(lambda: test_connection.run_test(self))

        row = QHBoxLayout()
        row.addWidget(self.btn_pair)
        row.addWidget(self.btn_test)

        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(row)
        layout.addWidget(self.label_status)
        layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.refresh_ui()

    def refresh_ui(self):
        status = pairing.get_pairing_status()
        desktop_id = status.get("desktop_id", "unknown")

        if status["paired"]:
            self.btn_pair.setText("🗑 Unpair device")
            self.btn_pair.setStyleSheet("background-color:#f44336; color:white; font-weight:bold;")
            device_id = status.get("device_id", "unknown")
            pairing_id = status.get("pairing_id", "unknown")
            self.label_status.setText(
                f"✅ Paired\n📱 Device ID: {device_id}\n💻 Desktop ID: {desktop_id}\n🔗 Pairing ID: {pairing_id}"
            )
            self.label_status.setStyleSheet("color:#4cff4c; font-size:13px; font-weight:600;")
        else:
            self.btn_pair.setText("🔗 Pair device (QR)")
            self.btn_pair.setStyleSheet("background-color:#4CAF50; color:white; font-weight:bold;")
            self.label_status.setText(f"❌ No device paired\n💻 Desktop ID: {desktop_id}")
            self.label_status.setStyleSheet("color:#ff7777; font-size:13px; font-weight:600;")

    def on_pair_click(self):
        status = pairing.get_pairing_status()

        if status["paired"]:
            pairing.unpair_device()
            self.refresh_ui()
        else:
            dlg = PairDeviceDialog(self)
            dlg.exec()
            QTimer.singleShot(300, self.refresh_ui)

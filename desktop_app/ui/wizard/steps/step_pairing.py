# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from ui.dialogs.pair_device import PairDeviceDialog
from services import pairing

class StepPairing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._poll = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(14)

        title = QLabel("Pair your phone")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:800;")

        self.state = QLabel("Click the button below and scan the QR code with the Android app.")
        self.state.setAlignment(Qt.AlignCenter)
        self.state.setWordWrap(True)
        self.state.setStyleSheet("color:#c9bda7;")

        self.btn = QPushButton("Start pairing (QR)")
        self.btn.setFixedHeight(38)
        self.btn.clicked.connect(self.open_pair_dialog)

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(self.state)
        lay.addWidget(self.btn, alignment=Qt.AlignCenter)
        lay.addStretch()

        # small poll timer to update state
        self._poll = QTimer(self)
        self._poll.setInterval(800)
        self._poll.timeout.connect(self._refresh_status)
        self._poll.start()

    def _refresh_status(self):
        status = pairing.get_pairing_status()
        if status.get("paired"):
            self.state.setText("✅ Paired successfully! You can proceed.")
        else:
            self.state.setText("Waiting for pairing…")

    def open_pair_dialog(self):
        dlg = PairDeviceDialog(self)
        dlg.exec()

    def can_continue(self):
        status = pairing.get_pairing_status()
        if status.get("paired"):
            return True, ""
        self.state.setText("<b style='color:#ff7777'>Device not paired yet.</b>")
        return False, "Not paired"

    def on_enter(self):
        self._refresh_status()

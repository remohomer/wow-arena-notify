# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from ui.dialogs.pair_device import PairDeviceDialog
from services import pairing

class StepPairing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._poll = QTimer(self)
        self._poll.setInterval(700)
        self._poll.timeout.connect(self._refresh)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(14)

        title = QLabel("Pair your phone")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:800;")

        self.state = QLabel("Click below and scan the QR in the app.")
        self.state.setAlignment(Qt.AlignCenter)
        self.state.setWordWrap(True)
        self.state.setStyleSheet("color:#c9bda7;")

        self.btn = QPushButton("Start pairing (QR)")
        self.btn.setFixedHeight(38)
        self.btn.clicked.connect(self.open)

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(self.state)
        lay.addWidget(self.btn, alignment=Qt.AlignCenter)
        lay.addStretch()

    def open(self):
        dlg = PairDeviceDialog(self)
        dlg.exec()

    def _refresh(self):
        status = pairing.get_pairing_status()
        if status.get("paired"):
            self.state.setText("✅ Paired!")
            # auto advance gently
            self._poll.stop()
            QTimer.singleShot(600, self.parent().go_next)
        else:
            self.state.setText("Waiting for pairing…")

    def can_continue(self):
        return pairing.get_pairing_status().get("paired"), "Not paired"

    def on_enter(self):
        self._poll.start()

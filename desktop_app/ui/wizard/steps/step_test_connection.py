# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from infrastructure.logger import logger
from ui.dialogs import test_connection

class StepTestConnection(QWidget):
    """
    Weryfikacja połączenia BEZ arena_pop.
    Korzysta z istniejącego dialogu: ui.dialogs.test_connection.run_test(self)
    i oczekuje na wynik (log + ewentualne okno).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ok = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(14)

        title = QLabel("Verify the connection")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:800;")

        self.state = QLabel(
            "We’ll send a light test signal to your phone to verify that push + RTDB are working.\n"
            "No arena events involved."
        )
        self.state.setAlignment(Qt.AlignCenter)
        self.state.setWordWrap(True)
        self.state.setStyleSheet("color:#c9bda7;")

        self.btn = QPushButton("Run connection test")
        self.btn.setFixedHeight(38)
        self.btn.clicked.connect(self._run_test)

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(self.state)
        lay.addWidget(self.btn, alignment=Qt.AlignCenter)
        lay.addStretch()

    def _run_test(self):
        try:
            test_connection.run_test(self)  # używamy Twojego istniejącego testu
            self._ok = True
            self.state.setText("✅ Connection verified!")
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self._ok = False
            self.state.setText("<b style='color:#ff7777'>Test failed. Try again or Skip.</b>")

    def can_continue(self):
        # Pozwalamy przejść dalej także jeśli user nie wykonał testu → można użyć Skip z paska
        # ale Next blokujemy jeżeli nie ma _ok. Skip jest odblokowany w wizardzie od tego kroku.
        if self._ok:
            return True, ""
        # miękka blokada — użytkownik może kliknąć Skip
        self.state.setText("<span style='color:#ffd166'>You can Skip and run the test later in Pairing tab.</span>")
        return False, "Not verified yet"

    def on_enter(self):
        # resetujemy status przy wejściu
        self._ok = False
        self.state.setText(
            "We’ll send a light test signal to your phone to verify that push + RTDB are working.\n"
            "No arena events involved."
        )

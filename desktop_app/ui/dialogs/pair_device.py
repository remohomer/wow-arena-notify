# file: desktop_app/ui/dialogs/pair_device.py
import json
import qrcode
import tempfile
import threading
import pyperclip
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QFont
from services import pairing
from infrastructure.logger import logger


class PairDeviceDialog(QDialog):
    success_signal = Signal()  # <-- 🔥 sygnał emitowany z worker thread

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pair Your Device")
        self.setFixedSize(360, 520)
        self.setWindowModality(Qt.ApplicationModal)

        self.stop_flag = threading.Event()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(12)

        self.success_signal.connect(self.on_success)  # <-- odbiór sygnału

        # --- Generate pairing info ---
        self.pairing_id, self.device_url = pairing.create_pairing_entry()
        logger.info(f"🔍 Waiting for pairing: {self.pairing_id}")

        # --- Build UI ---
        self.init_ui()
        self.start_polling()

    def init_ui(self):
        tmp = Path(tempfile.gettempdir()) / "wow_pair_qr.png"
        qrcode.make(json.dumps({"pid": self.pairing_id})).save(tmp)

        lbl = QLabel()
        lbl.setPixmap(QPixmap(str(tmp)).scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl.setAlignment(Qt.AlignCenter)

        info = QLabel(
            "📱 Scan this QR code in the WoW Arena Notify mobile app.\n\n"
            "Or enter the code below manually if QR scanning is not available."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color:#bbb;")

        code_label = QLabel(self.pairing_id)
        code_label.setFont(QFont("Consolas", 10, QFont.Bold))
        code_label.setAlignment(Qt.AlignCenter)
        code_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        copy_btn = QPushButton("📋 Copy Code")
        copy_btn.setFixedHeight(36)
        copy_btn.setStyleSheet("QPushButton { font-weight:600; }")
        copy_btn.clicked.connect(lambda: pyperclip.copy(self.pairing_id))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()

        self.progress = QProgressBar()
        self.progress.setRange(0, 60)
        self.progress.setValue(60)
        self.progress.setTextVisible(True)
        self.progress.setFormat("⏱ %v s remaining")
        self.progress.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(lbl)
        self.layout.addWidget(info)
        self.layout.addSpacing(6)
        self.layout.addWidget(QLabel("<b>Manual pairing code:</b>", alignment=Qt.AlignCenter))
        self.layout.addWidget(code_label)
        self.layout.addLayout(btn_row)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.progress)

        QTimer.singleShot(1000, self.update_timer)

    def update_timer(self):
        if self.stop_flag.is_set():
            return
        val = self.progress.value() - 1
        if val >= 0:
            self.progress.setValue(val)
            QTimer.singleShot(1000, self.update_timer)
        else:
            self.stop_flag.set()
            logger.warning("⏰ Pairing timed out.")
            self.reject()

    def start_polling(self):
        def worker():
            device_id, device_secret = pairing.poll_for_device(self.device_url, self.stop_flag)
            if device_id and device_secret:
                pairing.finalize_pairing(self.pairing_id, device_id, device_secret)
                logger.info("💫 Emitting success signal to GUI thread")
                self.success_signal.emit()  # <-- tu był invokeMethod
            else:
                logger.info("⚠ Pairing failed or timed out")
                QTimer.singleShot(0, self.reject)

        threading.Thread(target=worker, daemon=True).start()

    def on_success(self):
        self.stop_flag.set()
        logger.dev("✅ Device paired successfully — closing dialog.")
        self.accept()  # 🔥 natywne zamknięcie dialogu

    def closeEvent(self, event):
        self.stop_flag.set()
        return super().closeEvent(event)

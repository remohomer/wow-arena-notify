# file: desktop_app/ui/toast.py
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont


class Toast(QLabel):
    def __init__(self, parent, text: str, duration_ms=2200):
        super().__init__(parent)

        self.setText(text)
        self.setStyleSheet("""
            background-color: rgba(20, 20, 20, 205);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.15);
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Segoe UI", 9))
        self.adjustSize()
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # position bottom-center
        parent_w = parent.width()
        parent_h = parent.height()
        x = (parent_w - self.width()) // 2
        y = parent_h - self.height() - 35
        self.move(QPoint(x, y))
        self.show()

        # autohide
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.setSingleShot(True)
        self.timer.start(duration_ms)

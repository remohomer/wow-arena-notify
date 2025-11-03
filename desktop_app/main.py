# file: desktop_app/main.py
import sys
import socket
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow
from infrastructure.logger import logger


class SingleInstance:
    """Zapobiega uruchomieniu wielu instancji aplikacji."""
    def __init__(self, port: int = 54321):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = False
        try:
            self.sock.bind(("127.0.0.1", port))
            self.sock.listen(1)
        except OSError:
            self.is_running = True

    def __del__(self):
        try:
            self.sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    instance = SingleInstance()
    if instance.is_running:
        QMessageBox.warning(None, "WoW Arena Notify", "⚠ Program jest już uruchomiony.")
        sys.exit(0)

    app = QApplication(sys.argv)

    # 🖼️ Ikona aplikacji
    icon_path = Path("icon.ico")
    if not icon_path.exists():
        alt_path = Path.cwd() / "ui" / "icon.ico"
        if alt_path.exists():
            icon_path = alt_path
    app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    logger.dev("🚀 Application started.")
    sys.exit(app.exec())

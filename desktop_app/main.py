import sys
import socket
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from ui.wizard.wizard_window import WizardWindow

from infrastructure.logger import logger
from infrastructure.config import load_config, save_config


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

    # Ikona aplikacji
    icon_path = Path("icon.ico")
    if not icon_path.exists():
        alt_path = Path.cwd() / "ui" / "icon.ico"
        if alt_path.exists():
            icon_path = alt_path
    app.setWindowIcon(QIcon(str(icon_path)))

    cfg = load_config()

    def start_main():
        window = MainWindow()
        window.show()
        logger.dev("🚀 Application started.")
        sys.exit(app.exec())

    if cfg.get("first_run", True):
        wizard = WizardWindow()
        # po sukcesie lub skipie → ustaw first_run False i startuj main
        def _finish_and_start():
            cfg["first_run"] = False
            save_config(cfg)
            wizard.close()
            start_main()
        wizard.finishedSignal.connect(_finish_and_start)
        wizard.show()
        sys.exit(app.exec())
    else:
        start_main()

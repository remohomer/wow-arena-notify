import sys
import socket
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from ui.wizard.wizard_window import WizardWindow

from infrastructure.logger import logger
from infrastructure.config import load_config, save_config

# GLOBAL references (do NOT add "global" here)
main_window = None
wizard = None


class SingleInstance:
    def __init__(self, port: int = 54321):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = False
        try:
            self.sock.bind(("127.0.0.1", port))
            self.sock.listen(1)
        except OSError:
            self.is_running = True


if __name__ == "__main__":
    instance = SingleInstance()
    if instance.is_running:
        QMessageBox.warning(None, "WoW Arena Notify", "⚠ Program jest już uruchomiony.")
        sys.exit(0)

    app = QApplication(sys.argv)

    icon_path = Path("icon.ico")
    if not icon_path.exists():
        icon_path = Path.cwd() / "ui" / "icon.ico"
    app.setWindowIcon(QIcon(str(icon_path)))

    cfg = load_config()

    def show_main():
        global main_window
        main_window = MainWindow()
        main_window.show()
        logger.dev("🚀 Application started.")

    if cfg.get("first_run", True):
        wizard_local = WizardWindow()

        def _finish_and_start():
            cfg["first_run"] = False
            save_config(cfg)

            wizard_local.hide()
            QTimer.singleShot(50, show_main)

        wizard_local.finishedSignal.connect(_finish_and_start)
        wizard_local.show()

    else:
        show_main()

    sys.exit(app.exec())

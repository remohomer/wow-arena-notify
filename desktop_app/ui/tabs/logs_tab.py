# ui/tabs/logs_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from core.logger import logger


class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.log_view = QPlainTextEdit(readOnly=True)
        self.log_view.setStyleSheet(
            "background-color:#111; color:#0f0; font-family:Consolas; font-size:12px;"
        )
        layout.addWidget(self.log_view)

        if hasattr(logger, "qt_handler"):
            logger.qt_handler.emitter.new_log.connect(self.append_log)

    def append_log(self, message: str):
        self.log_view.appendPlainText(message)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

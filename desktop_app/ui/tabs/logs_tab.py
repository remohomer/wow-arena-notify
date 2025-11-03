# file: desktop_app/ui/tabs/logs_tab.py
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import QTimer
from infrastructure.logger import logger

# small startup buffer (filled before UI connects)
_startup_buffer = []
_BUFFER_LIMIT = 200


class LogsTab(QWidget):
    """
    Colored log viewer:
      - INFO/USER → green
      - [DEV]     → light blue
      - WARNING   → yellow
      - ERROR     → red
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.log_view = QTextEdit(readOnly=True)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color:#0b0b0b;
                color:#ddd;
                font-family: Consolas, 'Fira Code', monospace;
                font-size: 12px;
                border: 1px solid #222;
            }
        """)
        layout.addWidget(self.log_view)

        # delayed connection to logger
        QTimer.singleShot(50, self._connect_logger)

        # monkey-patch logger handler to buffer until connected
        if hasattr(logger, "qt_handler"):
            orig_emit = logger.qt_handler.emit

            def buffered_emit(record):
                msg = logger.qt_handler.format(record)

                # if UI not connected yet → buffer
                if not getattr(logger.qt_handler, "_connected", False):
                    _startup_buffer.append(msg)
                    if len(_startup_buffer) > _BUFFER_LIMIT:
                        _startup_buffer.pop(0)

                try:
                    orig_emit(record)
                except Exception:
                    pass

            logger.qt_handler.emit = buffered_emit

    def _connect_logger(self):
        if hasattr(logger, "qt_handler"):
            logger.qt_handler.emitter.new_log.connect(self.append_log)
            logger.qt_handler._connected = True
            logger.dev("LogsTab connected to logger")

            # flush buffered lines
            for msg in _startup_buffer:
                self.append_log(msg)
            _startup_buffer.clear()
        else:
            logger.dev("LogsTab: qt_handler missing!")

    def append_log(self, message: str):
        # determine color
        m = message.upper()

        # default green for normal logs (INFO/user)
        color = "#7CFC00"

        if "[DEV]" in m:
            color = "#56B6C2"  # light cyan
        elif "[WARNING]" in m or "[WARN]" in m:
            color = "#E5C07B"  # warm yellow
        elif "[ERROR]" in m or "[CRITICAL]" in m or "❌" in m:
            color = "#FF5555"  # red error

        # escape HTML entities
        safe = (
            message.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
        )

        self.log_view.append(f'<span style="color:{color}">{safe}</span>')
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

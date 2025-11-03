# -*- coding: utf-8 -*-
"""
Minimal logger with:
 - File rotation
 - Console output
 - Qt handler to Logs tab
 - .user() and .dev() helpers for compatibility
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import os
from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
    new_log = Signal(str)

class QtLogHandler(logging.Handler):
    """Emits formatted log lines to the GUI (Logs tab) via Qt signal."""
    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()

    def emit(self, record):
        try:
            msg = self.format(record)
            self.emitter.new_log.emit(msg)
        except Exception:
            pass


def get_logs_dir() -> Path:
    local_appdata = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local"))
    logs_dir = local_appdata / "WoWArenaNotify" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _get_log_level() -> int:
    lvl = os.getenv("WOWAN_LOG_LEVEL", "INFO").upper().strip()
    return {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }.get(lvl, logging.INFO)


def setup_logger() -> logging.Logger:
    log_dir = get_logs_dir()
    log_file = log_dir / "wow_arena.log"

    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("WoWArenaNotify")
    logger.setLevel(_get_log_level())

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    qt_handler = QtLogHandler()
    qt_handler.setFormatter(formatter)
    logger.addHandler(qt_handler)
    logger.qt_handler = qt_handler

    logger.propagate = False

    # --- restore compatibility helpers ---
    def user(msg: str):
        logger.info(f"{msg}")

    def dev(msg: str):
        logger.debug(f"[DEV] {msg}")

    logger.user = user
    logger.dev = dev
    # --------------------------------------

    logger.info(f"🪵 Logging started → {log_file}")
    return logger


logger = setup_logger()

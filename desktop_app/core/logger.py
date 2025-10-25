import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import os
from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
    new_log = Signal(str)

class QtLogHandler(logging.Handler):
    """Handler emitujący logi do GUI (zakładka Logs)."""
    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()

    def emit(self, record):
        msg = self.format(record)
        self.emitter.new_log.emit(msg)

def get_logs_dir() -> Path:
    """Zwraca folder logów w AppData\\Local\\WoWArenaNotify\\logs (tworzy, jeśli nie istnieje)."""
    local_appdata = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local"))
    logs_dir = local_appdata / "WoWArenaNotify" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def _get_log_level() -> int:
    """Pozwala nadpisać poziom logów zmienną środowiskową WOWAN_LOG_LEVEL (DEBUG/INFO/WARNING/ERROR)."""
    lvl = os.getenv("WOWAN_LOG_LEVEL", "INFO").upper().strip()
    return {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }.get(lvl, logging.INFO)

def setup_logger() -> logging.Logger:
    """Konfiguruje logger z rotacją i handlerem GUI."""
    log_dir = get_logs_dir()
    log_file = log_dir / "wow_arena.log"

    # 🔁 Rotacja dzienna
    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # 🔹 Logger główny
    logger = logging.getLogger("WoWArenaNotify")
    logger.setLevel(_get_log_level())
    if logger.hasHandlers():
        logger.handlers.clear()

    # 📂 Zapis do pliku
    logger.addHandler(file_handler)

    # 🖥️ Konsola (debug)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 🪟 GUI handler
    qt_handler = QtLogHandler()
    qt_handler.setFormatter(formatter)
    logger.addHandler(qt_handler)
    logger.qt_handler = qt_handler  # <- to kluczowe dla UI

    logger.propagate = False
    logger.info(f"🪵 Logging started → {log_file}")
    return logger

logger = setup_logger()

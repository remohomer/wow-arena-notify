# file: desktop_app/infrastructure/utils.py

import os
import time
import threading
from pathlib import Path
from pynput import keyboard
from infrastructure.logger import logger


def safe_delete(file_path: Path):
    """Usuwa plik bezpiecznie, ignorując błędy."""
    try:
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"🗑️ Deleted screenshot: {file_path.name}")
    except Exception as e:
        logger.info(f"⚠ Error deleting {file_path}: {e}")

class PrintScreenListener:
    """Nasłuchuje wciśnięcia PrintScreen i zapisuje timestampy."""
    def __init__(self):
        self.timestamps = []
        listener = keyboard.Listener(on_press=self.on_press)
        listener.daemon = True
        listener.start()
        logger.info("🎧 PrintScreen listener started.")

    def on_press(self, key):
        if key == keyboard.Key.print_screen:
            timestamp = time.time()
            self.timestamps.append(timestamp)
            self.timestamps = self.timestamps[-10:]

    def is_recent(self, event_time: float, tolerance: int = 1) -> bool:
        return any(abs(event_time - t) <= tolerance for t in self.timestamps)

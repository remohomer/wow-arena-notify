# -*- coding: utf-8 -*-
"""
Utility helpers:
 - safe_delete() → robust file deletion with retry
"""

import time
from pathlib import Path
from infrastructure.logger import logger


# ---------------------------------------------------------------------------
def safe_delete(p: Path) -> bool:
    """
    Removes a file safely (ignores missing, read-only), retries after delay.
    Returns True on success, False otherwise.
    """
    try:
        if not p.exists():
            return True
        p.unlink()
        return True
    except Exception:
        try:
            time.sleep(0.1)
            p.unlink()
            return True
        except Exception as e:
            logger.dev(f"safe_delete failed for {p}: {e}")
            return False


# ---------------------------------------------------------------------------
# Compatibility stub (always return False)
# ---------------------------------------------------------------------------
class PrintScreenListener:
    """
    Deprecated stub. Always returns False so nothing is ignored.
    """
    def is_recent(self, timestamp: float) -> bool:
        return False

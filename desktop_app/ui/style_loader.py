# file: desktop_app/ui/style_loader.py

from pathlib import Path
from infrastructure.logger import logger
import sys

BASE_DIR = Path(
    getattr(sys, "_MEIPASS",
    Path(__file__).resolve().parent.parent)
)

def apply_styles(widget):
    """
    Loads styles.qss from bundle/dev fallback locations.
    """
    fname = "styles.qss"
    candidates = [
        BASE_DIR / "ui" / fname,
        BASE_DIR / fname,
        Path(__file__).parent / "ui" / fname,
        Path(__file__).parent / fname,
        Path.cwd() / "ui" / fname,
        Path.cwd() / fname,
    ]

    for p in candidates:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                widget.setStyleSheet(f.read())
            logger.info(f"🎨 Loaded style: {p}")
            return

    logger.warning("⚠ Could not find styles.qss")
    for p in candidates:
        logger.warning(f"    - {p}")

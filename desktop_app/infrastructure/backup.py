import shutil
import os
from pathlib import Path
from infrastructure.logger import logger

VALID_EXT = {".png", ".jpg", ".jpeg", ".tga"}


def ensure_folder(path: Path):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"❌ Cannot create backup folder: {e}")


def backup_screenshots(src_folder: Path, dst_folder: Path):
    ensure_folder(dst_folder)

    count = 0

    for file in src_folder.iterdir():
        if not file.is_file():
            continue

        if file.suffix.lower() not in VALID_EXT:
            continue

        target = dst_folder / file.name

        if target.exists():
            continue  # already backed up

        try:
            shutil.copy2(file, target)
            count += 1
        except Exception as e:
            logger.error(f"⚠ Cannot backup {file.name}: {e}")

    if count > 0:
        logger.info(f"💾 Backed up {count} new screenshots.")
    else:
        logger.info("💾 Backup up-to-date (no new screenshots).")

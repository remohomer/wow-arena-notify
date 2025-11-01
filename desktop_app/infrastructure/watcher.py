# file: desktop_app/infrastructure/watcher.py
from pathlib import Path

def get_latest_screenshot_info(game_folder: str):
    """Zwraca (Path, timestamp) najnowszego screena lub (None, None)."""
    screenshot_folder = Path(game_folder) / "Screenshots"
    if not screenshot_folder.exists():
        return None, None
    files = list(screenshot_folder.glob("*.jpg")) + list(screenshot_folder.glob("*.png"))
    # ogranicz do ostatnich 50 plików, żeby nie mielić tysięcy
    files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:10]
    if not files:
        return None, None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return latest, latest.stat().st_mtime

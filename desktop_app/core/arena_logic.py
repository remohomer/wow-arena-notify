# core/arena_logic.py — v10 (2025-10-29)
"""
Full-border tag detection | removes only processed screenshots
• POP → start countdown + delete screenshot
• STOP → stop countdown + delete screenshot
• Manual / No Tag → ignore but KEEP file
"""

import os
import time
import uuid
from pathlib import Path
from PIL import Image

from core.firebase_notify import send_fcm_message
from core.push.arena_realtime import send_arena_event
from core.logger import logger
from core.tag_detector import detect_tag
from core.utils import safe_delete, PrintScreenListener


# Listener to detect manual printscreens
printscreen = PrintScreenListener()

_last_event_type: str | None = None
_last_event_id: str | None = None
_last_processed_timestamp = 0.0
_countdown_active = False

_stats = {
    "arena_pop": 0,
    "arena_stop": 0,
    "ignored_manual": 0,
    "ignored_no_tag": 0,
    "ignored_duplicates": 0,
    "ignored_old": 0,
    "ignored_stale": 0,
    "errors": 0,
}


def process_screenshot_event(file_path: Path, cfg: dict, app_start_time: float = 0.0) -> str:
    global _last_event_type, _last_event_id, _countdown_active, _last_processed_timestamp

    try:
        now = time.time()
        modified = os.path.getmtime(file_path)

        # ✅ ignore screenshots before app start
        if app_start_time and modified < app_start_time:
            _stats["ignored_old"] += 1
            return ""

        # ✅ ignore stale screenshots (> 4s old)
        if (now - modified) > 4:
            _stats["ignored_stale"] += 1
            return ""

        # ✅ detect border tag first
        event = detect_tag(str(file_path))

        # ✅ manual screenshot? (kept!)
        if printscreen.is_recent(modified):
            _stats["ignored_manual"] += 1
            logger.info(f"⚪ Manual Screenshot ignored → {file_path.name}")
            return ""

        if not event:
            _stats["ignored_no_tag"] += 1
            logger.info(f"⚪ No tag → ignoring file (kept): {file_path.name}")
            return ""

        # ✅ debounce duplicate events
        if event == _last_event_type and (now - _last_processed_timestamp) < 1.2:
            _stats["ignored_duplicates"] += 1
            return ""

        _last_event_type = event
        _last_processed_timestamp = now

        pairing_id = cfg.get("pairing_id") or "test_desktop"

        # ✅ POP event
        if event == "arena_pop":
            base = int(cfg.get("countdown_time", 40))
            adjusted = max(base - 4, 1)
            _countdown_active = True

            _last_event_id = str(uuid.uuid4())

            logger.info(f"🟢 arena_pop | {adjusted}s | {file_path.name}")

            if not send_fcm_message("arena_pop", adjusted, _last_event_id, pairing_id=pairing_id, cfg=cfg):
                send_arena_event("arena_pop", adjusted, pairing_id, _last_event_id, cfg)

            _stats["arena_pop"] += 1

            safe_delete(file_path)  # ✅ DELETE TAGGED SCREEN
            return "arena_pop"

        # ✅ STOP event
        if event == "arena_stop" and _countdown_active:
            logger.info(f"🔴 arena_stop | {file_path.name}")

            if not _last_event_id:
                _last_event_id = str(uuid.uuid4())

            if not send_fcm_message("arena_stop", 0, _last_event_id, pairing_id=pairing_id, cfg=cfg):
                send_arena_event("arena_stop", 0, pairing_id, _last_event_id, cfg)

            _countdown_active = False
            _last_event_id = None

            _stats["arena_stop"] += 1

            safe_delete(file_path)  # ✅ DELETE TAGGED SCREEN
            return "arena_stop"

        # ✅ STOP bez POP = spam STOP → ignore
        _stats["ignored_duplicates"] += 1
        return ""

    except Exception as e:
        _stats["errors"] += 1
        logger.error(f"❌ process_screenshot_event: {e}")
        return ""


def session_summary_string() -> str:
    s = _stats
    return (
        f"📊 pop={s['arena_pop']}, stop={s['arena_stop']}, "
        f"manual={s['ignored_manual']}, dup={s['ignored_duplicates']}, "
        f"no_tag={s['ignored_no_tag']}, old={s['ignored_old']}, "
        f"stale={s['ignored_stale']}, errors={s['errors']}"
    )

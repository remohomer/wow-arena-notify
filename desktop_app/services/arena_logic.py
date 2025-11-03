# -*- coding: utf-8 -*-
"""
Full-border tag detection | removes processed screenshots
• POP → start countdown + delete screenshot
• STOP → stop countdown + delete screenshot
• No Tag → keep file
"""

import os
import time
import uuid
from pathlib import Path

from services.firebase_notify import send_fcm_message
from services.push.arena_realtime import send_arena_event
from infrastructure.logger import logger
from services.tag_detector import detect_tag
from infrastructure.utils import safe_delete, PrintScreenListener

# stub always returns False
printscreen = PrintScreenListener()

_last_event_type: str | None = None
_last_event_id: str | None = None
_last_processed_timestamp = 0.0
_countdown_active = False

_stats = {
    "arena_pop": 0,
    "arena_stop": 0,
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

        if app_start_time and modified < app_start_time:
            _stats["ignored_old"] += 1
            return ""

        if (now - modified) > 4:
            _stats["ignored_stale"] += 1
            return ""

        event = detect_tag(str(file_path))

        if not event:
            _stats["ignored_no_tag"] += 1
            return ""

        if event == _last_event_type and (now - _last_processed_timestamp) < 1.2:
            _stats["ignored_duplicates"] += 1
            return ""

        _last_event_type = event
        _last_processed_timestamp = now

        pairing_id = cfg.get("pairing_id") or "test_desktop"

        # POP
        if event == "arena_pop":
            base = int(cfg.get("countdown_time", 40))
            user_offset = int(cfg.get("delay_offset", 2))
            real_offset = user_offset + 1
            adjusted = max(base - real_offset, 1)

            _last_event_id = str(uuid.uuid4())
            _countdown_active = True

            logger.user(f"🏁 Arena found!")
            logger.dev(f"POP file={file_path.name}, base={base}, offset={user_offset}+1 → {adjusted}")

            if not send_fcm_message("arena_pop", adjusted, _last_event_id, pairing_id=pairing_id, cfg=cfg):
                send_arena_event("arena_pop", adjusted, pairing_id, _last_event_id, cfg)

            _stats["arena_pop"] += 1
            safe_delete(file_path)
            return "arena_pop"

        # STOP
        if event == "arena_stop" and _countdown_active:
            logger.user("⚔️ Entered arena — fight!")

            if not _last_event_id:
                _last_event_id = str(uuid.uuid4())

            if not send_fcm_message("arena_stop", 0, _last_event_id, pairing_id=pairing_id, cfg=cfg):
                send_arena_event("arena_stop", 0, pairing_id, _last_event_id, cfg)

            _stats["arena_stop"] += 1
            _last_event_id = None
            _countdown_active = False

            safe_delete(file_path)
            return "arena_stop"

        _stats["ignored_duplicates"] += 1
        return ""

    except Exception as e:
        _stats["errors"] += 1
        logger.dev(f"process_screenshot_event error: {e}")
        return ""

def session_summary_string() -> str:
    s = _stats
    return (
        f"stats: pop={s['arena_pop']}, stop={s['arena_stop']}, "
        f"dup={s['ignored_duplicates']}, no_tag={s['ignored_no_tag']}, "
        f"old={s['ignored_old']}, stale={s['ignored_stale']}, errors={s['errors']}"
    )

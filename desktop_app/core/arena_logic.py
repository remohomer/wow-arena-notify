"""
WoW Arena Notify – Arena Event Logic
------------------------------------
Main detection and event dispatch module.
Handles screenshot-based triggers and sends events
through:
 - Cloud Function (HMAC-signed HTTPS via firebase_notify)
 - Realtime Database mirror (arena_realtime)

Now fully decoupled from user_token (uses pairing_id instead).
"""

import os
import time
import threading
import uuid
from core.firebase_notify import send_fcm_message
from core.push.arena_realtime import send_arena_event
from core.utils import safe_delete
from core.logger import logger


# ----------------------------------------------------------------------
# 🌐 Global session state
# ----------------------------------------------------------------------
_last_event_id: str | None = None
_last_event = {"type": None, "time": 0.0}
_last_processed_file = {"name": "", "time": 0.0}
_countdown_active = False

# 📊 Session stats
_stats = {
    "arena_pop": 0,
    "arena_stop": 0,
    "ignored_duplicates": 0,
    "ignored_old": 0,
    "ignored_stale": 0,
    "errors": 0,
}


# ----------------------------------------------------------------------
# 🔎 Screenshot processing
# ----------------------------------------------------------------------
def process_screenshot_event(file_path, cfg: dict, app_start_time: float = 0.0) -> str:
    """
    Inspect new screenshot and detect:
      - arena_pop (start)
      - arena_stop (end)
      - '' → no action
    """
    global _last_event, _last_processed_file, _countdown_active

    try:
        filename = os.path.basename(str(file_path)).lower()
        if not (filename.endswith(".jpg") or filename.endswith(".png")):
            return ""

        modified_time = os.path.getmtime(file_path)
        now = time.time()
        delta = now - modified_time

        # Ignore screenshots before app start
        if app_start_time and modified_time < app_start_time:
            _stats["ignored_old"] += 1
            logger.debug(f"⏸ Ignored old screenshot {filename} (before app start).")
            return ""

        # Ignore stale screenshots (>5s delay)
        if delta > 5:
            _stats["ignored_stale"] += 1
            return ""

        # Deduplicate same file within 5s
        if (
            _last_processed_file["name"] == filename
            and (now - _last_processed_file["time"]) < 5
        ):
            _stats["ignored_duplicates"] += 1
            logger.info(f"⏩ Ignored duplicate event for {filename}")
            return ""
        _last_processed_file.update({"name": filename, "time": now})

        # If countdown already active → this must be arena_stop
        last_event_type = _last_event.get("type")
        last_event_time = _last_event.get("time", 0.0)

        if (_countdown_active and last_event_type == "arena_pop") or (
            last_event_type == "arena_pop" and (now - last_event_time) < 5
        ):
            stop_arena_event(cfg)
            _last_event.update({"type": "arena_stop", "time": now})
            _stats["arena_stop"] += 1
            logger.info(f"🏁 Detected arena start/end → arena_stop ({filename})")
            return "arena_stop"

        # Otherwise treat as a new arena_pop (with -4s correction)
        base = int(cfg.get("countdown_time", 40))
        adjusted = max(base - 4, 1)
        start_arena_event(adjusted, cfg)
        _last_event.update({"type": "arena_pop", "time": now})
        _stats["arena_pop"] += 1
        logger.info(f"📊 Arena POP → base={base}s | adjusted={adjusted}s | delay=4s")
        return "arena_pop"

    except Exception as e:
        _stats["errors"] += 1
        logger.error(f"⚠️ process_screenshot_event() failed: {e}")
        return ""


# ----------------------------------------------------------------------
# 🚀 Send 'arena_pop' (FCM + RTDB)
# ----------------------------------------------------------------------
def start_arena_event(seconds: int, cfg: dict) -> str:
    global _last_event_id, _countdown_active

    _last_event_id = str(uuid.uuid4())
    _countdown_active = True

    # pairing_id detection
    pairing_id = cfg.get("pairing_id", "test_desktop")
    logger.info(f"🎯 pairing_id użyty = {pairing_id}")

    try:
        success_fcm = send_fcm_message(
            event_type="arena_pop",
            seconds=seconds,
            event_id=_last_event_id,
            pairing_id=pairing_id,
            cfg=cfg,
        )
        payload = send_arena_event(
            event_type="arena_pop",
            duration_sec=seconds,
            user_token=pairing_id,  # RTDB mirror uses token-like key
            event_id=_last_event_id,
            cfg=cfg,
        )
        if success_fcm and payload:
            logger.info(f"✅ arena_pop sent successfully (eventId={_last_event_id})")
        else:
            logger.warning(
                f"⚠ arena_pop partially sent (FCM={success_fcm}, RTDB={'OK' if payload else 'FAIL'})"
            )
        return _last_event_id
    except Exception as e:
        _stats["errors"] += 1
        logger.error(f"❌ Failed to send arena_pop: {e}")
        return ""


# ----------------------------------------------------------------------
# 🛑 Send 'arena_stop' (FCM + RTDB)
# ----------------------------------------------------------------------
def stop_arena_event(cfg: dict):
    global _last_event_id, _countdown_active

    if not _countdown_active:
        logger.info("🧱 stop_arena_event ignored — countdown not active.")
        return

    _countdown_active = False
    event_id = _last_event_id or str(uuid.uuid4())
    pairing_id = cfg.get("pairing_id", "test_desktop")
    logger.info(f"🎯 pairing_id użyty = {pairing_id}")

    try:
        success_fcm = send_fcm_message(
            event_type="arena_stop",
            seconds=0,
            event_id=event_id,
            pairing_id=pairing_id,
            cfg=cfg,
        )
        payload = send_arena_event(
            event_type="arena_stop",
            duration_sec=0,
            user_token=pairing_id,
            event_id=event_id,
            cfg=cfg,
        )
        if success_fcm and payload:
            logger.info(f"🛑 arena_stop sent successfully (eventId={event_id})")
        else:
            logger.warning(
                f"⚠ arena_stop partially sent (FCM={success_fcm}, RTDB={'OK' if payload else 'FAIL'})"
            )
        _last_event_id = None
    except Exception as e:
        _stats["errors"] += 1
        logger.error(f"❌ Failed to send arena_stop: {e}")


# ----------------------------------------------------------------------
# 🧹 Deferred screenshot deletion
# ----------------------------------------------------------------------
def delete_screenshot_later(file_path):
    def _del():
        try:
            safe_delete(file_path)
        except Exception as e:
            logger.warning(f"⚠ Could not delete screenshot {file_path}: {e}")

    threading.Timer(0.5, _del).start()


# ----------------------------------------------------------------------
# 📈 Session stats
# ----------------------------------------------------------------------
def session_summary() -> dict:
    return dict(_stats)


def session_summary_string() -> str:
    s = session_summary()
    return (
        f"📊 Session summary → "
        f"pop={s['arena_pop']}, stop={s['arena_stop']}, "
        f"ignored: dup={s['ignored_duplicates']}, old={s['ignored_old']}, stale={s['ignored_stale']}, "
        f"errors={s['errors']}"
    )

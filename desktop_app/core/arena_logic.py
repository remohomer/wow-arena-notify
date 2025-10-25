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
_last_event = {"type": None, "time": 0.0}      # 'arena_pop' / 'arena_stop'
_last_processed_file = {"name": "", "time": 0.0}
_countdown_active = False                      # is countdown active after 'arena_pop'

# 📊 Session stats (for clean end-of-session summary)
_stats = {
    "arena_pop": 0,
    "arena_stop": 0,
    "ignored_duplicates": 0,
    "ignored_old": 0,
    "ignored_stale": 0,
    "errors": 0,
}

# ----------------------------------------------------------------------
# 🔎 Main screenshot analysis + de-duplication + time correction
# ----------------------------------------------------------------------
def process_screenshot_event(file_path, cfg: dict, app_start_time: float = 0.0) -> str:
    """
    Inspect a new screenshot and decide the event:
      - returns 'arena_pop'  → sends FCM & RTDB (with -4s correction)
      - returns 'arena_stop' → sends FCM & RTDB
      - returns ''           → no action

    NOTE: config is passed in; this module does NOT read/write config files.
    """
    global _last_event, _last_processed_file, _countdown_active

    try:
        filename = os.path.basename(str(file_path)).lower()
        if not (filename.endswith(".jpg") or filename.endswith(".png")):
            return ""

        modified_time = os.path.getmtime(file_path)
        now = time.time()
        delta = now - modified_time

        # 1) Ignore screenshots created before the app started
        if app_start_time and modified_time < app_start_time:
            _stats["ignored_old"] += 1
            logger.debug(f"⏸ Ignored old screenshot {filename} (before app start).")
            return ""

        # 2) Ignore stale files (>5s since mtime) to reduce system 'echoes'
        if delta > 5:
            _stats["ignored_stale"] += 1
            return ""

        # 3) De-duplication: same file within a short window (5s)
        if (
            _last_processed_file["name"] == filename
            and (now - _last_processed_file["time"]) < 5
        ):
            _stats["ignored_duplicates"] += 1
            logger.info(f"⏩ Ignored duplicate event for {filename}")
            return ""
        _last_processed_file.update({"name": filename, "time": now})

        # 4) Exactly two screenshots per arena:
        #    if countdown is active after POP → the next screenshot is STOP
        #    also, if POP happened <5s ago (grace) → treat as STOP
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

        # 5) Otherwise → treat as a fresh arena_pop (with -4s correction)
        base = int(cfg.get("countdown_time", 40))
        adjusted = max(base - 4, 1)  # ~3s addon delay + ~1s detection delay
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
# 🚀 Send 'arena_pop' (FCM + RTDB) and mark countdown active
# ----------------------------------------------------------------------
def start_arena_event(seconds: int, cfg: dict) -> str:
    global _last_event_id, _countdown_active

    user_token = cfg.get("fcm_token")
    if not user_token:
        logger.warning("⚠ No paired FCM token — skipping arena_pop.")
        return ""

    _last_event_id = str(uuid.uuid4())
    _countdown_active = True

    try:
        # Pass token & cfg explicitly; no config I/O inside senders
        success_fcm = send_fcm_message(
            event_type="arena_pop",
            seconds=seconds,
            event_id=_last_event_id,
            user_token=user_token,
            cfg=cfg,
        )
        payload = send_arena_event(
            event_type="arena_pop",
            duration_sec=seconds,
            user_token=user_token,
            event_id=_last_event_id,
            cfg=cfg,
        )
        if success_fcm and payload:
            logger.info(f"✅ arena_pop sent (eventId={_last_event_id})")
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
# 🛑 Send 'arena_stop' (FCM + RTDB), protected against double-stop
# ----------------------------------------------------------------------
def stop_arena_event(cfg: dict):
    global _last_event_id, _countdown_active

    if not _countdown_active:
        logger.info("🧱 stop_arena_event ignored — countdown not active.")
        return

    user_token = cfg.get("fcm_token")
    if not user_token:
        logger.warning("⚠ No paired FCM token — skipping arena_stop.")
        _countdown_active = False
        _last_event_id = None
        return

    event_id = _last_event_id or str(uuid.uuid4())
    _countdown_active = False

    try:
        success_fcm = send_fcm_message(
            event_type="arena_stop",
            seconds=0,
            event_id=event_id,
            user_token=user_token,
            cfg=cfg,
        )
        payload = send_arena_event(
            event_type="arena_stop",
            duration_sec=0,
            user_token=user_token,
            event_id=event_id,
            cfg=cfg,
        )
        if success_fcm and payload:
            logger.info(f"🛑 arena_stop sent (eventId={event_id})")
        else:
            logger.warning(
                f"⚠ arena_stop partially sent (FCM={success_fcm}, RTDB={'OK' if payload else 'FAIL'})"
            )
        _last_event_id = None
    except Exception as e:
        _stats["errors"] += 1
        logger.error(f"❌ Failed to send arena_stop: {e}")


# ----------------------------------------------------------------------
# 🧹 Deferred deletion (avoid 'file in use' glitches)
# ----------------------------------------------------------------------
def delete_screenshot_later(file_path):
    def _del():
        try:
            safe_delete(file_path)
        except Exception as e:
            logger.warning(f"⚠ Could not delete screenshot {file_path}: {e}")
    threading.Timer(0.5, _del).start()


# ----------------------------------------------------------------------
# 📈 Session stats helpers
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
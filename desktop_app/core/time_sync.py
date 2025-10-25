import time
import threading
from core.logger import logger

try:
    import firebase_admin
    from firebase_admin import credentials, db
except Exception as e:
    firebase_admin = None
    logger.error(f"❌ Firebase Admin SDK not available: {e}")

_firebase_app_timesync = None
_last_offset = 0
_last_sync_time = 0
_offset_lock = threading.Lock()
_CACHE_TTL = 300  # seconds


def _ensure_timesync_app(sa_path: str, rtdb_url: str):
    """Ensure a dedicated Firebase app for TimeSync is initialized."""
    global _firebase_app_timesync

    if firebase_admin is None:
        logger.error("❌ Firebase Admin SDK missing.")
        return None

    if _firebase_app_timesync:
        return _firebase_app_timesync

    try:
        cred = credentials.Certificate(sa_path)
        _firebase_app_timesync = firebase_admin.initialize_app(
            cred,
            {"databaseURL": rtdb_url},
            name="TimeSync"
        )
        logger.info("✅ Firebase Admin initialized (TimeSync).")
        return _firebase_app_timesync
    except ValueError:
        _firebase_app_timesync = firebase_admin.get_app("TimeSync")
        return _firebase_app_timesync
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase TimeSync app: {e}")
        return None


def get_firebase_server_time_offset(rtdb_url: str, sa_path: str) -> int:
    """Compute offset using ServerValue.TIMESTAMP trick."""
    global _last_offset, _last_sync_time

    with _offset_lock:
        now = time.time()
        if now - _last_sync_time < _CACHE_TTL:
            return _last_offset

        try:
            app = _ensure_timesync_app(sa_path, rtdb_url)
            if app is None:
                return _last_offset

            ref = db.reference("/__time_sync__", app)
            local_before = int(time.time() * 1000)

            # write special value interpreted by Firebase as server time
            ref.set({"server_now": {"timestamp": {".sv": "timestamp"}}})
            data = ref.get()

            if data and "server_now" in data and "timestamp" in data["server_now"]:
                server_time = int(data["server_now"]["timestamp"])
            else:
                logger.error("❌ Invalid response from Firebase time sync node.")
                return _last_offset

            local_after = int(time.time() * 1000)
            local_mid = (local_before + local_after) // 2
            offset_ms = server_time - local_mid

            _last_offset = offset_ms
            _last_sync_time = now
            logger.info(f"🕒 Firebase offset (ServerValue.TIMESTAMP): {offset_ms} ms")
            return offset_ms

        except Exception as e:
            logger.error(f"❌ Could not get Firebase server offset (TIMESTAMP): {e}")
            return _last_offset


def get_firebase_server_time(rtdb_url: str = None, sa_path: str = None, cfg: dict = None) -> int:
    """Return estimated current Firebase server timestamp (ms)."""
    if cfg:
        rtdb_url = (
            rtdb_url
            or cfg.get("rtdb_url")
            or cfg.get("firebase_rtdb_url")
        )
        sa_path = sa_path or cfg.get("firebase_sa_path")

    if not rtdb_url or not sa_path:
        logger.error("❌ Missing firebase_sa_path or rtdb_url in get_firebase_server_time()")
        return int(time.time() * 1000)

    offset = get_firebase_server_time_offset(rtdb_url, sa_path)
    local_time = int(time.time() * 1000)
    server_time = local_time + offset
    logger.info(f"🕒 Server time ≈ {server_time} (offset={offset} ms)")
    logger.info(f"🌍 Synced with Firebase server time: {server_time}")
    return server_time


def get_server_offset(cfg: dict = None, rtdb_url: str = None, sa_path: str = None) -> int:
    """
    Lightweight helper for comparing desktop vs Android offset.
    Uses the same param resolution logic as get_firebase_server_time().
    Falls back to TIMESTAMP-based offset (no .info paths).
    """
    try:
        if cfg:
            rtdb_url = (
                rtdb_url
                or cfg.get("rtdb_url")
                or cfg.get("firebase_rtdb_url")
            )
            sa_path = sa_path or cfg.get("firebase_sa_path")

        if not rtdb_url or not sa_path:
            logger.error("❌ Missing firebase_sa_path or rtdb_url in get_server_offset().")
            return 0

        offset_ms = get_firebase_server_time_offset(rtdb_url, sa_path)
        logger.info(f"🧭 get_server_offset() → using TIMESTAMP offset {offset_ms} ms (fallback)")
        return offset_ms

    except Exception as e:
        logger.error(f"❌ get_server_offset() failed: {e}")
        return 0

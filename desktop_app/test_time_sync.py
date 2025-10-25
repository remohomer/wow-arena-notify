"""
Quick standalone test for Firebase time synchronization.
Run this file to verify that .info/serverTimeOffset returns a valid offset (ms)
and that your local and Firebase times are in sync.
"""

import time
from core.time_sync import get_firebase_server_time, get_firebase_server_time_offset

# 🧩 CONFIG – możesz zmienić na własne dane
RTDB_URL = "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"
SA_PATH = r"C:\Users\Adam\AppData\Local\WoWArenaNotify\firebase-service-account.json"


def run_time_sync_test():
    print("=== 🔥 WoW Arena Notify — Firebase TimeSync Test ===")
    print(f"RTDB URL: {RTDB_URL}")
    print(f"Service Account: {SA_PATH}\n")

    start_local = int(time.time() * 1000)
    offset = get_firebase_server_time_offset(RTDB_URL, SA_PATH)
    server_now = get_firebase_server_time(RTDB_URL, SA_PATH)

    local_now = int(time.time() * 1000)
    diff = server_now - local_now

    print("🕒 Local time:       ", start_local)
    print("🌍 Firebase time:    ", server_now)
    print("🔁 Reported offset:  ", offset, "ms")
    print("📏 Measured diff:    ", diff, "ms\n")

    if abs(diff) < 100:
        print("✅ OK — clocks are synchronized (<100 ms difference)")
    elif abs(diff) < 1000:
        print("⚠️  Small drift detected (<1 s) — acceptable.")
    else:
        print("❌ Large drift (>1 s) — check network delay or offset logic.")

    print("\nDone.\n")


if __name__ == "__main__":
    run_time_sync_test()

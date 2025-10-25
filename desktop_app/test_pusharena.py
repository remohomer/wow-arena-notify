"""
test_pusharena.py
-----------------------------------
Manual test sender for the Firebase Cloud Function pushArena.
Lets you trigger test events directly without running the full desktop app.
"""

import json
import hmac
import hashlib
import requests
import uuid
import time
import os

# 🔧 CONFIGURATION
FIREBASE_PUSH_URL = "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena"
SECRET = os.getenv("WOW_SECRET", "73b5abc506edd15dbae2a0fc1569cdbf8c391e4e59ebd8f2f8c5ac418581dced")  # lub wklej ręcznie
EVENT_TYPE = "arena_pop"  # zmień na "arena_stop" jeśli chcesz
DURATION = 40  # sekundy

# 🔧 PAYLOAD
event_id = str(uuid.uuid4())
sent_at_ms = int(time.time() * 1000)
ends_at_ms = sent_at_ms + DURATION * 1000
payload = {
    "schema": "1",
    "type": EVENT_TYPE,
    "event": EVENT_TYPE,               # 👈 dodane
    "pairing_id": "test_desktop",      # 👈 dodane
    "eventId": event_id,
    "start_time": str(sent_at_ms),     # 👈 dodane
    "endsAt": str(ends_at_ms),
    "duration": str(DURATION),
    "sentAtMs": str(sent_at_ms),
    "desktopOffset": "0"
}

# --- SERIALIZE CANONICAL JSON ---
msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
signature = hmac.new(SECRET.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

# --- SEND REQUEST ---
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "X-Signature": signature
}

print(f"📤 Sending test pushArena → {EVENT_TYPE}")
print(f"Payload: {msg}")
print(f"HMAC: {signature}")

resp = requests.post(FIREBASE_PUSH_URL, data=msg.encode("utf-8"), headers=headers)
print("\n🔁 Response:")
print(f"Status: {resp.status_code}")
print(resp.text)

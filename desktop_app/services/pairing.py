# file: desktop_app/services/pairing.py
# ✅ Handles all REST and config logic, no UI elements

import time
import uuid
import requests
from infrastructure.config import load_config, save_config
from infrastructure.logger import logger
from infrastructure.credentials_provider import CredentialsProvider


def create_pairing_entry():
    """Generates new pairing ID and returns its RTDB URL + credentials."""
    creds = CredentialsProvider()
    rtdb_url = creds.get_rtdb_url()
    pairing_id = str(uuid.uuid4())
    device_url = f"{rtdb_url}/devices/{pairing_id}.json"
    return pairing_id, device_url


def poll_for_device(device_url, stop_flag, timeout_s=60):
    """Polls RTDB for pairing completion."""
    start_t = time.time()
    while not stop_flag.is_set() and time.time() - start_t < timeout_s:
        try:
            resp = requests.get(device_url, timeout=5)
            if resp.ok and resp.text.strip() != "null":
                data = resp.json()
                if isinstance(data, dict) and "deviceId" in data and "device_secret" in data:
                    return data["deviceId"], data["device_secret"]
        except Exception as e:
            logger.warning(f"⚠ Polling error: {e}")
        time.sleep(2)
    return None, None


def finalize_pairing(pairing_id, device_id, device_secret):
    """Saves pairing result to config and updates RTDB with desktop_id."""
    cfg = load_config()
    cfg["pairing_id"] = pairing_id
    cfg["device_id"] = device_id
    cfg["device_secret"] = device_secret
    save_config(cfg)

    desktop_id = cfg.get("desktop_id")
    if desktop_id:
        try:
            creds = CredentialsProvider()
            rtdb_url = creds.get_rtdb_url()
            device_url = f"{rtdb_url}/devices/{pairing_id}.json"
            requests.patch(device_url, json={"desktop_id": desktop_id}, timeout=5)
            logger.info(f"🆕 Desktop ID updated in RTDB ({desktop_id})")
        except Exception as e:
            logger.warning(f"⚠ Could not update desktop_id in RTDB: {e}")


def unpair_device():
    cfg = load_config()
    for key in ("pairing_id", "device_id", "device_secret"):
        cfg.pop(key, None)
    save_config(cfg)
    logger.info("🧹 Device unpaired.")


def get_pairing_status():
    cfg = load_config()
    pairing_id = cfg.get("pairing_id", "")
    device_id = cfg.get("device_id", "")
    device_secret = cfg.get("device_secret", "")
    desktop_id = cfg.get("desktop_id", "")
    paired = bool(pairing_id and device_id and device_secret)
    return {
        "paired": paired,
        "pairing_id": pairing_id,
        "device_id": device_id,
        "device_secret": device_secret,
        "desktop_id": desktop_id,
    }

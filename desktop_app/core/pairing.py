import json
import qrcode
import tempfile
import threading
import uuid
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, db, initialize_app
from PySide6.QtWidgets import QLabel, QDialog, QVBoxLayout, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core.config import load_config, save_config
from core.logger import logger


def _start_device_token_watcher(device_id: str, cfg: dict):
    """Listen for token refreshes at /devices/<deviceId>/fcmToken and update config.json."""
    if not device_id:
        return
    try:
        ref = db.reference(f"devices/{device_id}/fcmToken")
    except Exception as e:
        logger.error(f"❌ Failed to create device token ref: {e}")
        return

    def _listener(event):
        try:
            token = event.data if isinstance(event.data, str) else None
            if token:
                logger.info(f"🔁 Device token updated in RTDB → {token[:16]}…")
                cfg["fcm_token"] = token
                save_config(cfg)
        except Exception as e:
            logger.warning(f"⚠ Error updating token from RTDB: {e}")

    def _watch():
        try:
            ref.listen(_listener)
        except Exception as e:
            logger.error(f"⚠ Device token watcher error: {e}")

    threading.Thread(target=_watch, daemon=True).start()


def start_pairing(parent_widget):
    """Rozpoczyna proces parowania telefonu z aplikacją desktopową."""
    cfg = load_config()
    rtdb_url = cfg.get("rtdb_url")
    firebase_path = cfg.get("firebase_sa_path")

    if not firebase_path or not Path(firebase_path).exists():
        QMessageBox.warning(
            parent_widget,
            "Firebase not configured",
            "⚠ Please configure Firebase service account in settings first.",
        )
        return

    # 🟢 Inicjalizacja Firebase
    try:
        cred = credentials.Certificate(firebase_path)
        if not firebase_admin._apps:
            initialize_app(cred, {"databaseURL": rtdb_url})
    except Exception as e:
        logger.error(f"❌ Failed to init Firebase: {e}")
        QMessageBox.critical(parent_widget, "Error", f"Could not initialize Firebase:\n{e}")
        return

    # 🆔 Unikalne ID parowania
    pairing_id = str(uuid.uuid4())

    # 🔹 Stwórz dane QR (JSON)
    qr_payload = {"pid": pairing_id, "rtdb": rtdb_url}
    tmp = Path(tempfile.gettempdir()) / "wow_pair_qr.png"
    qrcode.make(json.dumps(qr_payload)).save(tmp)

    # 🔹 Okno QR (modalne)
    dlg = QDialog(parent_widget)
    dlg.setWindowTitle("Pair your device")
    dlg.setFixedSize(320, 420)

    layout = QVBoxLayout(dlg)
    pixmap = QPixmap(str(tmp))
    lbl = QLabel()
    lbl.setPixmap(pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    lbl.setAlignment(Qt.AlignCenter)
    info = QLabel(
        "Scan this QR code using the WoW Arena Notify mobile app.\n\n"
        "Waiting for your device to connect..."
    )
    info.setWordWrap(True)
    info.setAlignment(Qt.AlignCenter)
    layout.addWidget(lbl)
    layout.addWidget(info)

    dlg.setModal(True)
    dlg.show()

    # 🔹 Nasłuch na pairing w RTDB (token + opcjonalnie deviceId)
    ref = db.reference(f"pairing/{pairing_id}")

    def listener(event):
        data = event.data
        if not isinstance(data, dict):
            return

        token = (data.get("token") or "").strip()
        device_id = (data.get("deviceId") or "").strip()

        changed = False
        if token:
            logger.info(f"📲 Received FCM token: {token}")
            cfg["fcm_token"] = token
            changed = True

        if device_id:
            logger.info(f"🆔 Received deviceId: {device_id}")
            cfg["device_id"] = device_id
            changed = True

        if changed:
            save_config(cfg)

        # Gdy mamy token → koniec parowania
        if token:
            try:
                ref.delete()
            except Exception:
                pass

            QMessageBox.information(
                parent_widget,
                "Pairing complete",
                "✅ Device paired successfully!\nYour phone will now receive notifications.",
            )
            dlg.close()

            # Start background watcher for future token refreshes (if deviceId is known)
            _start_device_token_watcher(device_id or "", cfg)

    def watch_pairing():
        try:
            ref.listen(listener)
        except Exception as e:
            logger.error(f"⚠ Error listening for pairing: {e}")

    threading.Thread(target=watch_pairing, daemon=True).start()

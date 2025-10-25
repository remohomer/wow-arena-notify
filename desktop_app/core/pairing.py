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


def start_pairing(parent_widget):
    """
    Generates a new pairing_id and shows a QR code.
    The Android app will scan it and register its FCM token
    under this pairing_id in Firebase (server-side only).
    """
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

    # 🟢 Initialize Firebase Admin (for temporary pairing node)
    try:
        cred = credentials.Certificate(firebase_path)
        if not firebase_admin._apps:
            initialize_app(cred, {"databaseURL": rtdb_url})
    except Exception as e:
        logger.error(f"❌ Failed to init Firebase: {e}")
        QMessageBox.critical(parent_widget, "Error", f"Could not initialize Firebase:\n{e}")
        return

    # 🆔 Generate unique pairing_id
    pairing_id = str(uuid.uuid4())

    # 🔹 Create QR payload
    qr_payload = {"pid": pairing_id, "rtdb": rtdb_url}
    tmp = Path(tempfile.gettempdir()) / "wow_pair_qr.png"
    qrcode.make(json.dumps(qr_payload)).save(tmp)

    # 🔹 Show QR modal
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
        "Your phone will register automatically."
    )
    info.setWordWrap(True)
    info.setAlignment(Qt.AlignCenter)
    layout.addWidget(lbl)
    layout.addWidget(info)

    dlg.setModal(True)
    dlg.show()

    # 🔹 Listen for pairing confirmation in RTDB
    ref = db.reference(f"pairing/{pairing_id}")

    def listener(event):
        """Triggered when mobile app confirms pairing."""
        data = event.data
        if not isinstance(data, dict):
            return

        device_id = (data.get("deviceId") or "").strip()
        if device_id:
            logger.info(f"🆔 Device paired successfully (deviceId={device_id})")
            cfg["pairing_id"] = pairing_id
            cfg["device_id"] = device_id
            save_config(cfg)

            try:
                ref.delete()
            except Exception:
                pass

            QMessageBox.information(
                parent_widget,
                "Pairing complete",
                f"✅ Device paired successfully!\n\nPairing ID:\n{pairing_id}",
            )
            dlg.close()

    def watch_pairing():
        try:
            ref.listen(listener)
        except Exception as e:
            logger.error(f"⚠ Error listening for pairing: {e}")

    threading.Thread(target=watch_pairing, daemon=True).start()

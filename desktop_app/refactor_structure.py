# file: desktop_app/refactor_structure.py
import os
import shutil
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent

moves = {
    "core/arena_logic.py": "services/arena_logic.py",
    "core/pairing.py": "services/pairing.py",
    "core/firebase_notify.py": "services/firebase_notify.py",
    "core/time_sync.py": "services/time_sync.py",
    "core/tag_detector.py": "services/tag_detector.py",
    "core/countdown_controller.py": "controllers/countdown_controller.py",
    "core/listener_controller.py": "controllers/listener_controller.py",
    "core/tray_controller.py": "controllers/tray_controller.py",
    "core/watcher.py": "infrastructure/watcher.py",
    "core/credentials_provider.py": "infrastructure/credentials_provider.py",
    "core/config.py": "infrastructure/config.py",
    "core/logger.py": "infrastructure/logger.py",
    "core/utils.py": "infrastructure/utils.py",
    "verify_secret.py": "scripts/verify_secret.py",
}

# create folders
for folder in ["services", "controllers", "infrastructure", "assets", "scripts"]:
    (BASE / folder).mkdir(exist_ok=True)

# move files
for src, dst in moves.items():
    src_path = BASE / src
    dst_path = BASE / dst
    if src_path.exists():
        dst_path.parent.mkdir(exist_ok=True)
        shutil.move(src_path, dst_path)
        print(f"MOVED: {src_path} → {dst_path}")

# update imports recursively
def update_imports():
    pattern = re.compile(r"from core\.(\w+)")
    python_files = list(BASE.rglob("*.py"))

    for file in python_files:
        text = file.read_text(encoding="utf-8")
        new = text

        replacements = {
            "arena_logic": "services.arena_logic",
            "pairing": "services.pairing",
            "firebase_notify": "services.firebase_notify",
            "time_sync": "services.time_sync",
            "tag_detector": "services.tag_detector",
            "countdown_controller": "controllers.countdown_controller",
            "listener_controller": "controllers.listener_controller",
            "tray_controller": "controllers.tray_controller",
            "watcher": "infrastructure.watcher",
            "credentials_provider": "infrastructure.credentials_provider",
            "config": "infrastructure.config",
            "logger": "infrastructure.logger",
            "utils": "infrastructure.utils",
        }

        for old, new_path in replacements.items():
            new = new.replace(f"from core.{old}", f"from {new_path}")

        if new != text:
            file.write_text(new, encoding="utf-8")
            print(f"UPDATED IMPORTS IN: {file}")

update_imports()

print("\n✅ Refactor complete!")

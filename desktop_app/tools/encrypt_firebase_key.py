from pathlib import Path
import base64
import win32crypt

base_dir = Path(__file__).resolve().parent.parent
input_path = base_dir / "core" / "push" / "wow-arena-notify-firebase-adminsdk-fbsvc-5d8afd7b79.json"
output_path = base_dir / "core" / "firebase_credentials.enc"

print(f"🔐 Encrypting Firebase service key:")
print(f"   Source: {input_path}")
print(f"   Target: {output_path}")

if not input_path.exists():
    raise FileNotFoundError(f"❌ Input file not found: {input_path}")

data = input_path.read_bytes()
encrypted = win32crypt.CryptProtectData(data, None, None, None, None, 0)
output_path.write_text(base64.b64encode(encrypted).decode("utf-8"))

print("✅ Done! Encrypted credentials saved successfully.")
print("💾 Output file:", output_path)
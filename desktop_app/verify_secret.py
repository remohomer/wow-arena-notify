# verify_secret.py
import hmac, hashlib

secret = "73b5abc506edd15dbae2a0fc1569cdbf8c391e4e59ebd8f2f8c5ac418581dced"

msg = '{"desktopOffset":"0","duration":"40","endsAt":"1761395346850","eventId":"d6b8f165-ca6b-41c3-8e25-fea2d71258ca","schema":"1","sentAtMs":"1761395306850","type":"arena_pop"}'

print("HMAC:", hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest())

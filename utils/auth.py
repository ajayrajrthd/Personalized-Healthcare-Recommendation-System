import os, time, base64, json, hashlib, hmac
from typing import Optional, Dict
import jwt


SECRET = os.environ.get("JWT_SECRET", "dev_secret_change_me")
ALG = "HS256"

def _pbkdf2_hash(password: str, salt: Optional[bytes] = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(salt + dk).decode("utf-8")

def _split_hash(stored: str):
    raw = base64.b64decode(stored.encode("utf-8"))
    return raw[:16], raw[16:]

def hash_password(password: str) -> str:
    return _pbkdf2_hash(password)

def verify_password(password: str, stored: str) -> bool:
    salt, dk = _split_hash(stored)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(candidate, dk)

def create_jwt(payload: Dict, exp_seconds: int = 60*60*8) -> str:
    now = int(time.time())
    token = jwt.encode(
        {"iat": now, "exp": now + exp_seconds, **payload},
        SECRET,
        algorithm=ALG
    )
    return token

def decode_jwt(token: str) -> Optional[Dict]:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALG])
    except Exception:
        return None

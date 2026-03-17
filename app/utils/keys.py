import secrets
import hashlib

def generate_api_key() -> tuple[str, str, str]:
    """
    Returns (raw_key, prefix, hash)
    raw_key  → shown to developer ONCE, never stored
    prefix   → stored to identify key (e.g. cs_live_a1b2c3)
    hash     → stored in DB for validation
    """
    raw = "cs_live_" + secrets.token_urlsafe(32)
    prefix = raw[:16]  # e.g. cs_live_a1b2c3
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, key_hash

def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()

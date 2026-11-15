import hashlib
import json


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()).hexdigest()


def stable_id(kind: str, *parts) -> str:
    return f"{kind}:{digest(parts)[:24]}"

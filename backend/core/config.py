import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_config(name: str) -> dict:
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))

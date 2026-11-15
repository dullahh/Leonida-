"""Explicit one-time download. Preprocessing and playback never fetch a model."""
from pathlib import Path
from huggingface_hub import snapshot_download
ROOT = Path(__file__).resolve().parents[1]
try:
    path = snapshot_download("Systran/faster-whisper-tiny.en", local_dir=str(ROOT / "var/models/faster-whisper-tiny.en"), allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"], max_workers=1)
except Exception as error:
    raise SystemExit(f"Speech model setup failed: {type(error).__name__}: {error}\nConnect to the internet and retry python scripts/manage.py setup-speech. Cached chat/PCM playback remains available; missing ASR is reported explicitly.") from None
print("Speech model installed:", path)

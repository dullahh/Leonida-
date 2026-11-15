"""Explicit one-time download. Preprocessing and playback never fetch a model."""
from pathlib import Path
import argparse
import json
from huggingface_hub import snapshot_download
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--asr-model", choices=["small.en", "tiny.en"], default="small.en")
args = parser.parse_args()
try:
    from huggingface_hub import model_info
    repository = f"Systran/faster-whisper-{args.asr_model}"
    revision = model_info(repository).sha
    path = snapshot_download(repository, revision=revision, local_dir=str(ROOT / f"var/models/faster-whisper-{args.asr_model}"), allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.txt", "preprocessor_config.json"], max_workers=1)
    files = {p.name: p.stat().st_size for p in Path(path).glob("*") if p.is_file() and p.name != "download.json"}
    receipt = {"repository": repository, "revision": revision, "files_bytes": files, "total_bytes": sum(files.values())}
    (Path(path) / "download.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
except Exception as error:
    raise SystemExit(f"Speech model setup failed: {type(error).__name__}: {error}\nConnect to the internet and retry python scripts/manage.py setup-speech. Cached chat/PCM playback remains available; missing ASR is reported explicitly.") from None
print("Speech model installed:", path)
print(json.dumps(receipt, indent=2))

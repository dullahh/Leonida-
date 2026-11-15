"""Preprocess the recording manifest once; print its immutable replay cache path."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.ingestion.recordings import MediaPreprocessor, load_manifest
from backend.ingestion.tools import MediaSetupError
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--manifest", type=Path, default=ROOT / "data/recordings/manifest.json")
parser.add_argument("--cache-dir", type=Path, default=ROOT / "var/evidence-cache")
parser.add_argument("--asr-model", choices=["small.en", "tiny.en"], help="Quality mode: small.en; explicit fast fallback: tiny.en; default from config/local_asr.json")
parser.add_argument("--reuse-ocr-only", action="store_true", help="Require verified existing OCR artifacts; never run OCR")
parser.add_argument("--no-select-cache", action="store_true", help="Build a new cache without changing the playback pointer")
args = parser.parse_args()
try:
    cache = MediaPreprocessor(ROOT, args.asr_model, reuse_ocr_only=args.reuse_ocr_only).preprocess(load_manifest(args.manifest, ROOT), args.cache_dir)
except (ValueError, OSError, MediaSetupError) as error:
    raise SystemExit(str(error))
path = (args.cache_dir / (cache.cache_key + ".json")).resolve()
(ROOT / "var").mkdir(exist_ok=True)
if not args.no_select_cache:
    (ROOT / "var/last-recording-cache.txt").write_text(str(path), encoding="utf-8")
print("CACHE:", path)
print("Observations:", len(cache.observations))
for report in cache.asset_reports:
    print(report.model_dump_json())

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
args = parser.parse_args()
try:
    cache = MediaPreprocessor(ROOT).preprocess(load_manifest(args.manifest, ROOT), args.cache_dir)
except (ValueError, OSError, MediaSetupError) as error:
    raise SystemExit(str(error))
path = (args.cache_dir / (cache.cache_key + ".json")).resolve()
(ROOT / "var").mkdir(exist_ok=True)
(ROOT / "var/last-recording-cache.txt").write_text(str(path), encoding="utf-8")
print("CACHE:", path)
print("Observations:", len(cache.observations))
for report in cache.asset_reports:
    print(report.model_dump_json())

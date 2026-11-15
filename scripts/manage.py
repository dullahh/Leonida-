"""Windows-native launch/setup/check commands; Make targets delegate here."""
import argparse
import os
import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
NPM = "npm.cmd" if os.name == "nt" else "npm"


def select_demo(scenario, cache=None, root=ROOT):
    """Resolve release input using files only; never extract/download media."""
    if scenario == "portable":
        return "courtroom-praise", None, "Portable deterministic fixture; synthetic evidence and prices."
    if scenario not in {"auto", "recordings"}:
        return scenario, cache, None
    try:
        if cache is None:
            cache = Path((root / "var/last-recording-cache.txt").read_text(encoding="utf-8").strip())
        cache = (root / cache).resolve()
        data = json.loads(cache.read_text(encoding="utf-8"))
        assets = data["manifest"]["recordings"]
        if not assets or any(not a.get("local_path") or not (root / a["local_path"]).is_file() for a in assets):
            raise ValueError("local recording files unavailable")
        index = root / "var/evidence-cache" / data["cache_key"] / "artifacts.json"
        if not index.is_file():
            index = cache.parent / data["cache_key"] / "artifacts.json"
        if not index.is_file() or any(not (cache.parent / p).is_file() for p in json.loads(index.read_text(encoding="utf-8"))):
            raise ValueError("cached evidence artifacts unavailable")
        return "recordings", cache, "Local recordings and cached evidence available."
    except (OSError, ValueError, KeyError, TypeError) as error:
        return "courtroom-praise", None, f"Local demo unavailable ({error}); selecting portable synthetic Courtroom fixture."


def run(arguments, **kwargs):
    result = subprocess.run([str(a) for a in arguments], cwd=ROOT, **kwargs)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup", "demo", "check", "demo-check", "export-contracts", "refresh-markets", "preprocess", "generate-recording", "setup-speech"])
    parser.add_argument("--gate", choices=["G1", "G2", "G3"], default="G3")
    parser.add_argument("--scenario", default="auto")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--live-quotes", action="store_true")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/recordings/manifest.json")
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    if args.action == "setup":
        run(["uv", "sync", "--frozen", "--cache-dir", ".cache/uv"])
        run([NPM, "ci", "--cache", ".cache/npm", "--no-audit", "--no-fund"])
        if (ROOT / "frontend/package-lock.json").exists():
            run([NPM, "--prefix", "frontend", "ci", "--cache", str(ROOT / ".cache/npm"), "--no-audit", "--no-fund"])
            run([NPM, "--prefix", "frontend", "run", "build"])
        print("Setup complete. OCR is bundled; optional local speech model: python scripts/manage.py setup-speech")
        return
    if not PYTHON.exists():
        parser.error("Run python scripts/manage.py setup first")
    if args.action == "demo":
        args.scenario, cache, note = select_demo(args.scenario, args.cache)
        if note:
            print(note, flush=True)
        args.db = args.db or ROOT / ("var/demo-recordings.sqlite3" if args.scenario == "recordings" else "var/demo-portable.sqlite3")
        env = dict(os.environ, LEONIDA_DB=str(args.db.resolve()), LEONIDA_LIVE_QUOTES="1" if args.live_quotes else "0",
            LEONIDA_SCENARIO="foundation" if args.scenario == "recordings" else args.scenario,
            LEONIDA_EVIDENCE_CACHE=str(cache.resolve()) if cache else "")
        print(f"Leonida: http://127.0.0.1:{args.port} | {args.scenario} GTA V proxy evidence | paper / synthetic fills only", flush=True)
        run([PYTHON, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", args.port], env=env)
    elif args.action == "export-contracts":
        run([PYTHON, "scripts/export_contracts.py"])
        run([NPM, "run", "generate"])
    elif args.action == "check":
        run([PYTHON, "-B", "scripts/validate_pack.py"])
        run([PYTHON, "-B", "scripts/export_contracts.py", "--check"])
        run(["node", "scripts/generate_types.cjs", "--check"])
        run([NPM, "run", "typecheck"])
        run(["node", "--check", "scripts/state_viewer.js"])
        if args.gate in {"G2", "G3"}:
            run([PYTHON, "-B", "-m", "backend.ingestion.replay", "--scenario", "all", "--validate-only"])
            run([PYTHON, "-B", "-c", "import backend.quant; import backend.execution.paper; import backend.ingestion.recordings"])
            run([NPM, "--prefix", "frontend", "run", "typecheck"])
            run([NPM, "--prefix", "frontend", "run", "build"])
        if args.gate == "G3":
            run([PYTHON, "-B", "-m", "unittest", "discover", "-s", "tests/g3", "-p", "test_*.py", "-v"])
        print(args.gate + " checks passed. G4 verification: .venv/Scripts/python.exe -m unittest discover -s tests/g4 -v")
    elif args.action == "demo-check":
        scenario = args.scenario
        cache = args.cache
        if scenario == "auto":
            scenario = "recordings" if cache or (ROOT / "var/last-recording-cache.txt").exists() else "foundation"
        if scenario == "recordings" and cache is None:
            cache = Path((ROOT / "var/last-recording-cache.txt").read_text(encoding="utf-8").strip())
        run([PYTHON, "-B", "scripts/inspect_demo.py", "--scenario", scenario] + (["--cache", cache] if cache else []))
    elif args.action == "preprocess":
        run([PYTHON, "scripts/media.py", "--manifest", args.manifest])
    elif args.action == "generate-recording":
        run([PYTHON, "scripts/generate_recording.py"])
    elif args.action == "setup-speech":
        run([PYTHON, "scripts/setup_speech.py"])
    else:
        run([PYTHON, "scripts/refresh_market_snapshot.py"])


if __name__ == "__main__":
    main()

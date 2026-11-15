"""Windows-native launch/setup/check commands; Make targets delegate here."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
NPM = "npm.cmd" if os.name == "nt" else "npm"


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
    parser.add_argument("--db", type=Path, default=ROOT / "var/leonida.sqlite3")
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
        if args.scenario == "auto":
            args.scenario = "recordings" if args.cache or (ROOT / "var/last-recording-cache.txt").exists() else "foundation"
        cache = args.cache
        if args.scenario == "recordings" and cache is None:
            pointer = ROOT / "var/last-recording-cache.txt"
            if not pointer.exists():
                parser.error("Run python scripts/manage.py preprocess --manifest data/recordings/manifest.json first, or pass --cache PATH")
            cache = Path(pointer.read_text(encoding="utf-8").strip())
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
        print(args.gate + " checks passed. Formal G4 suite is a later gate.")
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

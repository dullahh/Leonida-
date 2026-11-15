"""Export or drift-check deterministic G1 serialization schemas/examples/OpenAPI."""
import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.cache import prepare_fixture_cache
from backend.core.config import read_config
from backend.core.market import unavailable
from backend.core.reference_slice import build_snapshot
from backend.core.schemas import EvidenceCache, RecordingManifest, StreamEnvelope, RunCommand, CreateRunRequest, ScenarioRequest
from backend.main import create_app


def artifacts() -> dict[str, str]:
    with TemporaryDirectory(prefix="leonida-export-") as directory:
        cache = prepare_fixture_cache(ROOT / "config/foundation_scenario.json", Path(directory))
        snapshot = build_snapshot("example-g1", cache, read_config("foundation_scenario.json"),
            read_config("scenario_model.json"), read_config("paper_limits.json"),
            unavailable("Deterministic example omits changing venue context; runtime loads actual captures separately."))
        envelope = StreamEnvelope(run_id=snapshot.run_id, sequence=1, generated_at=snapshot.replay_time, payload=snapshot)
        serialized = envelope.model_dump_json(indent=2) + "\n"
        StreamEnvelope.model_validate_json(serialized)
    output = {"dashboard-envelope.example.json": serialized}
    for name, model in (("dashboard-envelope", StreamEnvelope), ("recording-manifest", RecordingManifest), ("evidence-cache", EvidenceCache), ("run-command", RunCommand), ("create-run", CreateRunRequest), ("scenario-request", ScenarioRequest)):
        output[f"{name}.schema.json"] = json.dumps(model.model_json_schema(mode="serialization"), indent=2) + "\n"
    output["openapi.json"] = json.dumps(create_app().openapi(), indent=2) + "\n"
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = ROOT / "contracts/generated"
    destination.mkdir(parents=True, exist_ok=True)
    changed = []
    for name, content in artifacts().items():
        path = destination / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                changed.append(name)
        else:
            path.write_text(content, encoding="utf-8")
    if changed:
        print("Contract artifacts out of date: " + ", ".join(changed))
        return 1
    print("G1 contracts: " + ("drift check passed" if args.check else "exported serialization schemas, full example and OpenAPI"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

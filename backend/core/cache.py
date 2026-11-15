"""Real content-addressed cache; video decoding/OCR is deliberately not implemented at G1."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .identity import digest, stable_id
from .schemas import CachedObservation, EvidenceCache, RecordingManifest


def prepare_fixture_cache(path: Path, directory: Path) -> EvidenceCache:
    raw = path.read_bytes()
    config = json.loads(raw)
    manifest = RecordingManifest.model_validate(config["manifest"])
    observation = dict(config["observation"])
    if observation["provider"] != "supplied_fixture":
        raise ValueError("G1 adapter accepts supplied fixtures only; recorded OCR is not implemented")
    asset = next(a for a in manifest.recordings if a.asset_id == observation["asset_id"])
    if observation["stream_id"] != asset.stream_id:
        raise ValueError("asset and stream disagree")
    observation["replay_seconds"] = asset.replay_offset(observation["media_seconds"])
    observation["observation_id"] = stable_id("observation", observation, manifest.model_dump(mode="json"))
    entry = CachedObservation.model_validate(observation)
    input_hash = hashlib.sha256(raw).hexdigest()
    key = digest({"schema": "2", "input_sha256": input_hash, "manifest": manifest.model_dump(mode="json")})
    payload = [entry.model_dump(mode="json")]
    cache = EvidenceCache(cache_key=key, input_sha256=input_hash, payload_sha256=digest(payload), manifest=manifest, observations=[entry])
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{key}.json"
    if destination.exists():
        existing = EvidenceCache.model_validate_json(destination.read_text(encoding="utf-8"))
        if existing != cache or existing.payload_sha256 != digest([e.model_dump(mode="json") for e in existing.observations]):
            raise ValueError("cache digest/content mismatch; refuse corrupt cached evidence")
        return existing
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, suffix=".tmp", delete=False) as file:
        temporary = Path(file.name)
        file.write(cache.model_dump_json(indent=2) + "\n")
    os.replace(temporary, destination)
    return cache

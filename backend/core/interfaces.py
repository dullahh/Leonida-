"""G1 integration seams. Full multi-stream/quant/broker interfaces remain G2 work."""
from datetime import datetime
from pathlib import Path
from typing import Protocol

from .schemas import EvidenceCache, RecordingManifest, StreamEnvelope


class Clock(Protocol):
    def now(self) -> datetime: ...


class SnapshotReader(Protocol):
    def snapshot(self, run_id: str | None = None) -> StreamEnvelope: ...


class RecordedPreprocessor(Protocol):
    def preprocess(self, manifest: RecordingManifest, cache_directory: Path) -> EvidenceCache: ...


class UnavailableRecordedPreprocessor:
    """Explicit G1 placeholder: never supplies fabricated OCR/media output."""
    def preprocess(self, manifest: RecordingManifest, cache_directory: Path) -> EvidenceCache:
        raise NotImplementedError("Recorded video decoding and sampled-frame OCR are not implemented at G1. Supply recordings and execute the pipeline job after G1.")

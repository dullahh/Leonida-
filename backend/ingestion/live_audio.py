"""Bounded transcription adapter for user-authorized live tab-audio chunks.

The adapter does not discover or download Twitch media. A browser client must
capture the selected tab audio with explicit user permission and submit short
chunks. This module returns transcript observations only; game identity,
semantic claims and market routing belong to separate, later stages.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import math
from pathlib import Path
import tempfile
import wave

from backend.core.identity import digest, stable_id
from .audio import GATE_VERSION, LocalASR, validate_segments
from .tools import MediaSetupError, run_ffmpeg

LIVE_AUDIO_ADAPTER_VERSION = "live-tab-audio-v1"
MAX_CHUNK_BYTES = 2 * 1024 * 1024
MAX_CHUNK_SECONDS = 15.0


@dataclass(frozen=True)
class LiveAudioTranscriptWindow:
    """Standalone live observation; deliberately not a GTA V proxy SourceWindow."""

    schema_version: str
    source_window_id: str
    stream_id: str
    evidence_mode: str
    source_media_start_seconds: float
    source_media_end_seconds: float
    event_at: datetime
    available_at: datetime
    source_sha256: str
    payload_sha256: str
    adapter_version: str
    asr_version: str | None
    model_identity: dict | None
    gate_version: str
    status: str
    unavailable_reason: str | None
    accepted_segments: tuple[dict, ...]
    audit_segments: tuple[dict, ...]

    def as_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "source_window_id": self.source_window_id,
            "stream_id": self.stream_id,
            "evidence_mode": self.evidence_mode,
            "source_media_start_seconds": self.source_media_start_seconds,
            "source_media_end_seconds": self.source_media_end_seconds,
            "event_at": self.event_at.isoformat(),
            "available_at": self.available_at.isoformat(),
            "source_sha256": self.source_sha256,
            "payload_sha256": self.payload_sha256,
            "adapter_version": self.adapter_version,
            "asr_version": self.asr_version,
            "model_identity": self.model_identity,
            "gate_version": self.gate_version,
            "status": self.status,
            "unavailable_reason": self.unavailable_reason,
            "accepted_segments": list(self.accepted_segments),
            "audit_segments": list(self.audit_segments),
        }


class LiveAudioTranscriber:
    """Transcribe small user-captured chunks with one local Whisper model.

    `engine` may be supplied by the app lifespan to reuse one loaded model. If
    omitted, loading is lazy and occurs on the first valid chunk. No model or
    executable is downloaded here.
    """

    def __init__(self, model_path: Path, *, engine: LocalASR | None = None):
        self.model_path = model_path.resolve()
        self.engine = engine

    def transcribe_chunk(
        self,
        *,
        stream_id: str,
        payload: bytes,
        content_type: str,
        source_media_start_seconds: float,
        event_at: datetime,
        available_at: datetime,
        language: str = "en",
    ) -> LiveAudioTranscriptWindow:
        """Convert and transcribe one chunk, preserving its source-time offset.

        WAV chunks and standalone WebM/Opus chunks are accepted. Chunk timestamps
        are source-relative seconds; callers should send non-overlapping windows
        with stable offsets. Invalid input raises ValueError for an HTTP 4xx.
        Missing local ASR returns an explicit `unavailable` observation.
        """
        if not stream_id or len(stream_id) > 240:
            raise ValueError("stream_id must contain 1–240 characters")
        if content_type.lower().split(";")[0].strip() not in {"audio/webm", "audio/wav", "audio/wave", "audio/x-wav"}:
            raise ValueError("content_type must be audio/webm or audio/wav")
        if language not in {"eng", "en"}:
            raise ValueError("Live local ASR currently supports English only (language=en)")
        if not isinstance(payload, bytes) or not payload or len(payload) > MAX_CHUNK_BYTES:
            raise ValueError(f"audio chunk must be between 1 and {MAX_CHUNK_BYTES} bytes")
        if not math.isfinite(source_media_start_seconds) or source_media_start_seconds < 0:
            raise ValueError("source_media_start_seconds must be finite and nonnegative")
        if event_at.tzinfo is None or event_at.utcoffset() is None or available_at.tzinfo is None or available_at.utcoffset() is None:
            raise ValueError("event_at and available_at must be timezone-aware")
        if available_at < event_at:
            raise ValueError("available_at cannot precede event_at")

        source_hash = hashlib.sha256(payload).hexdigest()
        suffix = ".wav" if content_type.lower().split(";")[0].strip() in {"audio/wav", "audio/wave", "audio/x-wav"} else ".webm"
        with tempfile.TemporaryDirectory(prefix="leonida-live-audio-") as temporary:
            root = Path(temporary)
            original, pcm = root / f"input{suffix}", root / "audio-16k-mono.wav"
            original.write_bytes(payload)
            try:
                run_ffmpeg(["-y", "-i", str(original), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(pcm)], timeout=20)
                with wave.open(str(pcm), "rb") as source:
                    duration = source.getnframes() / source.getframerate()
            except (MediaSetupError, OSError, EOFError, wave.Error) as error:
                raise ValueError(f"audio chunk could not be decoded: {error}") from error
            if not math.isfinite(duration) or duration <= 0 or duration > MAX_CHUNK_SECONDS:
                raise ValueError(f"decoded audio duration must be between 0 and {MAX_CHUNK_SECONDS:g} seconds")

            source_end = source_media_start_seconds + duration
            window_id = stable_id("live-audio-window", stream_id, source_media_start_seconds, source_end, source_hash, LIVE_AUDIO_ADAPTER_VERSION)
            pcm_hash = hashlib.sha256(pcm.read_bytes()).hexdigest()
            payload_hash = digest({"source_sha256": source_hash, "pcm_sha256": pcm_hash, "model_path": str(self.model_path), "adapter_version": LIVE_AUDIO_ADAPTER_VERSION, "gate_version": GATE_VERSION})
            try:
                if self.engine is None:
                    self.engine = LocalASR(self.model_path)
                raw = self.engine.transcribe(pcm, language)
                accepted, audit = validate_segments(raw, duration)
                accepted = tuple(self._absolute_segment(segment, source_media_start_seconds, event_at) for segment in accepted)
                audit = tuple(self._absolute_audit(entry, source_media_start_seconds, event_at) for entry in audit)
                return LiveAudioTranscriptWindow(
                    schema_version="1", source_window_id=window_id, stream_id=stream_id,
                    evidence_mode="live", source_media_start_seconds=source_media_start_seconds,
                    source_media_end_seconds=source_end, event_at=event_at, available_at=available_at,
                    source_sha256=source_hash, payload_sha256=payload_hash,
                    adapter_version=LIVE_AUDIO_ADAPTER_VERSION,
                    asr_version="local-asr-v2", model_identity=self.engine.identity,
                    gate_version=GATE_VERSION, status="transcribed", unavailable_reason=None,
                    accepted_segments=accepted, audit_segments=audit,
                )
            except (MediaSetupError, ImportError, RuntimeError, OSError) as error:
                return LiveAudioTranscriptWindow(
                    schema_version="1", source_window_id=window_id, stream_id=stream_id,
                    evidence_mode="live", source_media_start_seconds=source_media_start_seconds,
                    source_media_end_seconds=source_end, event_at=event_at, available_at=available_at,
                    source_sha256=source_hash, payload_sha256=payload_hash,
                    adapter_version=LIVE_AUDIO_ADAPTER_VERSION, asr_version=None,
                    model_identity=None, gate_version=GATE_VERSION, status="unavailable",
                    unavailable_reason=f"Local ASR unavailable: {type(error).__name__}: {str(error)[:240]}",
                    accepted_segments=(), audit_segments=(),
                )

    @staticmethod
    def _absolute_segment(segment: dict, offset: float, event_at: datetime) -> dict:
        local_start, local_end = segment["start_seconds"], segment["end_seconds"]
        return {
            **segment,
            "local_start_seconds": local_start,
            "local_end_seconds": local_end,
            "start_seconds": offset + local_start,
            "end_seconds": offset + local_end,
            "event_start_at": (event_at + timedelta(seconds=local_start)).astimezone(timezone.utc).isoformat(),
            "event_end_at": (event_at + timedelta(seconds=local_end)).astimezone(timezone.utc).isoformat(),
            "evidence_mode": "live",
        }

    @staticmethod
    def _absolute_audit(entry: dict, offset: float, event_at: datetime) -> dict:
        local_start, local_end = entry.get("start_seconds"), entry.get("end_seconds")
        result = {**entry, "evidence_mode": "live"}
        if isinstance(local_start, (int, float)) and isinstance(local_end, (int, float)):
            result.update({
                "local_start_seconds": local_start,
                "local_end_seconds": local_end,
                "start_seconds": offset + local_start,
                "end_seconds": offset + local_end,
                "event_start_at": (event_at + timedelta(seconds=local_start)).astimezone(timezone.utc).isoformat(),
                "event_end_at": (event_at + timedelta(seconds=local_end)).astimezone(timezone.utc).isoformat(),
            })
        return result

"""Local PCM extraction, measured activity, and optional local Whisper ASR.

Activity is an acoustic measurement, never game sentiment or guaranteed speech.
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import re
import sys
import wave

from .tools import MediaSetupError, run_ffmpeg


def pcm_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as source:
        return source.getnframes() / source.getframerate()


def validate_segments(segments: list[dict], duration: float) -> tuple[list[dict], list[dict]]:
    """Retain raw ASR separately; never manufacture events from out-of-file times.

    At most 50 ms of timestamp rounding at the final boundary is tolerated. A
    repeated phrase remains visible but is flagged as unreliable interpretation.
    """
    accepted, audit, recent = [], [], []
    for index, original in enumerate(segments):
        segment = dict(original)
        start, end = segment["start_seconds"], segment["end_seconds"]
        reason = None
        if not all(math.isfinite(value) for value in (start, end, segment["avg_logprob"], segment["no_speech_probability"])):
            reason = "nonfinite ASR timing or quality"
        elif start < 0 or start >= duration or end <= start:
            reason = "ASR segment has no positive interval within the actual PCM audio"
        elif end > duration + .05:
            reason = "ASR segment extends beyond the actual PCM audio; text cannot be supported by a clipped interval"
        elif not segment["text"].strip():
            reason = "ASR segment has no text"
        if reason:
            audit.append({"segment_index": index, "status": "rejected", "reason": reason, "raw_segment": original, "start_seconds": start, "end_seconds": end, "pcm_duration_seconds": duration})
            continue
        segment["end_seconds"] = min(end, duration)
        normalized = re.sub(r"[^\w]+", " ", segment["text"].casefold()).strip()
        repeated = len(recent) >= 2 and normalized == recent[-1] == recent[-2]
        words = normalized.split()
        for width in range(1, min(9, len(words) // 3 + 1)):
            if any(words[pos:pos + width] == words[pos + width:pos + 2 * width] == words[pos + 2 * width:pos + 3 * width] for pos in range(len(words) - 3 * width + 1)):
                repeated = True
                break
        if repeated:
            segment["repetition_warning"] = "Repeated ASR phrase may be a decoding loop; retain raw evidence but abstain from sentiment."
        compression = segment.get("compression_ratio")
        if compression is not None and (not math.isfinite(compression) or compression > 2.4):
            segment["quality_warning"] = f"High ASR compression ratio ({compression}); decoding may be repetitive or hallucinated."
        recent.append(normalized)
        accepted.append(segment)
        warnings = [segment[key] for key in ("repetition_warning", "quality_warning") if key in segment]
        audit.append({"segment_index": index, "status": "accepted_with_quality_warning" if warnings else "accepted", "warnings": warnings, "start_seconds": start, "end_seconds": segment["end_seconds"], "pcm_duration_seconds": duration})
    return accepted, audit


def extract_audio(path: Path, destination: Path, start: float, duration: float) -> list[dict]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(["-y", "-ss", str(start), "-i", str(path), "-t", str(duration), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(destination)], timeout=max(120, int(duration * 3)))
    activity = []
    with wave.open(str(destination), "rb") as source:
        index = 0
        while data := source.readframes(32000):
            values = array("h", data)
            if sys.byteorder != "little":
                values.byteswap()
            rms = math.sqrt(sum(float(x) * x for x in values) / len(values)) / 32768
            activity.append({"start_seconds": start + index * 2, "end_seconds": start + index * 2 + len(values) / 16000, "rms": rms, "audible_activity": rms >= .005, "measurement": "rms-v1; activity does not establish speech or sentiment"})
            index += 1
    return activity


def transcribe(path: Path, model_path: Path, language: str) -> list[dict]:
    if not model_path.is_dir() or not (model_path / "model.bin").is_file():
        raise MediaSetupError(f"Local Whisper model missing at {model_path}. Download a faster-whisper model during setup, then set speech_model_path in the manifest. Playback never downloads a model.")
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise MediaSetupError("Speech ASR unavailable. Run python scripts/manage.py setup to install faster-whisper, then configure a local speech_model_path.") from error
    try:
        model = WhisperModel(str(model_path), device="cpu", compute_type="int8", cpu_threads=2, local_files_only=True)
        # We already own the decoded PCM format. Passing it directly also avoids
        # faster-whisper's filename decoder relying on older PyAV keyword options.
        import numpy as np
        with wave.open(str(path), "rb") as source:
            if source.getnchannels() != 1 or source.getframerate() != 16000 or source.getsampwidth() != 2:
                raise ValueError("ASR expects extracted 16 kHz mono PCM16 audio.")
            audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        segments, _ = model.transcribe(audio, language={"eng": "en"}.get(language, language), beam_size=1, temperature=0, vad_filter=False, condition_on_previous_text=False)
        return [{"start_seconds": float(s.start), "end_seconds": float(s.end), "text": s.text.strip(), "avg_logprob": float(s.avg_logprob), "no_speech_probability": float(s.no_speech_prob), "compression_ratio": float(s.compression_ratio)} for s in segments if s.text.strip()]
    except Exception as error:
        raise MediaSetupError(f"Local Whisper transcription failed: {error}") from error

"""Resolve local providers without downloading programs or models at runtime."""
from __future__ import annotations

import hashlib
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess


class MediaSetupError(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def ffmpeg_path() -> str:
    configured = os.getenv("LEONIDA_FFMPEG")
    candidate = configured or shutil.which("ffmpeg")
    if candidate:
        if not Path(candidate).is_file():
            raise MediaSetupError(f"FFmpeg executable does not exist: {candidate}. Set LEONIDA_FFMPEG to ffmpeg.exe or run python scripts/manage.py setup.")
        return str(candidate)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError, OSError) as error:
        raise MediaSetupError("FFmpeg unavailable. Run python scripts/manage.py setup for the bundled imageio-ffmpeg executable, or install FFmpeg and set LEONIDA_FFMPEG to its executable. FFprobe is not required.") from error


def run_ffmpeg(arguments: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess:
    command = [ffmpeg_path(), "-nostdin", "-hide_banner", "-loglevel", "error", *arguments]
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise MediaSetupError(f"FFmpeg failed to run: {error}") from error
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace")[-1800:]
        raise MediaSetupError(f"FFmpeg decoding failed (exit {result.returncode}): {detail}")
    return result


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unavailable"


def media_info(path: Path) -> dict:
    try:
        import av
    except ImportError as error:
        raise MediaSetupError("Media metadata decoder PyAV unavailable. Run python scripts/manage.py setup (av is installed with faster-whisper).") from error
    try:
        with av.open(str(path)) as container:
            video = next(iter(container.streams.video), None)
            if video is None:
                raise MediaSetupError(f"No video stream found in {path.name}.")
            duration = float(container.duration / av.time_base) if container.duration is not None else None
            if duration is None and video.duration is not None:
                duration = float(video.duration * video.time_base)
            if duration is None or duration <= 0:
                raise MediaSetupError(f"Cannot establish a positive video duration for {path.name}.")
            return {"duration_seconds": duration, "width": video.width, "height": video.height, "audio_available": bool(container.streams.audio)}
    except MediaSetupError:
        raise
    except Exception as error:
        raise MediaSetupError(f"Cannot decode media metadata for {path.name}: {error}") from error

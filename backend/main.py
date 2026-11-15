"""FastAPI lifespan and composition only. No venue execution routes."""
import asyncio
from datetime import datetime, timezone
import ipaddress
import os
import re
from threading import Lock
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from backend.core.config import ROOT
from backend.core.projector import StateProjector
from backend.core.runtime import Runtime
from backend.core.schemas import CommandResult, CreateRunRequest, EvidenceCache, ExecutionTrace, Receipt, RunCommand, ScenarioRequest, StreamEnvelope


def create_app(db_path: Path | None = None, cache_dir: Path | None = None, live_quotes: bool = False, evidence_cache_path: Path | None = None, scenario: str = "foundation") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        runtime = Runtime(db_path or ROOT / "var/leonida.sqlite3", (evidence_cache_path.parent if evidence_cache_path else cache_dir or ROOT / "var/evidence-cache"), live_quotes, evidence_cache_path, scenario)
        app.state.runtime = runtime
        app.state.projector = StateProjector(runtime)
        from backend.ingestion.live_audio import LiveAudioTranscriber
        from backend.core.config import read_config
        model_name = read_config("local_asr.json").get("default_model", "small.en")
        app.state.live_audio_transcriber = LiveAudioTranscriber(ROOT / "var" / "models" / f"faster-whisper-{model_name}")
        app.state.live_audio_lock = Lock()
        try:
            await runtime.start()
            yield
        finally:
            await runtime.close()

    app = FastAPI(title="Leonida Alpha proxy desk", version="0.3.0", lifespan=lifespan)

    @app.get("/")
    async def viewer():
        index = ROOT / "frontend/dist/index.html"
        return FileResponse(index if index.exists() else ROOT / "scripts/state_viewer.html")

    @app.get("/foundation")
    async def foundation_viewer():
        return FileResponse(ROOT / "scripts/state_viewer.html")

    @app.get("/assets/{name}")
    async def asset(name: str):
        if name in {"state_viewer.css", "state_viewer.js"}:
            return FileResponse(ROOT / "scripts" / name)
        directory = (ROOT / "frontend/dist/assets").resolve()
        path = (directory / name).resolve()
        if path.parent != directory or not path.is_file():
            raise HTTPException(404)
        return FileResponse(path)

    verified_media = {}

    @app.get("/api/recordings/{asset_id}/media")
    async def recording_media(asset_id: str, run_id: str | None = None):
        runtime = app.state.runtime
        try:
            cache = runtime.context(run_id).cache
        except KeyError:
            raise HTTPException(404, "Unknown run")
        asset = next((a for a in cache.manifest.recordings if a.asset_id == asset_id), None)
        if asset is None or not asset.local_path:
            raise HTTPException(404, "Recording is unavailable; configure data/recordings/manifest.json")
        path = (ROOT / asset.local_path).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise HTTPException(404, "Recording file is unavailable within the repository")
        stat = path.stat()
        fingerprint = (str(path), stat.st_size, stat.st_mtime_ns, asset.asset_sha256)
        if verified_media.get(asset_id) != fingerprint:
            from backend.ingestion.tools import file_sha256
            if await asyncio.to_thread(file_sha256, path) != asset.asset_sha256:
                raise HTTPException(409, "Recording bytes changed since preprocessing; rebuild the evidence cache")
            verified_media[asset_id] = fingerprint
        return FileResponse(path)

    @app.get("/api/evidence/artifact")
    async def evidence_artifact(ref: str, run_id: str | None = None):
        runtime = app.state.runtime
        try:
            context = runtime.context(run_id)
        except KeyError:
            raise HTTPException(404, "Unknown run")
        allowed = {o.frame_ref for o in context.cache.observations if o.frame_ref}
        allowed.update(o.audio_ref for o in context.cache.observations if o.audio_ref)
        allowed.update(r.audio_ref for r in context.cache.asset_reports if r.audio_ref)
        if ref not in allowed:
            raise HTTPException(404, "Unknown evidence artifact")
        directory = (context.cache_path.parent if context.cache_path else runtime.cache_dir).resolve()
        path = (directory / ref).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise HTTPException(404, "Cached artifact unavailable")
        return FileResponse(path)

    @app.get("/health")
    async def health():
        return {"status": "ok", "gate": app.state.runtime.snapshot().payload.gate, "execution": "paper_synthetic_only"}

    @app.get("/ready")
    async def ready():
        runtime = app.state.runtime
        return {"ready": True, "schema_version": "2", "run_id": runtime.active_run_id,
            "cache_key": runtime.cache.cache_key, "live_quote_polling": runtime.live_quotes,
            "capabilities": {"cached_fixture": True, "recording_offsets": True, "candidate_pipeline": True,
                "recorded_video_decoder": True, "sampled_frame_ocr": True, "audio_extraction": True, "cached_synchronized_playback": True, "paper_broker": True},
            "asset_reports": runtime.cache.asset_reports, "limitations": ["Only fully synthetic fixtures can simulate fills; media remains candidate-only", "GTA V proxy evidence never prices actual GTA VI contracts"]}

    @app.get("/api/state", response_model=StreamEnvelope)
    async def state(run_id: str | None = None):
        try:
            return app.state.projector.snapshot(run_id)
        except KeyError:
            raise HTTPException(404, "Unknown run")

    @app.get("/api/cache", response_model=EvidenceCache)
    async def evidence_cache():
        return app.state.runtime.cache

    @app.post("/api/live-audio/chunks")
    async def live_audio_chunk(request: Request):
        """Transcribe one user-authorized, bounded audio-only browser chunk."""
        from backend.ingestion.live_audio import MAX_CHUNK_BYTES

        client_host = request.client.host if request.client else ""
        try:
            if not ipaddress.ip_address(client_host.split("%", 1)[0]).is_loopback:
                raise HTTPException(403, "Live capture is available only through the local demo server")
        except ValueError:
            raise HTTPException(403, "Live capture is available only through the local demo server")
        origin = request.headers.get("origin")
        host = request.headers.get("host", "")
        if origin and origin not in {f"http://{host}", f"https://{host}"}:
            raise HTTPException(403, "Cross-origin live audio upload is not allowed")

        channel = request.headers.get("x-leonida-source", "").strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{1,25}", channel):
            raise HTTPException(422, "A valid Twitch channel login is required")
        raw_started_at = request.headers.get("x-leonida-started-at", "")
        try:
            event_at = datetime.fromisoformat(raw_started_at.replace("Z", "+00:00"))
            if event_at.tzinfo is None or event_at.utcoffset() is None:
                raise ValueError("timezone required")
            chunk_index = int(request.headers.get("x-leonida-chunk-index", "0"))
            if chunk_index < 0:
                raise ValueError("chunk index must be nonnegative")
            source_start = chunk_index * 15.0
        except ValueError:
            raise HTTPException(422, "Valid timezone-aware chunk start and nonnegative chunk index are required")

        content_type = request.headers.get("content-type", "")
        if content_type.lower().split(";", 1)[0].strip() not in {"audio/webm", "audio/wav", "audio/wave", "audio/x-wav"}:
            raise HTTPException(415, "Only independently decodable WebM/Opus or WAV audio chunks are accepted")
        try:
            content_length = int(request.headers.get("content-length", "0"))
        except ValueError:
            raise HTTPException(400, "Invalid Content-Length")
        if content_length > MAX_CHUNK_BYTES:
            raise HTTPException(413, f"Audio chunks are limited to {MAX_CHUNK_BYTES} bytes")
        payload = bytearray()
        async for part in request.stream():
            payload.extend(part)
            if len(payload) > MAX_CHUNK_BYTES:
                raise HTTPException(413, f"Audio chunks are limited to {MAX_CHUNK_BYTES} bytes")
        if not payload:
            raise HTTPException(422, "Audio chunk is empty")

        transcriber = app.state.live_audio_transcriber
        lock = app.state.live_audio_lock
        def transcribe():
            with lock:
                return transcriber.transcribe_chunk(
                    stream_id=f"twitch:{channel}", payload=bytes(payload), content_type=content_type,
                    source_media_start_seconds=source_start, event_at=event_at,
                    available_at=datetime.now(timezone.utc), language="en",
                ).as_dict()
        try:
            return await asyncio.to_thread(transcribe)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/markets")
    async def markets(run_id: str | None = None):
        envelope = await state(run_id)
        p = envelope.payload
        return {"scenario": {"markets": p.markets, "quotes": p.quotes}, "venue_context": p.venue_context}

    @app.post("/api/runs", response_model=CommandResult)
    async def create_run(request: CreateRunRequest):
        try:
            return await app.state.runtime.create_run(request)
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.post("/api/runs/{run_id}/control", response_model=CommandResult)
    async def control(run_id: str, request: RunCommand):
        try:
            return await app.state.runtime.control(run_id, request)
        except KeyError:
            raise HTTPException(404, "Unknown run")
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.post("/api/runs/{run_id}/inject", response_model=CommandResult)
    async def inject(run_id: str, request: ScenarioRequest):
        try:
            return await app.state.runtime.inject(run_id, request)
        except KeyError:
            raise HTTPException(404, "Unknown run")
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get("/api/runs/{run_id}/receipts/{receipt_id}", response_model=Receipt)
    async def receipt(run_id: str, receipt_id: str):
        envelope = await state(run_id)
        result = app.state.runtime.store.record(run_id, "receipts", receipt_id)
        if result is None:
            raise HTTPException(404, "Receipt not found in this run")
        return result

    @app.get("/api/runs/{run_id}/execution-traces/{trace_id}", response_model=ExecutionTrace)
    async def execution_trace(run_id: str, trace_id: str):
        envelope = await state(run_id)
        result = next((t for t in envelope.payload.execution.traces if t.trace_id == trace_id), None)
        if result is None:
            raise HTTPException(404, "Execution trace not found in this run")
        return result

    @app.websocket("/ws")
    async def websocket(websocket: WebSocket, run_id: str | None = None):
        await websocket.accept()
        try:
            selected = run_id or app.state.runtime.active_run_id
            while True:
                envelope = app.state.projector.snapshot(selected)
                await websocket.send_text(envelope.model_dump_json())
                await asyncio.sleep(1)  # transport-only; unchanged sequence/state, never ingestion
        except KeyError:
            await websocket.close(code=1008, reason="Unknown run")
        except (WebSocketDisconnect, RuntimeError):
            return

    return app


app = create_app(
    db_path=Path(os.environ["LEONIDA_DB"]) if "LEONIDA_DB" in os.environ else None,
    live_quotes=os.environ.get("LEONIDA_LIVE_QUOTES") == "1",
    evidence_cache_path=Path(os.environ["LEONIDA_EVIDENCE_CACHE"]) if os.environ.get("LEONIDA_EVIDENCE_CACHE") else None,
    scenario=os.environ.get("LEONIDA_SCENARIO", "foundation"),
)

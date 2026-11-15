"""One run-scoped scheduler and SQLite writer; full snapshots only."""
import asyncio
from dataclasses import dataclass
import time
from pathlib import Path
import httpx
from .cache import prepare_fixture_cache
from .clock import utc_now
from .config import ROOT, read_config
from .identity import digest, stable_id
from .market import fetch_context, historical_context
from .reference_slice import build_snapshot
from .schemas import CommandResult, CreateRunRequest, RunCommand, StreamEnvelope
from .storage import StateStore

@dataclass(frozen=True)
class RunInput:
    name: str
    cache: object
    metadata: dict
    fingerprint: str
    cache_path: Path | None = None

    def saved(self):
        return {"name": self.name, "fingerprint": self.fingerprint, "cache_path": str(self.cache_path) if self.cache_path else None}

class Runtime:
    def __init__(self, db: Path, cache_dir: Path, live_quotes=False, evidence_cache_path: Path | None = None, scenario="foundation"):
        self.cache_dir, self.evidence_cache_path = cache_dir, evidence_cache_path
        self.fixture = read_config("foundation_scenario.json")
        self.model = read_config("scenario_model.json")
        self.limits = read_config("paper_limits.json")
        self.registry = read_config("market_registry.json")
        self.store, self.lock = StateStore(db), asyncio.Lock()
        self.live_quotes = live_quotes
        self.venue = historical_context(ROOT / "data/snapshots", self.registry["aliases"])
        self.contexts, self.loaded_inputs = {}, {}
        self.frames = {e.run_id: e for e in self.store.all_runs()}
        for run_id, saved in self.store.inputs().items():
            context = self._input(saved["name"], Path(saved["cache_path"]) if saved["cache_path"] else None)
            if context.fingerprint == saved["fingerprint"]:
                self.contexts[run_id] = context
        base = self._input("recordings" if evidence_cache_path else scenario, evidence_cache_path)
        active = self.store.active()
        if active in self.contexts:
            self.active_run_id = active
        else:
            run_id = stable_id("run", "g3", base.fingerprint)
            if run_id in self.frames:
                run_id = stable_id("run", run_id, len(self.frames))
            frame, broker, audit = self._new_frame(run_id, base)
            self.store.commit(frame, active=True, broker_state=(0, broker) if broker else None, audit_snapshots=audit, run_input=base.saved())
            self.frames[run_id], self.contexts[run_id] = frame, base
            self.active_run_id = run_id
        self.task = self.freshness_task = self.client = self.playback_task = None
        self.last_tick = time.monotonic()

    def _input(self, name, path=None):
        if name == "recordings":
            if path is None:
                pointer = ROOT / "var/last-recording-cache.txt"
                if not pointer.exists():
                    raise ValueError("No recordings cache. Run python scripts/manage.py preprocess first.")
                path = Path(pointer.read_text(encoding="utf-8").strip())
            path = path.resolve()
        key = (name, str(path))
        if key in self.loaded_inputs:
            return self.loaded_inputs[key]
        metadata = {}
        if name == "recordings":
            from backend.ingestion.recordings import load_cache
            cache = load_cache(path)
        elif name == "foundation":
            cache = prepare_fixture_cache(ROOT / "config/foundation_scenario.json", self.cache_dir)
        else:
            from backend.ingestion.replay import load_scenario, scenario_metadata
            cache = load_scenario(name, self.cache_dir)
            metadata = scenario_metadata(name)
        metadata = dict(metadata, scenario_id=name)
        from .reactions import REACTION_VERSION, reaction_policy
        context = RunInput(name, cache, metadata, digest((cache.cache_key, self.model, self.limits, "g3-reactions-v1", metadata, REACTION_VERSION, reaction_policy())), path)
        self.loaded_inputs[key] = context
        return context

    @property
    def cache(self):
        return self.contexts[self.active_run_id].cache

    def context(self, run_id=None):
        return self.contexts[run_id or self.active_run_id]

    def _new_frame(self, run_id, context):
        if context.name == "foundation":
            payload = build_snapshot(run_id, context.cache, self.fixture, self.model, self.limits, self.venue)
            payload = payload.model_copy(update={"configuration_fingerprint": context.fingerprint})
            broker, audit = None, []
        else:
            from backend.execution.paper import BrokerState
            from .media_projection import project
            from .replay_engine import advance
            initial = project(run_id, context.cache, 0, 1, False, context.fingerprint, self.venue, context.metadata)
            payload, broker, audit = advance(initial, context.cache, context.metadata, context.fingerprint, self.venue, BrokerState(run_id), 0, 1, False, initial=True)
        return StreamEnvelope(run_id=run_id, sequence=1, generated_at=utc_now(), payload=payload), broker, audit

    def snapshot(self, run_id=None):
        return self.frames[run_id or self.active_run_id]

    async def start(self):
        await self._replace_venue(self.venue)
        for run_id, old in list(self.frames.items()):
            if old.payload.playback.playing:
                frame = self._paused(old)
                self.store.commit(frame)
                self.frames[run_id] = frame
        self.playback_task = asyncio.create_task(self._playback_loop())
        if self.live_quotes:
            self.client = httpx.AsyncClient(timeout=8, limits=httpx.Limits(max_connections=2))
            self.task = asyncio.create_task(self._poll_venue())
            self.freshness_task = asyncio.create_task(self._expire_venue_quotes())

    @staticmethod
    def _paused(old):
        payload = old.payload.model_copy(update={"playback": old.payload.playback.model_copy(update={"playing": False}), "run_status": "paused"})
        return StreamEnvelope(run_id=old.run_id, sequence=old.sequence + 1, generated_at=utc_now(), payload=payload)

    def _project_playback(self, old, position, speed, playing, manual_exit=None):
        from backend.execution.paper import BrokerState
        from .replay_engine import advance
        context = self.context(old.run_id)
        loaded = self.store.load_broker(old.run_id)
        revision, broker = loaded if loaded else (0, BrokerState(old.run_id))
        payload, broker, audit = advance(old.payload, context.cache, context.metadata, context.fingerprint, self.venue, broker, position, speed, playing, manual_exit=manual_exit)
        return StreamEnvelope(run_id=old.run_id, sequence=old.sequence + 1, generated_at=utc_now(), payload=payload), (revision, broker), audit

    async def _playback_loop(self):
        while True:
            await asyncio.sleep(.25)
            async with self.lock:
                tick = time.monotonic()
                elapsed, self.last_tick = tick - self.last_tick, tick
                old = self.snapshot()
                playback = old.payload.playback
                if not playback.playing:
                    continue
                position = min(playback.duration_seconds, round(playback.position_seconds + elapsed * playback.speed, 3))
                frame, broker, audit = self._project_playback(old, position, playback.speed, position < playback.duration_seconds)
                self.store.commit(frame, broker_state=broker, audit_snapshots=audit)
                self.frames[old.run_id] = frame

    async def _expire_venue_quotes(self):
        while True:
            await asyncio.sleep(1)
            previous = self.venue
            if any(not q.is_stale and (utc_now() - q.captured_at).total_seconds() >= 10 for q in previous.quotes):
                stale = [q.model_copy(update={"quote_mode": "cached_stale", "is_stale": True}) for q in previous.quotes]
                await self._replace_venue(previous.model_copy(update={"status": "error", "error": "Actual quote expired while awaiting a fresh response.", "quotes": stale}))

    async def _replace_venue(self, context):
        async with self.lock:
            self.venue = context
            for run_id, old in list(self.frames.items()):
                if old.payload.venue_context == context:
                    continue
                payload = old.payload.model_copy(update={"venue_context": context})
                envelope = StreamEnvelope(run_id=run_id, sequence=old.sequence + 1, generated_at=utc_now(), payload=payload)
                self.store.commit(envelope)
                self.frames[run_id] = envelope

    async def _poll_venue(self):
        delay = 3
        while True:
            try:
                context, raw = await fetch_context(self.client, self.registry)
                self.store.capture(digest(raw), raw)
                await self._replace_venue(context)
                delay = 3
            except (httpx.HTTPError, ValueError, KeyError, TypeError, ArithmeticError) as error:
                previous = self.venue
                stale = [q.model_copy(update={"quote_mode": "cached_stale", "is_stale": True}) for q in previous.quotes]
                context = previous.model_copy(update={"status": "error", "error": f"Public quote fetch failed: {type(error).__name__}: {str(error)[:200]}", "quotes": stale})
                await self._replace_venue(context)
                delay = min(delay * 2, 30)
            await asyncio.sleep(delay)

    async def _activate(self, context, scope, command_id, payload_hash, previous_run_id=None):
        run_id = stable_id("run", scope, command_id, context.fingerprint)
        frame, broker, audit = self._new_frame(run_id, context)
        prior = self._paused(self.snapshot()) if self.snapshot().payload.playback.playing else None
        result = CommandResult(command_id=command_id, run_id=run_id, previous_run_id=previous_run_id)
        self.store.commit(frame, command=(scope, command_id, payload_hash, result), active=True,
            broker_state=(0, broker) if broker else None, audit_snapshots=audit, run_input=context.saved(), prior_envelope=prior)
        if prior:
            self.frames[prior.run_id] = prior
        self.frames[run_id], self.contexts[run_id] = frame, context
        self.active_run_id = run_id
        self.last_tick = time.monotonic()
        return result

    async def create_run(self, request: CreateRunRequest):
        async with self.lock:
            payload_hash = digest(request.model_dump())
            previous = self.store.command("create", request.command_id, payload_hash)
            if previous:
                return previous
            context = self._input(request.scenario) if request.scenario else self.context()
            return await self._activate(context, "create", request.command_id, payload_hash)

    async def inject(self, run_id, request):
        # New synthetic occurrence; never mix fixtures into recorded evidence.
        async with self.lock:
            self.snapshot(run_id)
            scope, payload_hash = "inject:" + run_id, digest(request.model_dump())
            previous = self.store.command(scope, request.command_id, payload_hash)
            if previous:
                return previous
            if run_id != self.active_run_id:
                raise ValueError("Only the active run can select a synthetic scenario")
            return await self._activate(self._input(request.scenario), scope, request.command_id, payload_hash, run_id)

    async def control(self, run_id, request: RunCommand):
        async with self.lock:
            self.snapshot(run_id)
            payload_hash = digest(request.model_dump())
            previous = self.store.command(run_id, request.command_id, payload_hash)
            if previous:
                return previous
            if run_id != self.active_run_id or run_id not in self.contexts:
                raise ValueError("Controls require the active run with unchanged source/config versions")
            if request.action == "replay_observation":
                result = CommandResult(command_id=request.command_id, run_id=run_id, duplicate_observation=True)
                self.store.commit(command=(run_id, request.command_id, payload_hash, result))
                return result
            if request.action == "reset":
                return await self._activate(self.context(), run_id, request.command_id, payload_hash, run_id)
            if self.context().name == "foundation":
                raise ValueError("G1 diagnostic supports reset/re-delivery only; select a G3 replay")
            old = self.snapshot(run_id)
            playback = old.payload.playback
            position, speed, playing = playback.position_seconds, playback.speed, playback.playing
            if request.action == "seek":
                if request.position_seconds > playback.duration_seconds:
                    raise ValueError("Seek exceeds replay duration")
                position = request.position_seconds
            elif request.action == "set_speed":
                speed = request.speed
            elif request.action == "play":
                playing = position < playback.duration_seconds
            elif request.action == "pause":
                playing = False
            elif request.action == "exit":
                if not old.payload.execution.enabled or not old.payload.execution.positions:
                    raise ValueError("Exit requires an open position in a fully synthetic paper run")
            if position >= playback.duration_seconds:
                playing = False
            frame, broker, audit = self._project_playback(old, position, speed, playing,
                manual_exit=request.command_id if request.action == "exit" else None)
            result = CommandResult(command_id=request.command_id, run_id=run_id)
            self.store.commit(frame, command=(run_id, request.command_id, payload_hash, result), broker_state=broker, audit_snapshots=audit)
            self.frames[run_id] = frame
            self.last_tick = time.monotonic()
            return result

    async def close(self):
        for task in (self.task, self.freshness_task, self.playback_task):
            if task:
                task.cancel()
        for task in (self.task, self.freshness_task, self.playback_task):
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        if self.client:
            await self.client.aclose()
        self.store.close()

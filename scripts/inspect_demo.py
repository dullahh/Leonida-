"""Operational replay health/transport inspection with an isolated ASGI lifespan.

The future tester owns the formal invariant suite. This utility awaits shutdown
in-process to avoid orphaned Windows venv launcher children holding SQLite open.
"""
import argparse
import asyncio
import json
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
import uvicorn
from websockets.asyncio.client import connect
from backend.core.schemas import StreamEnvelope
from backend.main import create_app


async def inspect(url: str, server_task=None, seek_end=False) -> dict:
    async with httpx.AsyncClient(base_url=url, timeout=15, trust_env=False) as client:
        deadline = asyncio.get_running_loop().time() + 20
        while True:
            try:
                response = await client.get("/ready")
                response.raise_for_status()
                break
            except httpx.HTTPError:
                if asyncio.get_running_loop().time() >= deadline or (server_task and server_task.done()):
                    raise RuntimeError("Isolated app did not become ready")
                await asyncio.sleep(.1)
        readiness = response.json()
        response = await client.get("/api/state")
        response.raise_for_status()
        envelope = StreamEnvelope.model_validate_json(response.text)
        if seek_end and envelope.payload.gate in {"G2", "G3"}:
            response = await client.post(f"/api/runs/{envelope.run_id}/control", json={"command_id": "inspect-seek-end", "action": "seek", "position_seconds": envelope.payload.playback.duration_seconds})
            response.raise_for_status()
            response = await client.get("/api/state")
            response.raise_for_status()
            envelope = StreamEnvelope.model_validate_json(response.text)
        websocket_url = url.replace("http://", "ws://").replace("https://", "wss://")
        async with connect(websocket_url + "/ws?run_id=" + envelope.run_id, open_timeout=3, proxy=None, max_size=16 * 1024 * 1024) as websocket:
            socket_frame = StreamEnvelope.model_validate_json(await asyncio.wait_for(websocket.recv(), timeout=3))
        if socket_frame != envelope:
            raise RuntimeError("REST and WebSocket do not share the same full snapshot")
        p = envelope.payload
        receipt_status = None
        if p.receipts:
            receipt = await client.get(f"/api/runs/{envelope.run_id}/receipts/{p.receipts[0].receipt_id}")
            receipt.raise_for_status()
            receipt_status = receipt.status_code
        trace_status = []
        for trace in p.execution.traces:
            response = await client.get(f"/api/runs/{envelope.run_id}/execution-traces/{trace.trace_id}")
            response.raise_for_status()
            trace_status.append(response.status_code)
        page = await client.get("/")
        page.raise_for_status()
        return {
            "gate": p.gate, "ready": readiness["ready"], "http_ws_equal": True,
            "viewer_http_status": page.status_code, "run_id": envelope.run_id,
            "schema": envelope.schema_version, "observations": len(p.windows), "unique_observations": len({w.observation_id for w in p.windows}),
            "feature_bucket_count": sum(f.unique_observation_count for f in p.features),
            "z": p.features[0].mean_z if p.features else None, "model_probability": p.estimates[0].model_probability if p.estimates else None,
            "candidate_side": p.decisions[0].side if p.decisions else None, "no_ev_usd": str(p.decisions[0].no_ev_per_contract) if p.decisions and p.decisions[0].no_ev_per_contract is not None else None,
            "fills": p.fill_count, "orders": p.order_count, "cash_usd": str(p.cash_usd), "realized_pnl": str(p.execution.realized_pnl),
            "scenario": p.scenario_name, "sources": len(p.streams), "receipt_status": receipt_status, "trace_status": trace_status,
            "estimate_status": "available" if p.estimates else "abstained",
            "supported_claims": sum(c.sentiment is not None and c.target == "game" for c in p.claims),
            "abstained_claims": sum(c.sentiment is None for c in p.claims),
            "limitations": readiness["limitations"], "formal_g4_suite": "not implemented",
        }


async def main_async(url: str | None, evidence_cache: Path | None = None, scenario="foundation") -> int:
    if scenario == "all" and not url:
        from backend.ingestion.replay import scenario_names
        for name in scenario_names():
            await main_async(None, None, name)
        return 0
    if url:
        report = await inspect(url.rstrip("/"))
    else:
        with tempfile.TemporaryDirectory(prefix="leonida-g1-inspect-") as directory:
            with socket.socket() as bound:
                bound.bind(("127.0.0.1", 0))
                port = bound.getsockname()[1]
            folder = Path(directory)
            app = create_app(folder / "isolated.sqlite3", folder / "cache", live_quotes=False, evidence_cache_path=evidence_cache, scenario="foundation" if scenario == "recordings" else scenario)
            server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                log_level="warning", timeout_graceful_shutdown=3))
            task = asyncio.create_task(server.serve())
            try:
                report = await inspect(f"http://127.0.0.1:{port}", task, seek_end=True)
            finally:
                server.should_exit = True
                await asyncio.wait_for(task, timeout=10)
        report["isolated_server_and_database_closed"] = True
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Read-only inspection of an existing app; does not reset its run")
    parser.add_argument("--cache", type=Path, help="Inspect a G2 recording cache in an isolated temporary run")
    parser.add_argument("--scenario", default="foundation", help="foundation, recordings (requires --cache), all, or a named synthetic scenario")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args.url, args.cache, args.scenario)))

"""One lifespan-owned SQLite writer; atomic snapshot, records and command receipts."""
import json
import sqlite3
from pathlib import Path

from .schemas import CommandResult, StreamEnvelope


class StateStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL, envelope TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS records(run_id TEXT NOT NULL, kind TEXT NOT NULL, record_id TEXT NOT NULL,
            payload TEXT NOT NULL, PRIMARY KEY(run_id,kind,record_id));
        CREATE TABLE IF NOT EXISTS commands(scope TEXT NOT NULL, command_id TEXT NOT NULL, payload_hash TEXT NOT NULL,
            result TEXT NOT NULL, PRIMARY KEY(scope,command_id));
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS broker_states(run_id TEXT PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS execution_records(run_id TEXT NOT NULL,revision INTEGER NOT NULL,kind TEXT NOT NULL,record_id TEXT NOT NULL,
            payload TEXT NOT NULL,PRIMARY KEY(run_id,revision,kind,record_id));
        CREATE TABLE IF NOT EXISTS venue_captures(capture_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS run_inputs(run_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
        """)

    def load(self, run_id: str) -> StreamEnvelope | None:
        row = self.connection.execute("SELECT envelope FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return StreamEnvelope.model_validate_json(row[0]) if row else None

    def all_runs(self) -> list[StreamEnvelope]:
        return [StreamEnvelope.model_validate_json(row[0]) for row in self.connection.execute("SELECT envelope FROM runs")]

    def active(self) -> str | None:
        row = self.connection.execute("SELECT value FROM metadata WHERE key='active_run' ").fetchone()
        return row[0] if row else None

    def command(self, scope: str, command_id: str, payload_hash: str) -> CommandResult | None:
        row = self.connection.execute("SELECT payload_hash,result FROM commands WHERE scope=? AND command_id=?", (scope, command_id)).fetchone()
        if row and row[0] != payload_hash:
            raise ValueError("command_id was already used with a different payload")
        return CommandResult.model_validate_json(row[1]) if row else None

    def commit(self, envelope: StreamEnvelope | None = None, *, command: tuple | None = None, active: bool = False, broker_state: tuple[int, object] | None = None, audit_snapshots=(), run_input=None, prior_envelope=None) -> None:
        with self.connection:
            if run_input is not None:
                self.connection.execute("INSERT INTO run_inputs VALUES(?,?)", (envelope.run_id, json.dumps(run_input)))
            if prior_envelope is not None:
                prior = self.load(prior_envelope.run_id)
                if prior is None or prior_envelope.sequence != prior.sequence + 1:
                    raise ValueError("prior run snapshot revision conflict")
                self.connection.execute("UPDATE runs SET sequence=?,envelope=? WHERE run_id=?", (prior_envelope.sequence, prior_envelope.model_dump_json(), prior_envelope.run_id))
            if broker_state is not None:
                from backend.execution.paper import dump_state, load_state
                expected_revision, state = broker_state
                serialized = dump_state(state)
                validated = load_state(serialized)
                if envelope is not None and envelope.run_id != validated.run_id:
                    raise ValueError("broker plan and envelope run disagree")
                row = self.connection.execute("SELECT revision FROM broker_states WHERE run_id=?", (validated.run_id,)).fetchone()
                actual_revision = row[0] if row else 0
                if actual_revision != expected_revision:
                    raise ValueError("broker revision conflict")
                revision = actual_revision + 1
                self.connection.execute("INSERT INTO broker_states VALUES(?,?,?) ON CONFLICT(run_id) DO UPDATE SET revision=excluded.revision,payload=excluded.payload",
                    (validated.run_id, revision, serialized))
                raw = json.loads(serialized)
                for kind, field in (("orders", "order_id"), ("fills", "fill_id")):
                    for record in raw[kind]:
                        self.connection.execute("INSERT INTO execution_records VALUES(?,?,?,?,?)", (validated.run_id, revision, kind, record[field], json.dumps(record)))
            if envelope:
                previous = self.load(envelope.run_id)
                expected = 1 if previous is None else previous.sequence + 1
                if envelope.sequence != expected:
                    raise ValueError("snapshot revision conflict")
                self.connection.execute("INSERT INTO runs VALUES(?,?,?) ON CONFLICT(run_id) DO UPDATE SET sequence=excluded.sequence,envelope=excluded.envelope",
                    (envelope.run_id, envelope.sequence, envelope.model_dump_json()))
                for snapshot in (*audit_snapshots, envelope.payload):
                    for kind, field in (("windows", "window_id"), ("claims", "claim_id"), ("reactions", "reaction_id"), ("groups", "group_id"), ("markets", "market_id"), ("features", "feature_id"), ("quotes", "quote_id"), ("estimates", "estimate_id"), ("decisions", "decision_id"), ("receipts", "receipt_id")):
                        for record in getattr(snapshot, kind):
                            # Groups carry an evolving membership; immutable
                            # members/claims remain available in each snapshot.
                            record_id = getattr(record, field)
                            if kind == "groups":
                                from .identity import digest
                                record_id += ":" + digest(record.claim_ids)
                            self.connection.execute("INSERT OR IGNORE INTO records VALUES(?,?,?,?)",
                                (envelope.run_id, kind, record_id, record.model_dump_json()))
                if active:
                    self.connection.execute("INSERT INTO metadata VALUES('active_run',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (envelope.run_id,))
            if command:
                scope, command_id, payload_hash, result = command
                self.connection.execute("INSERT INTO commands VALUES(?,?,?,?)", (scope, command_id, payload_hash, result.model_dump_json()))

    def load_broker(self, run_id: str):
        from backend.execution.paper import load_state
        row = self.connection.execute("SELECT revision,payload FROM broker_states WHERE run_id=?", (run_id,)).fetchone()
        return (row[0], load_state(row[1])) if row else None

    def inputs(self):
        return {row[0]: json.loads(row[1]) for row in self.connection.execute("SELECT run_id,payload FROM run_inputs")}

    def record(self, run_id, kind, record_id):
        row = self.connection.execute("SELECT payload FROM records WHERE run_id=? AND kind=? AND record_id=?", (run_id, kind, record_id)).fetchone()
        return json.loads(row[0]) if row else None

    def capture(self, capture_id: str, payload: dict) -> None:
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO venue_captures VALUES(?,?)", (capture_id, json.dumps(payload)))

    def close(self):
        self.connection.close()

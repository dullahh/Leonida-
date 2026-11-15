Execute G0 and G1 of PLAN.md as root integrator. Implementation is authorised within this repository; paper-only.

First read current AGENTS.md, docs/STATE.md and any implementation plan. Inspect actual dependencies/version/tooling. Keep the existing frontend framework if present; otherwise React/TypeScript/Vite. Root owns shared files and Python dependencies.

Do not spawn implementation workers until a minimal vertical slice works:
1. Adopt/finalise contracts/models.py into backend/core/schemas.py and establish schema v1.
2. Create clock/config/storage/runtime/projector interfaces and one synthetic replay observation.
3. Feed it through a minimal real feature/estimate/paper-decision path.
4. Expose health/ready/state and one full WebSocket snapshot.
5. Create one frontend state viewer or equivalent integration proof.
6. Export JSON Schema/example payloads and root-owned generated TypeScript.
7. Establish commands make setup/demo/check/demo-check with no-key replay defaults.

Refresh known market seed definitions through the public API if reachable. Save actual original responses and capture time only; otherwise record the failure and use a separate explicitly synthetic replay quote fixture. Never fabricate a live snapshot.

Write initial runtime composition and narrowly scoped placeholders behind the frozen interfaces, clearly marked. The implementation workers will replace their owned placeholders. Record exact signatures and examples.

G1 gate: one deterministic observation reaches a visible snapshot with an evidence ID, a model estimate labelled heuristic, side-specific candidate EV and provenance. Publish updated STATE/DECISIONS/TASKS. Validate imports/schema examples. Do not claim the full app is built.

Then return a concise handoff ready for prompt 02. No live-money routes or keys.


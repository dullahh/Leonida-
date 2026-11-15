# Leonida Alpha project instructions

Build a multi-stream evidence and prediction-market research desk with paper execution. Read PLAN.md sections 1–6 before changing shared foundations; read only assigned further sections for a worker job.

## Delegation and ownership
The root is the integrator. Explicitly delegate independent implementation tasks to pipeline_engineer, quant_engineer and frontend_engineer after G1. At most three spawned workers run simultaneously. Workers never spawn workers.

Root owns contracts/, backend/core/, backend/main.py, config/, scripts/, root dependencies/lockfiles, data/snapshots/, .codex/, docs/, generated frontend types and runtime processes.
Pipeline owns backend/ingestion/, backend/perception/, data/scenarios/, data/recordings/ manifests and handoffs/pipeline.md.
Quant owns backend/quant/, backend/execution/ and handoffs/quant.md.
Frontend owns frontend/ except generated types, and handoffs/frontend.md.
Tester owns tests/ and handoffs/tester.md; only tester creates test source. Other roles run existing tests and focused checks.
Reviewer does not edit application files; write handoffs/reviewer.md only if explicitly assigned.

Do not edit another owner's files. Submit a precise contract/dependency request and continue independent work. Root decides routine changes and coordinates consumers. Never perform broad git add/reset/clean/checkout/commit from a shared worker. Root owns integration/commits and server process lifecycle.

## Non-negotiable behaviour
- Use stable event/claim/intent IDs, run IDs and explicit schema/model versions.
- Raw source data, features, quotes, estimates, decisions, orders and fills are separate contracts.
- Missing modalities/quotes are null with reason, not neutral/zero.
- Keep absolute sentiment and pre-update rolling surprise separately.
- No sqrt(N) signal inflation or viewer-count accuracy assumptions.
- Relevance weights are nonnegative; encode evidence direction exactly once.
- No direct face-derived game approval in the MVP.
- Recompute the bounded market-relative correction from unique evidence; timer refreshes never add evidence.
- Label unvalidated coefficients and estimates heuristic. Do not call them calibrated Bayesian posteriors.
- Actual market tickers/rules are resolved from venue data. Never invent live tickers or spreads.
- Preserve live/recorded/synthetic evidence, live/stale/synthetic quote and paper execution modes throughout.
- Stale quotes prohibit normal new paper fills. Synthetic replay uses its own explicit quote timeline.
- Accounting is Decimal, side-specific and quantity/fee/depth-aware.
- Paper-only scope; do not add real-money order routes.
- Singleton/ambiguous evidence is allowed with explicit reliability or abstention.
- Root owns one SQLite writer and shared state. Tests use isolated databases/run IDs.

## Execution
Follow G0–G5 gates, not optimistic minute promises. Build one replay vertical slice before parallel expansion. Keep no-key deterministic replay working.

Worker handoff: changed paths; public interfaces; check commands/results; limitations; blockers; integration actions. Root persists docs/STATE.md and docs/DECISIONS.md.

Do not claim a test passed unless it ran. Do not claim a live source works without actual observations. Do not fill unavailable media or model output with unlabelled fabricated content.


You are the root planner for Leonida Alpha. This task is planning/design, not application implementation.

Read AGENTS.md, README.md and PLAN.md. Inspect the actual repository, installed Codex version/help, available package managers and existing stack. Preserve existing work and project instructions.

Use two directly spawned read-only workers: one reviews quant/data/execution correctness; one reviews source feasibility/UI/runtime integration. Workers may not delegate. Give each only the relevant PLAN.md sections and ask for a concise actionable report.

In the main thread verify the installed Codex configuration/custom-agent support against current official documentation. Do not assume legacy max_depth, a particular retired model, MCP availability or raw Twitch A/V access.

Produce or update:
- docs/IMPLEMENTATION_PLAN.md: concrete architecture, retained stack, module signatures and dependency DAG.
- docs/STATE.md: actual capabilities, source modes, gate and blockers.
- docs/DECISIONS.md: resolved choices and remaining consequential unknowns.
- docs/TASKS.md: bounded jobs with exact owned paths and acceptance gates.

Adopt the corrected mathematical/provenance rules from PLAN.md. Flag any proposed deviation with its reason. Assume paper-only and no-key replay unless the user supplies a different instruction.

Include an honest cut line and several-hour gate-based schedule. Make ordinary implementation choices autonomously. Ask only a genuinely blocking question; continue independent planning meanwhile.

Wait for both review workers, reconcile their findings, then return the concrete plan and which implementation prompt begins G1. Do not start application code in this planning task.


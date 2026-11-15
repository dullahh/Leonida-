Run isolated browser QA after backend/frontend readiness. Root starts and owns the servers. Spawn qa_reviewer; no application-file edits.

Use available browser tooling/Playwright MCP if installed; otherwise an existing browser test runner. Do not assume MCP is available or install a suite of unrelated servers.

QA creates/selects its own synthetic replay run:
- Inspect all six scenario controls and receipts.
- Confirm modes/freshness/calibration and units.
- Check absolute sentiment differs from surprise.
- Inspect narrative praise, bug-plus-laughter, skill null, disagreement/missing facecam.
- Reconnect/drop/restore state, reset, and verify no old-run contamination.
- Trigger quote outage and confirm paper entries pause.
- Inspect paper entry/partial/no-fill/exit accounting, not just a trade badge.
- Check laptop/projector layout and narrow layout.
- Collect browser console/network evidence and screenshots.

Browser clicks change replay state; never act in another user's run. Report severity, exact reproduction, expected/actual behaviour, run/scenario and suspected owner. Root assigns fixes to file owners and reruns relevant checks.


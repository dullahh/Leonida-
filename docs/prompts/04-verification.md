Execute G4 verification. Spawn tester with exclusive tests/ ownership and handoffs/tester.md. Tester may not edit production files or manifests; request fixes/dependencies through root.

Cover PLAN section 17's meaningful invariants, prioritising:
- Missing vs neutral; pre-update/warmup z; finite constant input.
- Duplicate events/timer refreshes do not add evidence/orders.
- No sqrt(N) amplification; negative bug direction once; skill/null and mixed claims.
- Quote movement updates anchor with constant evidence correction.
- Correct No ask entry and held-side bid MTM/exit.
- Order-level fees/rounding/cash/depth/partial fills/group cap.
- Stale/missing quotes and mode gates.
- Fixed-seed 1x/5x replay equivalence.
- WS reconnect/state resync/reset old-message rejection.
- Threshold/event coherence.

Use isolated temporary DBs and run IDs. No network/provider calls required for deterministic tests. Do not chase a test-count target or mirror implementation lines.

Root runs existing smoke/build checks in parallel, without changing active production worker files. When tester reports a failure, send it to one owner, wait for the patch, rerun the affected checks, then run the required acceptance suite once.

Return actual commands, pass/fail results and material limitations. Update STATE. No fabricated green checkmarks.


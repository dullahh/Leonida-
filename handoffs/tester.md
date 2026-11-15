# G3 focused acceptance handoff

Completed 15 November 2026. This is the focused G3 integration acceptance suite;
the broader G4 verification gate was not started or claimed. No workers were
delegated. Only tester-owned paths were changed. Existing backend/frontend code
and generated contracts were inspected; no application, dependency, scenario,
shared database or runtime process was modified. `git status --short` reported
that this workspace is not a Git repository.

## Changed paths and interface

- `tests/g3/test_acceptance.py`: nine stdlib `unittest` integration checks.
- `handoffs/tester.md`: this handoff.

Run from repository root:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests/g3 -p 'test_*.py' -v
```

Root may invoke that command from `python scripts/manage.py check --gate G3`.
No added package or test dependency is needed. Each test owns temporary SQLite
databases, fixture cache directories and isolated run IDs. Actual recording
evidence is read from the verified immutable local cache without OCR, ASR,
decoding, network calls or cache writes.

## Verification actually executed

The command above exited **0**: **9 tests passed in 5.320 seconds, no skips**.
The local t1/t2/t3 cache was present and its recording check ran. Asyncio printed
slow-task diagnostics for synchronous in-process integration work; these were
not test failures. An unused test import was removed afterward; no behavioral
test or application code changed.

Verified behaviors:

- Courtroom praise has six statuses and an explicit synthetic reaction that
  moves the estimate above its 0.5 anchor. A pending 10-contract request cannot
  fill at 249ms; at 250ms it fills six contracts and cancels residual depth.
  Cash becomes `9996.925`, entry fee is `.06`, and reservation is released.
- A 300-second time exit sees only four priced contracts and two unpriced.
  Exit fills of four then two close the position. Total fees are `.12`, final
  cash is `10000.0800` and realized P&L is `.0800`, computed from the explicitly
  synthetic timeline. Six immutable plan/eligibility traces retain supported
  source text and persistent feature/quote/estimate/decision/receipt references.
- Technical failure remains a negative technical feature with no narrative
  estimate; laughter abstains and shared dependency has effective count one.
  Skill-only claims are excluded while negative control/gameplay claims remain.
  Mixed evidence shows disagreement, absent facecam and cancelled pending entry.
  Duplicate/reconnect fixture keeps one partial entry and six-contract position.
- Outage quote becomes stale at exactly 10 seconds. Current estimate/decision
  become unavailable, not neutral. Eligibility at 10.15 seconds cancels the
  pending entry with no fill, no reservation and unchanged cash.
- Repeated same command returns the prior result without changing sequence or
  broker state; changed payload under the same command ID is rejected. Reads
  and observation re-delivery do not ingest or execute. Reset has a new run ID,
  keeps old audit state, is idempotent and rejects subsequent old-run controls.
- Restart preserves pending orders without executing them during restore. An
  explicit later advance fills once; subsequent restart pauses playback while
  preserving the exact filled broker ledger and position.
- A deliberate duplicate-command SQLite failure after staged broker, envelope
  and audit writes rolls back the entire transaction. The DB dump, broker
  revision/state and visible envelope remain unchanged; a later valid retry
  fills once.
- Different 1x/5x publication partitions produce equivalent event-time
  observations, features, estimates, decisions, order timing, fills, positions,
  cash and realized P&L after excluding run-scoped IDs. Quote-only refresh
  changes the market anchor without changing source baseline statistics/counts.
- Actual recordings retain 105/221/303 observations for t1/t2/t3: 629 unique
  recorded GTA V proxy observations, all with null sentiment and a reason.
  They have no groups, features, estimates, decisions, orders or fills. Actual
  venue context has no effect on the proxy estimate. Selecting the qualifying
  fixture creates a separate synthetic run and leaves the real recording run
  unchanged.

## Limits and integration actions

No production defect or dependency blocker was found in these checks. Root
still owns HTTP/WS and browser acceptance, launcher integration, current process
lifecycle and the G3 acceptance report. This suite uses the runtime's isolated
in-process APIs, not a browser or real socket reconnect. It does not claim new
live venue observations, forecasting calibration, OCR/ASR recognition accuracy,
real venue liquidity/fees or G4 completion.

The local recording test skips with an explicit reason on a checkout lacking
the verified unbundled cache. It did **not** skip in this session. Scenario
fixture loading writes only within each test's temporary cache. Root should
rerun the command after material runtime/schema/scenario changes.

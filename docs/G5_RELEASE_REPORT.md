# G5 local release candidate - 15 November 2026

Starting commit:74d69491c512dfe472f56a9a792f65c28ae6dc46. One thread; no agents. G4's browser coverage was retained and release browser work was limited to final startup modes and the pitch sequence. No analytical features, probability changes, OCR/ASR reruns, model downloads, provider additions, deployment, publication or remote push occurred.

## Supported modes

After installation with `python scripts/manage.py setup`:

```powershell
python scripts/manage.py demo --scenario recordings
python scripts/manage.py demo --scenario portable
```

Default `python scripts/manage.py demo` selects available local recordings/cache or explains its fallback to the portable Courtroom fixture. Open http://127.0.0.1:8000. Local mode uses the existing immutable five-recording cache, with1651 original observations and no supported quality claims. Portable mode runs from tracked deterministic fixtures with no private videos, speech model, API credential or runtime network access. Its synthetic evidence, prices and execution remain visibly labelled.

Separate default databases are `var/demo-recordings.sqlite3` and `var/demo-portable.sqlite3`. Explicit `--db` and `--port` remain supported. Matching saved inputs resume paused; another saved scenario cannot override the requested launch mode. Old audit is retained. Stop an existing server before binding its port.

The primary existing local server on8000 was left intact. Temporary release rehearsal servers on8002/8003 were owned by root and stopped after verification. Run the commands above for a fresh release launch, using another port if necessary.

## Minimal release fixes

1. Startup previously selected foundation with no cache and errored for a missing explicit recording cache. Added file-only launch selection: cached local media when available, otherwise a clear portable synthetic Courtroom fallback. No extraction/download is triggered. Explicit `portable` is a launch alias for the existing scenario.
2. Saved run-input restoration could fail before fixture startup when an old local cache disappeared. Unavailable old inputs now leave audit readable without blocking the selected fixture.
3. A saved active scenario could override an explicitly selected mode, including portable mode. Startup now restores only matching input fingerprints; selecting recordings cannot silently restore an old outage run. Regression verified old audit retained.
4. Updated stale check output and judge documentation. Existing replay controls completed the pitch reliably; no UI/navigation/analytical changes were necessary.

Changes are limited to root startup/launch code,4 focused release tests, README and release/status documents. Thresholds, coefficients, claim classifier, reaction rules, paper-broker methodology, original caches/media and frontend source remain unchanged.

## Verification actually executed

| Check | Result |
|---|---|
| Clean source-only copy | Copied tracked source paths with current release edits into ignored `var/g5-source-only`. No recordings, models, evidence cache, DB, dependency tree or virtual environment was copied. |
| Frozen Python setup offline | `uv sync --offline --frozen --cache-dir C:/Users/abdul/Desktop/drhck/.cache/uv` installed51 locked packages into a new virtual environment. |
| Frozen npm setup offline | Root and frontend `npm ci --offline --cache C:/Users/abdul/Desktop/drhck/.cache/npm --no-audit --no-fund` succeeded; clean frontend build passed. |
| Portable source-only launch | Explicit portable launch and default missing-local fallback both started on8002. Final state Courtroom,0 local files, paused; browser displayed Synthetic demo, no video requests and no external requests. |
| Full local launch | Root launch on8003 loaded all5 videos and the unchanged composed evidence cache. After final startup fix, re-launch selected recordings instead of the saved outage scenario. |
| Existing G3 checks | Final `python scripts/manage.py check --gate G3`:15 tests, zero skips, generated schema/OpenAPI/type checks, six fixtures and frontend typecheck/build passed. |
| G4 plus release regressions | Final `.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v`:10 tests, zero skips,47.380s. Existing G4 tests preserved;4 startup cases added. |
| Existing operational smoke | `python scripts/manage.py demo-check --scenario all`: all6 isolated HTTP/WS fixture inspections passed with receipts/traces and clean database closure. |
| Final rehearsal | Full flow completed in22.4s of control operation, using seeks; narration expands it to3 minutes. Five decoded players, reaction exclusion, Courtroom quality/estimate/receipts,6-contract partial fill,4+2 exits and stale cancellation passed. |
| Release browser state | Installed Edge: no page/console errors, no portable external requests,1440px desktop and390px narrow layouts without horizontal overflow. G4 remains the evidence for broader reset/reconnect/accounting coverage. No cross-browser certification claimed. |
| Repository hygiene | Tracked paths checked for video/audio/model/DB/image/cache/venv/dependency artifacts: no matches. Common private-key/token signature scan: no matches. Ignore rules retain local artifacts and secret-file exclusions. This is a bounded scan, not a comprehensive security audit. |

Final startup state was read back over HTTP:8002 Courtroom/no local videos;8003 recordings/5 local videos; both paused. No production test failure remained. The release gaps above were found by inspection and exercised by focused regression tests; broader checks were rerun after the final mode-restoration fix.

Local ignored evidence: `var/g5-final-g3.log`, `g5-final-g4.log`, `g5-smoke.log`, `var/g5-review/rehearsal.json`, `final-startup.json`, `recording-exclusion.png`, `portable-desktop.png`, `release-narrow.png`. The clean source copy and its installed dependencies remain ignored local verification artifacts.

## Three-minute pitch

Exact timed controls/narration: [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Judge summary is in README; release sign-off is [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

0:00 playback/telemetry;0:30 ambiguous-reaction exclusion;0:55 load labelled Courtroom and seek2s;1:25 source/eligibility receipts and6/10 fill;1:50 seek310s for completed exits;2:20 load outage and seek10.2s for stale cancellation;2:45 limitations and return to recordings. In portable-only mode, explain that private recordings are absent and begin with the labelled fixture instead of claiming real footage is present.

## Honest remaining limitations

- First installation needs internet or populated dependency caches. Offline replay does not imply that missing Python/npm packages can be installed from nothing. Portable mode requires no separate speech-model download.
- Supplied footage and caches are local/untracked. All recorded quality opinions currently abstain; speaker verification remains pending and OCR/ASR text can be wrong. Text reaction labels do not measure actual emotion or acoustic arousal.
- Courtroom evidence/baselines are supplied fixtures. Quote movement, depth, fees, latency, fills and exits are simulated. The bounded market-relative estimate is heuristic and uncalibrated; the tiny authored profit is not predictive validation.
- Actual GTA VI venue context remains historical/stale and separate from GTA V proxy evidence. No new live source, live execution or calibrated edge is claimed.
- Windows Proactor/socket teardown warnings observed in G4 can still occur despite clean browser console checks. No unrelated platform refactor was attempted.
- A valid-looking but corrupt evidence cache may still fail strict integrity validation; fallback handles unavailable/malformed launch inputs and missing artifacts/media, and never bypasses cache integrity checks. Long recordings, other codecs/browsers and general multilingual semantics remain outside this release evidence.
- Future research: as-of historical game/year data; held-out calibration; market-only/competitor baselines; actual venue fee/depth and execution evaluation. These are not release features.

The release is local only. G3/G4 commits remain intact; final commit title is `G5 demo release`. No push/deployment was attempted. Stop here.

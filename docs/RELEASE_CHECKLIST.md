# Local release candidate checklist

Base:74d69491c512dfe472f56a9a792f65c28ae6dc46. Date:15 November2026. One thread; no agents, remote publication or push.

- [x] Read browser/release prompts, G4 report and README. Existing G4 browser evidence retained.
- [x] Local launch selects the existing five-file cache; no OCR/ASR rerun or model/provider call.
- [x] Explicit `--scenario portable` uses tracked Courtroom fixture.
- [x] Default/recordings startup explains missing local files/cache and falls back to portable synthetic Courtroom.
- [x] Missing old run inputs cannot prevent starting a fixture; old audit is preserved.
- [x] Separate default DB paths for recordings and portable launches; explicit --db remains available.
- [x] Clean copy built from tracked source paths, without local videos, cache, models, DBs, dependencies or virtual environment copied in.
- [x] Frozen Python and npm dependencies installed offline using existing package caches; clean frontend build passed.
- [x] Source-only portable app launched on8002 with no media or speech model; no external browser requests.
- [x] Full local app launched on8003; five decoded videos and reaction exclusion displayed.
- [x] Existing G3 checks:15 tests, contract/type consistency and frontend build passed.
- [x] G4 suite plus startup/launch-isolation cases (final results in release report).
- [x] Final rehearsal completed source/telemetry/claim/estimate/fill/exit/receipt/outage sequence using seeks.
- [x] Release desktop1440/narrow390 browser checks passed with no console errors or horizontal overflow.
- [x] Tracked-file scan found no media, model weights, databases, cache directories, screenshots, virtual environments or dependency trees.
- [x] Common private-key/token signature scan found no matches; secret-file patterns remain ignored. This is not a comprehensive security audit.
- [x] Judge-facing README, three-minute script and final report prepared.
- [ ] Deploy/publish/push: deliberately not part of this local release.

Verification commands:

```powershell
python scripts/manage.py check --gate G3
.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v
python scripts/manage.py demo-check --scenario all
```

Clean offline install verification used `uv sync --offline --frozen --cache-dir <existing-uv-cache>`, root and frontend `npm ci --offline --cache <existing-npm-cache>`, then frontend build. First installation on a machine without dependencies/caches requires internet or supplied offline packages; replay itself needs no network or API key. No claim of installation from unavailable packages offline is made.

Known limitations remain in G4_VERIFICATION.md and G5_RELEASE_REPORT.md. In particular, Windows media-socket teardown warnings may appear despite a clean browser console; text reactions are not measured emotion; speaker verification remains pending; prices/fees/depth/execution are simulated and the probability model is uncalibrated.

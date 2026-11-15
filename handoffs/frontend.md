# G2 frontend handoff

Completed 15 November 2026. No delegation, root-owned edits, test-source creation, shared server lifecycle changes or publishing occurred.

## Changed paths

- `frontend/package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `.gitignore`, `README.md`.
- `frontend/src/main.tsx`, `App.tsx`, `styles.css`.
- `frontend/src/transport/useDesk.ts`.
- `frontend/src/components/Primitives.tsx`, `SourceCard.tsx`, `EvidenceArtifacts.tsx`, `ReceiptDialog.tsx`.
- `frontend/dist/` is the ignored built artifact. `frontend/.qa/` contains ignored local browser screenshots/reports.
- This handoff. Root-generated `frontend/src/generated/` was consumed, not edited.

## Public interfaces and integration

The client imports `StreamEnvelope`, nested snapshot types and `PlaybackState` from `src/generated/contracts.ts`; control bodies satisfy `RunCommand` from `src/generated/commands.ts`. It uses schema 2 with root's additive G2 contracts, preserving G1 snapshots.

Endpoints: `GET /api/state?run_id=…`, `WS /ws?run_id=…`, `POST /api/runs/{run_id}/control`, `GET /api/recordings/{asset_id}/media`, and `GET /api/evidence/artifact?ref=…`. No arbitrary local paths are fetched. Root serves the build at `/`; Vite development proxies APIs to `127.0.0.1:8000`.

`useDesk()` returns frame, connection/error/notice, busy state, reception time, refresh and typed control. One decoder and shared run/sequence acceptance gate serve REST and WebSocket. Duplicate/old frames are ignored, sequence gaps resync, resets switch generation/run before fetching, reconnect falls back to REST. `?mock=1` uses only the frozen generated example, shows an explicit label and disables mutation.

Players apply trim/timeline offsets and replay speed, pause before their start, bound seeks/display times to their decoded duration and start muted. Source cards label generated media, show actual observed modalities, exclude abstentions/non-game claims from supported counts, and select the latest attributable claim's aspect feature (including mixed-modality aggregates). Aggregate scope and aspect remain visible. Missing/warmup values are unavailable, never zero.

The terminal has source monitor, cache controls, searchable/filterable evidence with OCR tracks/confidence/raw frame/audio inspection, a synthetic scenario estimate/candidate panel, receipt modal, separate actual GTA VI venue table/rules/freshness, paper candidate tape and coverage/limitations. It does not transform proxy evidence into a live GTA VI estimate.

## Verification actually executed

- `npm.cmd install --cache ../.cache/npm --no-audit --no-fund` from `frontend`: exit 0, 69 packages installed without escalation. Locked versions include React/ReactDOM 19.3.1, TypeScript 5.9.3, Vite 6.4.6 and React plugin 4.7.0.
- Final `npm.cmd run build` from `frontend`: exit 0; TypeScript `--noEmit` and Vite build succeeded. Output approximately 271 KB JS / 27 KB CSS before gzip.
- First bundling attempt exposed an invalid empty data-URL CSS import; removed and rebuilt successfully. A targeted feature-selection check exposed mixed-modality aggregates being filtered out; accepted the generated `mixed` value and reran successfully.
- Mock browser inspection used installed Microsoft Edge through Playwright with request-intercepted build assets, no preview process: explicit mock label, receipt quote/open/Escape close, search empty state, desktop 1440 and narrow 390 no horizontal document overflow, no page errors.
- Actual browser QA used root-owned `http://127.0.0.1:8000` with an isolated newly created run: both generated videos decoded; generation/proxy labels visible; 2× play/pause advanced replay to 3.718 seconds with video times 3.892/4.634 (within 0.5 seconds of replay and replay+1); keyboard seek reached 12 seconds; two speech observations present; receipt opened/closed; sampled image loaded; extracted audio decoded; reset changed run; injected old-run sequence 999999 was rejected; forced socket close showed REST fallback then reconnected; desktop/narrow passed overflow checks; zero console errors or HTTP failures.
- Final focused browser recheck after source-display fixes passed supported counts, aspect/negative feature labels, bounded media times, observed modalities and both layouts, again with zero console/HTTP errors.
- Local artifacts: `frontend/.qa/g2-browser.json`, `g2-final-ui.json`, `g2-desktop.png`, `g2-mobile.png`, plus mock screenshots. These are verification artifacts, not a formal tester-owned suite.

## Limitations and remaining integration

- The current full-state contract exposes candidate decisions and order/fill counts, not a detailed order/fill/position ledger. The tape accurately displays candidates; no realized/unrealized P&L is fabricated. Detailed broker lifecycle UI needs root's future projection contract.
- No scenario injection/selection API was provided. Controls operate the loaded fixture/recording run; loading six scenarios remains a root CLI/runtime integration concern.
- Cached observations are rendered from full snapshots without virtualization. Very long recordings with very large ledgers may need pagination/virtualization later.
- Browser video codec support still matters; decoding preprocessing success does not guarantee a browser supports every original container/codec. Player errors are visible. Verified generated H.264/AAC media plays in installed Edge.
- Muting is per source; enabling several tracks can overlap sound. No automatic speaker isolation/voice attribution is claimed by the UI.
- Root owns dependency setup integration, media/cache preparation and server shutdown. The client build is ready; no frontend blockers remain.

## G2 follow-up: unassigned scenes and abstention

15 November 2026, after root received three local clips. Changed only `frontend/src/App.tsx`, rebuilt ignored `frontend/dist/`, and updated this handoff.

- Coverage excludes empty/unknown/unassigned/manual-unassigned/manual-unknown scene sentinels (case-insensitive, underscore/hyphen normalized). With none assigned it displays **Unknown / Unassigned scenes**, not one recognized scene. Known manual scene IDs are still counted uniquely.
- Observations without an estimate now show **No estimate · abstained** and an **Abstained** candidate state. No probability or sentiment is substituted; the receipt button remains disabled when no receipt exists.
- `npm.cmd run build`: exit 0, including TypeScript. Isolated Edge browser inspection passed sentinel variants, a known manual scene, empty features/estimates/decisions/receipts, disabled receipt, unavailable values, no error alert/page errors and 390px no-overflow. Report: `frontend/.qa/g2-unassigned-ui.json`.
- The initial exact-text browser assertion used a middle-dot literal corrupted by the Windows command encoding; the rendered text was correct. Rechecked with an ASCII Unicode escape and it passed. No application change was needed for that assertion.
- Root owns the actual three-recording browser pass and retained preview process. This follow-up did not start/stop a server, alter the loaded run, change contracts, or begin G3.

## G3 frontend integration and preservation audit

G3 was subsequently authorized. The following implementation was complete before the session interruption and remained intact when work resumed:

- `ScenarioChooser.tsx`: six generated-request-typed synthetic scenarios, new isolated run acknowledgement and return-to-recordings action. `useDesk.ts` uses generated `ScenarioRequest`/`CreateRunRequest`, serializes mutations and changes active run/generation before accepting new state.
- `PaperActivity.tsx`: backend cash/reservations/realized P&L, pending/filled/partial/cancelled orders, side/direction/quantity/limit, fills/VWAP/gross/executed fees, positions/cost basis, depth-aware marks, explicitly unpriced inventory, risk reasons and paper exit request. No frontend accounting calculation or live orders.
- `ExecutionTraceDialog.tsx`: original entry/exit plan and eligibility tabs, exact quote/timestamp/staleness, nullable estimate/decision/receipt, original supporting windows/claims/features, order/fill/intent/book identifiers and immutable trace endpoint link. The existing candidate receipt stays available separately.
- `UnavailableSources.tsx`: padded source statuses without invented recording assets or media requests. Existing real-recording abstention and unknown/unassigned-scene behavior is preserved.
- `App.tsx` integrates these components; synthetic accounting seeks are forward-only with reset guidance, while recording replay stays bidirectional. `SourceCard.tsx` and `EvidenceArtifacts.tsx` append the selected run ID to media/artifact requests. `styles.css` contains responsive G3 layouts. No dependencies were added.

After the user requested preservation, `git status` confirmed this folder is not a Git repository. All 19 owned frontend source/config/documentation files were read and inspected; no truncated or missing frontend module was found. A read-only rebuild passed with unchanged artifact hashes. Working components were preserved.

Two missing G3 requirements were reported and explicitly approved by root for minimal completion:

1. `frontend/src/transport/useDesk.ts` now rejects malformed optional execution containers/array fields instead of passing them into array consumers. Missing execution remains compatible with older snapshots. Inline checks accepted three valid optional/empty cases and rejected ten malformed cases.
2. `frontend/src/App.tsx` now shows current synthetic quote fresh/stale state, venue status and capture age using `snapshot.replay_time`. Isolated Edge inspection verified stale/fresh badges and 20-second/2-second replay-clock ages, no page errors and 390px no document overflow.

These two application files plus this handoff are the only source/metadata changes after the preservation audit. Final `npm.cmd run build` exited 0 (TypeScript plus Vite); output JS `index-C8t3C6h0.js`, approximately 294 KB before gzip. Root owns the integrated G3 browser pass, runtime processes and final persistence checks; this worker did not start, stop or mutate the shared runtime during the resumed audit. The earlier G2 notes about absent lifecycle/scenario UI are superseded by the G3 implementation above.

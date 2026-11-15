# Leonida Alpha terminal UI

15 November 2026. Frontend redesign against application baseline `1baadb2`. The checkout began at `2935a2e`, which adds only README changes after that baseline; those changes are retained. One thread, no agents. No backend, transport, contract, schema, model, accounting, scenario data, dependency or media-processing changes.

## Before audit

Playwright MCP inspected isolated recordings and portable applications on ports 8002 and 8003. Port 8002 was not listening at inspection, so both were launched with separate `var/ui-*.sqlite3` databases. The existing server on 8000 was left alone. The installed, cached Playwright MCP server was used over localhost HTTP through an ignored local bridge; nothing was added to project dependencies.

Before screenshots at 1440×900 and 390×844 are in `var/ui-redesign/before-{recordings,portable}-{desktop,narrow}.png`.

| Dimension | Finding | Decision |
| --- | --- | --- |
| Hierarchy | Sources began roughly 630px down the desktop; mobile first viewport contained neither source nor market summary. | Remove hero; place compact replay/scenario controls above sources. Market summary precedes sources on narrow screens. |
| Density | Large metric cards, generous chrome and repeated per-source analysis obscured the research path. | Inline coverage strip; compact source tiles; analysis disclosure; shared reaction/claim timeline. |
| Alignment | Sources, market cards and long downstream panels lacked a persistent common frame. | One research workspace and a 305px sticky market/model rail spanning its full height. |
| Typography | Promotional headline competed with operational values. Many green-muted labels had weak distinction. | System UI font, compact headings, tabular values and semantic color roles. |
| Spacing | Rounded cards and large gutters consumed vertical space. | 1px rules, 2px radii, 8px source gutters and 12–14px panel spacing. |
| State clarity | A missing model read like a missing market; contextual reactions repeated within each card. | Quote-derived midpoint and explicit model/candidate abstention stay separate. Context, claim support and inclusion remain separate labels. |
| Evidence → execution | Receipts were centered generic dialogs and paper activity sat after venue context. | Right-edge receipt/trace inspector; evidence tape followed by paper blotter; separate historical venue context. |

## Design system

| Token | Value | Role |
| --- | --- | --- |
| Canvas | `#0b0c0e` | Near-black neutral background |
| Panel | `#111316` | Source, evidence and research panels |
| Raised surface | `#16181c` | Command controls and table headers |
| Separator | `#2a2d33` | Thin panel, column and row rules |
| Primary text | `#e0e2e6` | Operational content |
| Secondary text | `#a0a6af` | Supporting labels and provenance |
| Amber | `#edbb65` | Quote prices and market midpoint |
| Green | `#80d5a1` | Active connections, positive values, included claims |
| Cyan | `#7ed1e2` | Evidence, source identifiers, inspection links, focus |
| Red | `#f18f92` | Stale quotes, excluded evidence, cancellation and risk |

Use color with explicit text. Badges are unboxed labels, with small dots only where useful. Surfaces are neutral; no gradients, blur, glass, decorative card shadows or external fonts. The only shadow separates the inspector from the workspace. Primary/secondary text and semantic colors exceed 4.5:1 against their normal neutral surfaces; disabled controls retain an intentionally subdued appearance.

Segoe UI / Arial provide labels and prose. Cascadia Mono / SFMono-Regular / Consolas provide tabular numbers and audit IDs using installed fonts. Normal content is 11–12px, section headings 12–13px, supporting metadata 8–10px and key numerical values 16–23px. Small metadata is secondary to readable source text and the market state.

Keyboard focus uses a 2px cyan outline with a 3px offset. Native selects, details and dialog focus containment are retained. A skip link, explicit scenario/source labels and focusable named table scroll regions support keyboard navigation. Receipt inspectors retain accessible titles, close buttons, Escape dismissal and focus restoration.

## Layout and state

1. Command chrome identifies the full run, connection and paper mode. The adjacent replay strip contains scenario, replay position, status, speed and reset. Scenario loading and return-to-recordings remain visible in a compact row.
2. Three source columns at wide desktop sizes, two below 1200px. Videos preserve their 16:9 frame. Synthetic fixtures use a compact no-media strip instead of a large empty player. Source analysis retains sentiment, pre-update surprise, baseline reasons, media timing and modality availability behind disclosure.
3. The market/model rail stays alongside sources, timelines, evidence, execution and venue context. It independently presents synthetic bid/ask, freshness, midpoint, heuristic estimate, correction, candidate EV/reasons, receipt, account and resolution/source details. Existing quote validation and formatting calculations are reused.
4. The shared source-aligned reaction timeline sits immediately beneath the source grid. It reuses the existing reaction component and its unchanged time bins, recent-window selection and eligibility flags. Supported quality claims have a distinct timestamped lane; telemetry alone does not establish quality.
5. The evidence tape preserves every row, search, source filter, source extraction details, media artifacts and receipt action. Its bounded scroll area keeps the paper blotter reachable on long recordings. The blotter retains order/fill lifecycle, positions, marks, fees, exits, reasons and execution-stage inspection.
6. Venue context retains exact returned tickers, resolution rules, captured timestamps and source paths. Historical/stale captures are explicit and visually separate from synthetic scenario prices. Optional live context still uses its existing returned mode labels; no live network fetch was enabled or claimed verified.
7. Native dialogs are styled as full-height, right-aligned inspectors, 620px wide on desktop and viewport-wide on mobile. Their focus and Escape behavior is preserved.

Below 700px, order becomes run/replay/scenario controls → market/model summary → source selector and active source → timelines/evidence/execution/venue. Only the selected source tile is shown; all existing video synchronization logic remains intact. Execution and venue tables preserve their columns within keyboard-scrollable regions, instead of compressing the desktop grid into miniature cards. The document itself does not overflow horizontally.

Explicit provenance appears where data is consumed: local recording; machine OCR/ASR; contextual reaction telemetry; supported quality claim; synthetic fixture/no video; synthetic quote; historical/stale Kalshi context; optional live venue context; simulated paper fill. The valid abstention state reads:

> Market midpoint 14.50% · Model abstained · No supported quality claim · No paper candidate

The established semantic values and test IDs for midpoint, model, correction and candidate remain intact. No neutral values are substituted for missing outputs.

## Verification and artifacts

Playwright MCP used the built frontend against the two isolated applications. Browser records and screenshots are local ignored artifacts under `var/ui-redesign/`.

| Screenshot | State |
| --- | --- |
| `recordings-desktop.png` | 1440×900, all five decoded local videos, valid 14.50% midpoint, abstention |
| `courtroom-supported-claim.png` | 1440×900, three supported fixture claims at replay 7s |
| `courtroom-claim-timeline.png` | Supported claims, reaction context and model rail |
| `paper-execution.png` | Simulated partial fill, fees, position and executable mark |
| `receipt-inspector.png` / `paper-trace.png` | Decision drawer and eligibility-stage trace |
| `venue-context.png` / `venue-rules.png` | Eight historical Kalshi captures and resolution disclosure |
| `venue-outage.png` | Stale synthetic quote, model abstention, cancelled order / zero fills |
| `narrow-390.png` / `narrow-390-full.png` | 390×844 viewport and full-page narrow layout |
| `narrow-source-analysis.png` / `narrow-venue-table.png` | Active-source analysis and keyboard-scrolled table |

Browser observations: five 1920px-wide decoded videos; play/pause and synchronized positions; speed and seek/reset covered by the retained G4 browser suite; all five narrow source selections; source filtering/search/no-results; three included Courtroom claims; 6/10 partial entry; receipt and trace inspection; eight stale venue rows/rules; outage cancellation with unchanged $10,000 cash and no fill. Drawer focus containment and Escape close were checked. Page widths 390, 700, 768, 1024 and 1440 had equal viewport/document widths. Final browser capture recorded no console errors, page exceptions or external resource requests. Table scrolling was confined to its labelled region.

Commands run successfully:

```powershell
python scripts/manage.py check --gate G3
.venv/Scripts/python.exe -B -m unittest discover -s tests/g4 -v
python scripts/manage.py demo-check --scenario all
npm.cmd --prefix frontend run build
git diff --check
```

G3: 15 tests plus schema/type drift, scenario, typecheck and build checks. G4/release: 11 tests, including retained quote/abstention semantic assertions. Release smoke: all six scenarios. Logs: `g3-check.log`, `g4-final.log`, `release-check.log`; browser records: `final-browser-results.jsonl`, `venue-outage-results.jsonl`, `network-requests.txt`. Existing Windows media-socket teardown/reset/resource warnings and Uvicorn graceful-shutdown warning remain in G4 server output; browser errors remained zero. No application workaround or backend change was made.

Limits: verified on installed Edge, not cross-browser/device certification. Dense metadata is deliberately small. Source previews show two lines; the evidence tape retains full text and artifacts. Long venue/execution tables require local horizontal scrolling on narrow screens. Local recordings and screenshots are ignored assets, unavailable in a source-only checkout. Fixture no-video states, OCR/ASR uncertainty, text-only reaction heuristics and uncalibrated estimates remain explicit. Live venue behavior was preserved but not exercised against the network.

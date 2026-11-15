# Leonida Alpha terminal

React/TypeScript client for the local evidence desk. The root backend serves `frontend/dist` at `/` after a build; `/foundation` retains the G1 viewer.

From the repository root:

```powershell
npm.cmd --prefix frontend ci --cache .cache/npm --no-audit --no-fund
npm.cmd --prefix frontend run build
python scripts/manage.py demo
```

Use the recording launch command documented in the root README and `data/recordings/README.md` to load local media instead of the foundation fixture. Put recordings in `data/recordings/inbox/` and configure the manifest; the browser does not upload or preprocess video.

For frontend development with a separately running backend on port 8000:

```powershell
npm.cmd --prefix frontend run dev
```

Vite proxies `/api`, `/ws`, `/health` and `/ready` to the local backend. `npm.cmd --prefix frontend run typecheck` checks the generated-contract consumer. `?mock=1` displays the explicitly labelled, read-only frozen contract example without connecting to the backend.

## Behavior

- One decoder and run/sequence gate for full HTTP/WebSocket snapshots. Stale run frames and duplicate/older sequences are ignored; gaps request a REST resync. Reconnect uses REST fallback while retrying the socket.
- Generated backend `RunCommand` types drive play/pause, speed, seek, replay and reset controls. Reset switches the active run before accepting new frames.
- Video alignment is `media_seconds = replay_seconds - timeline_start_seconds + media_start_seconds`. Players are muted initially, pause before their start, respect replay speed and stop at their own duration. Each source has a separate audio toggle.
- Source and evidence views distinguish generated test media, recorded GTA V proxy evidence, OCR/transcription providers, unsupported claims, missing modalities and warmup. Sample images/audio use the backend's allowlisted artifact route.
- Actual GTA VI venue quotes remain in their own panel, with original tickers, rules, capture age and freshness. The model panel uses synthetic scenario quotes. Paper candidates, quantities and fees are distinct from orders and fills.
- Receipts show original words, feature inputs, model arithmetic, quote/decision IDs and limitations. Frontend formatting uses numbers only for display; it never calculates accounting or places orders.

Root owns `src/generated/`; do not edit generated files. Backend API and recorded-media setup remain root/pipeline responsibilities. No external hosting or runtime process management is part of this client.

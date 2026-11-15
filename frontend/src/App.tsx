import { useEffect, useState } from 'react';
import type { DashboardSnapshot, MarketQuote } from './generated/contracts';
import { useDesk } from './transport/useDesk';
import { Badge, Icon, age, cents, dollars, duration, percent, signed } from './components/Primitives';
import { SourceCard } from './components/SourceCard';
import { ReceiptDialog } from './components/ReceiptDialog';
import { EvidenceArtifacts } from './components/EvidenceArtifacts';
import { ScenarioChooser } from './components/ScenarioChooser';
import { PaperActivity } from './components/PaperActivity';
import { ExecutionTraceDialog } from './components/ExecutionTraceDialog';
import { UnavailableSources } from './components/UnavailableSources';
import { quoteReference } from './components/quoteReference';

const unassignedSceneIds = new Set(['unknown', 'unassigned', 'manual-unassigned', 'manual-unknown']);
const isAssignedScene = (sceneId: string) => {
  const normalized = sceneId.trim().toLowerCase().replaceAll('_', '-');
  return normalized.length > 0 && !unassignedSceneIds.has(normalized);
};

function QuotePrice({ quote, side }: { quote?: MarketQuote; side: 'yes' | 'no' }) {
  const bid = quote?.[`${side}_bid`];
  const ask = quote?.[`${side}_ask`];
  return <div className={`quote-price ${side}`}><span>{side.toUpperCase()}</span><div><b title={quote?.missing_reasons?.[`${side}_bid`]}>{cents(bid)}</b><i>/</i><b title={quote?.missing_reasons?.[`${side}_ask`]}>{cents(ask)}</b></div><small>Bid / Ask · per contract</small></div>;
}

function ScenarioPanel({ snapshot, onReceipt }: { snapshot: DashboardSnapshot; onReceipt: (id: string) => void }) {
  const estimate = snapshot.estimates.at(-1);
  const decision = snapshot.decisions.at(-1);
  const market = snapshot.markets.find(item => item.market_id === estimate?.market_id) ?? snapshot.markets[0];
  const quote = snapshot.quotes.find(item => item.quote_id === estimate?.quote_id) ?? snapshot.quotes.at(-1);
  const receipt = snapshot.receipts.find(item => item.decision_id === decision?.decision_id);
  const candidateEv = decision?.side === 'yes' ? decision.yes_ev_per_contract : decision?.no_ev_per_contract;
  const hasObservations = snapshot.windows.length > 0;
  const hasSupportedClaims = snapshot.claims.some(claim => claim.sentiment != null && claim.target === 'game');
  const reference = quoteReference(quote, snapshot.replay_time);
  return <aside className="panel scenario-panel" id="scenario">
    <div className="panel-heading"><span className="eyebrow">SCENARIO MARKET</span><Badge tone="amber">Synthetic quotes</Badge></div>
    <h2>{market?.title ?? 'Waiting for a scenario'}</h2>
    <p className="muted small">This estimate uses GTA V proxy evidence. Actual GTA VI quotes are shown separately.</p>
    <div className="quote-pair"><QuotePrice quote={quote} side="yes" /><QuotePrice quote={quote} side="no" /></div>
    <div className="badge-row" aria-label="Synthetic quote freshness" style={{ marginBottom: 16 }}><Badge tone={!quote ? 'muted' : quote.is_stale ? 'amber' : 'green'} dot>{!quote ? 'Quote unavailable' : quote.is_stale ? 'Stale synthetic quote' : 'Fresh synthetic quote'}</Badge><span className="tiny muted" title={quote?.captured_at}>{quote ? `${quote.venue_status} · captured ${age(quote.captured_at, Date.parse(snapshot.replay_time))} (replay time)` : 'No scenario quote received'}</span></div>
    <div className="estimate-grid"><div><span>Market reference</span><strong data-testid="quote-midpoint">{percent(reference.midpoint, 2)}</strong><small>Synthetic Yes midpoint / quote-derived</small></div><div><span>Model estimate</span><strong className="green-text" data-testid="model-estimate">{estimate ? percent(estimate.model_probability) : hasSupportedClaims ? 'Evidence-adjusted estimate unavailable' : 'No supported quality claims'}</strong><small>Heuristic probability</small></div></div>
    {estimate ? <div className="probability-track" aria-label={`Market reference ${percent(estimate.market_reference_probability)}, model estimate ${percent(estimate.model_probability)}`}><div className="track-line" /><span className="marker market-marker" style={{ left: `${estimate.market_reference_probability * 100}%` }} /><span className="marker model-marker" style={{ left: `${estimate.model_probability * 100}%` }} /><div className="track-labels"><span>0%</span><span>100%</span></div></div> : <div className="empty-state compact">{reference.reason ?? (!hasSupportedClaims ? 'Market quote available; no evidence-adjusted estimate because no supported quality claims exist.' : 'Market quote available; evidence-adjusted estimate unavailable for the current routed inputs.')}</div>}
    <div className="correction-row"><span>Log-odds correction</span><b className="mono" data-testid="log-odds-correction">{signed(estimate?.correction_log_odds, 3)}</b></div>
    <div className="candidate-box"><div className="candidate-title"><span className="eyebrow">PAPER CANDIDATE</span><Badge tone="blue">{decision ? `${decision.side.toUpperCase()} side` : hasObservations ? 'Abstained' : 'Waiting'}</Badge></div><div className="candidate-value"><strong data-testid="paper-candidate">{candidateEv == null ? (!estimate ? 'Evidence-adjusted estimate unavailable' : 'No executable EV') : `${Number(candidateEv) > 0 ? '+' : ''}${(Number(candidateEv) * 100).toFixed(3)}¢`}</strong><span>net EV / contract</span></div><p>{decision?.reasons[0] ?? 'Evidence-adjusted estimate unavailable; no paper candidate can be formed.'}</p>{decision && <details><summary>Why this is a candidate</summary><ul>{decision.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul></details>}</div>
    <button className="button receipt-button" type="button" disabled={!receipt} onClick={() => receipt && onReceipt(receipt.receipt_id)}><Icon name="document" />Inspect full receipt<Icon name="arrow" /></button>
    {market && <details className="market-rules"><summary>Scenario resolution & model context</summary><p>{market.rules_primary}</p><p className="mono tiny">{estimate?.model_version ?? 'Model unavailable'}</p></details>}
  </aside>;
}

export default function App() {
  const desk = useDesk();
  const [now, setNow] = useState(Date.now());
  const [receiptId, setReceiptId] = useState<string | null>(null);
  const [executionOrderId, setExecutionOrderId] = useState<string | null>(null);
  const [streamFilter, setStreamFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [seekDraft, setSeekDraft] = useState<number | null>(null);
  const snapshot = desk.frame?.payload;
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  useEffect(() => { setReceiptId(null); setExecutionOrderId(null); setSeekDraft(null); setStreamFilter('all'); setSearch(''); }, [snapshot?.run_id]);
  const playback = snapshot?.playback;
  const position = playback?.position_seconds ?? 0;
  const playbackDuration = playback?.duration_seconds ?? 0;
  const disabled = desk.busy || desk.mockMode || !snapshot;
  const selectedReceipt = snapshot?.receipts.find(item => item.receipt_id === receiptId) ?? null;
  const selectedOrder = snapshot?.execution?.orders?.find(item => item.order_id === executionOrderId) ?? null;
  const forwardOnly = Boolean(snapshot?.execution?.enabled);
  const unassignedSources = snapshot?.streams.filter(source => !snapshot.recording_manifest.recordings.some(asset => asset.stream_id === source.stream_id)) ?? [];
  const sourcesReady = snapshot?.streams.filter(item => item.state === 'recording_ready').length ?? 0;
  const uniqueSources = new Set(snapshot?.windows.map(item => item.stream_id)).size;
  const displayedWindows = snapshot?.windows.filter(item => (streamFilter === 'all' || item.stream_id === streamFilter) && (!search || item.raw_text.toLowerCase().includes(search.toLowerCase()))).slice().reverse() ?? [];
  const quoteModes = [...new Set(snapshot?.venue_context.quotes.map(item => item.quote_mode))];
  const latestFeature = snapshot?.features.at(-1);
  const manualSceneCount = new Set(snapshot?.claims.map(item => item.scene_id).filter(isAssignedScene) ?? []).size;
  const seek = () => { if (seekDraft != null) void desk.control('seek', { position_seconds: forwardOnly ? Math.max(position, seekDraft) : seekDraft }); setSeekDraft(null); };

  return <div className="app">
    <header className="topbar"><a className="brand" href="#"><span className="brand-mark">L<span>α</span></span><div><strong>LEONIDA <span>ALPHA</span></strong><small>EVIDENCE & MARKET RESEARCH</small></div></a><div className="header-right"><span className={`connection ${desk.connection}`}><i />{({ connecting: 'Connecting', streaming: 'Stream connected', polling: 'REST fallback', offline: 'Offline', mock: 'Frozen example' })[desk.connection]}</span><span className="local-label mono">LOCAL / {snapshot?.gate ?? 'G2'}</span></div></header>
    <nav className="desk-nav" aria-label="Desk sections"><div><a className="active" href="#streams">Evidence desk</a><a href="#markets">Venue context</a><a href="#paper">Paper activity</a></div><span className="mono tiny">{snapshot?.run_id ? `RUN ${snapshot.run_id.slice(-12)}` : 'AWAITING SNAPSHOT'}</span></nav>
    <main>
      <div className="page-heading"><div><div className="eyebrow"><span className="green-text">RESEARCH WORKSPACE</span><span className="slash">/</span> GTA V → GTA VI PROXY DEMO</div><h1>Every signal. An inspectable source.</h1><p>Recorded streams, extracted evidence and transparent paper decisions.</p></div><div className="badge-row mode-badges"><Badge tone="amber">GTA V proxy evidence</Badge><Badge tone="green">{snapshot?.evidence_mode === 'recorded' ? 'Recorded evidence' : 'Synthetic replay'}</Badge><Badge tone="blue">Paper execution</Badge><Badge>Heuristic model</Badge></div></div>
      {desk.mockMode && <div className="notice amber" role="status">Frozen contract example · read-only preview. No backend or media activity is being shown.</div>}
      {desk.error && <div className="notice error" role="alert"><span>{desk.error}</span><button type="button" onClick={() => void desk.refresh()}>Retry connection</button></div>}
      {desk.notice && <div className="notice success" role="status">{desk.notice}</div>}
      {!snapshot ? <div className="waiting-panel"><Icon name="signal" size={34} /><h2>{desk.connection === 'offline' ? 'The local desk is offline' : 'Connecting to your evidence desk'}</h2><p>Start the backend with <code>python scripts/manage.py demo</code>, then this view will load its full state.</p><a href="?mock=1">Inspect the frozen contract example <Icon name="arrow" size={14} /></a></div> : <>
        <ScenarioChooser activeScenario={snapshot.scenario_name} disabled={disabled} onLoad={scenario => void desk.loadScenario(scenario)} />
        <section className="metric-strip" aria-label="Evidence coverage"><div><span>Recording sources</span><strong>{sourcesReady}<small> / {snapshot.recording_manifest.recordings.length}</small></strong><em>{sourcesReady ? 'Ready for synchronized playback' : 'Fixture fallback available'}</em></div><div><span>Unique observations</span><strong>{snapshot.windows.length.toString().padStart(2, '0')}</strong><em>{uniqueSources} contributing source{uniqueSources === 1 ? '' : 's'}</em></div><div><span>Supported claims</span><strong>{snapshot.claims.filter(item => item.sentiment != null).length.toString().padStart(2, '0')}</strong><em>{snapshot.claims.filter(item => item.sentiment == null).length} abstained · missing stays missing</em></div><div><span>Paper cash</span><strong>{dollars(snapshot.cash_usd)}</strong><em>{snapshot.order_count ?? 0} orders · {snapshot.fill_count ?? 0} fills</em></div></section>
        <section className="playback-bar" aria-label="Synchronized replay controls"><div className="playback-main"><button type="button" className="play-button" disabled={disabled || playbackDuration <= 0} onClick={() => void desk.control(playback?.playing ? 'pause' : 'play')} aria-label={playback?.playing ? 'Pause replay' : 'Play replay'}><Icon name={playback?.playing ? 'pause' : 'play'} size={17} /></button><div><strong>Cached evidence replay</strong><span>{snapshot.run_status?.toUpperCase()} · {playbackDuration > 0 ? 'Synchronized event time' : 'Single fixture observation'}</span></div></div><div className="timeline"><span className="mono">{duration(seekDraft ?? position)}</span><input type="range" aria-label="Replay position" min={forwardOnly ? position : 0} max={Math.max(playbackDuration, 1)} step="0.1" value={forwardOnly ? Math.max(position, seekDraft ?? position) : seekDraft ?? position} disabled={disabled || playbackDuration <= 0} onChange={event => setSeekDraft(Number(event.target.value))} onPointerUp={seek} onKeyUp={event => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) seek(); }} /><span className="mono muted">{duration(playbackDuration)}</span></div><div className="playback-actions"><label className="sr-only" htmlFor="replay-speed">Replay speed</label><select id="replay-speed" aria-label="Replay speed" value={playback?.speed ?? 1} onChange={event => void desk.control('set_speed', { speed: Number(event.target.value) })} disabled={disabled || playbackDuration <= 0}>{[0.5, 1, 2, 5].map(speed => <option value={speed} key={speed}>{speed}× speed</option>)}</select><button type="button" className="icon-button" disabled={disabled} onClick={() => void desk.control('reset')} aria-label="Reset to a new run" title="Reset to a new run"><Icon name="reset" /></button></div></section>
        {forwardOnly && <p className="seek-guidance">Synthetic accounting advances forward only. Use Reset to inspect an earlier point in a fresh run.</p>}
        <div className="main-grid"><section id="streams" className="stream-section"><div className="section-heading"><div><span className="section-index">01</span><h2>Source monitor</h2><Badge>{snapshot.streams.length} source slots</Badge></div><span className="tiny muted">LOCAL MEDIA · CHAT OCR · AUDIO</span></div><div className="stream-grid">{snapshot.recording_manifest.recordings.map((asset, index) => {
          const windows = snapshot.windows.filter(item => item.stream_id === asset.stream_id);
          const claims = snapshot.claims.filter(item => item.stream_id === asset.stream_id);
          const latestClaim = claims.filter(item => item.sentiment != null && (item.target ?? 'game') === 'game').at(-1);
          const feature = snapshot.features.filter(item => (!latestClaim || (item.aspect === latestClaim.aspect && (item.source_modality === latestClaim.source_modality || item.source_modality === 'mixed'))) && item.claim_ids.some(id => claims.some(claim => claim.claim_id === id))).at(-1);
          return <SourceCard key={asset.asset_id} asset={asset} index={index} status={snapshot.streams.find(item => item.stream_id === asset.stream_id)} window={windows.at(-1)} windows={windows} claims={claims} feature={feature} playback={playback} runId={snapshot.run_id} reactions={(snapshot.reactions ?? []).filter(r => r.stream_id === asset.stream_id)} reactionRecentSeconds={snapshot.reaction_recent_window_seconds ?? 30} />;
        })}</div><UnavailableSources sources={unassignedSources} /><details className="input-guide"><summary><Icon name="folder" />Add your own recordings<span>Local files + manifest</span></summary><p>Put 2–6 GTA V screen recordings with visible chat in <code>data/recordings/inbox/</code>. Configure each file, streamer ID, trim start, timeline offset and chat crop in the recording manifest.</p><p>See <code>data/recordings/README.md</code> for preprocessing and launch commands. Extracted evidence is cached; playback does not rerun OCR or speech models.</p><p className="tiny muted">Current manifest: {snapshot.recording_manifest.manifest_version} · OCR: {snapshot.recording_manifest.ocr_version}</p></details></section><ScenarioPanel snapshot={snapshot} onReceipt={setReceiptId} /></div>
        <section className="panel evidence-panel" id="evidence"><div className="section-heading"><div><span className="section-index">02</span><h2>Evidence ledger</h2><Badge>{snapshot.windows.length} observations</Badge></div><div className="ledger-filters"><input type="search" placeholder="Find evidence…" aria-label="Search evidence" value={search} onChange={event => setSearch(event.target.value)} /><select aria-label="Filter by source" value={streamFilter} onChange={event => setStreamFilter(event.target.value)}><option value="all">All sources</option>{snapshot.streams.map(item => <option value={item.stream_id} key={item.stream_id}>{item.label}</option>)}</select></div></div>
          {displayedWindows.length ? <div className="evidence-list">{displayedWindows.map(window => {
            const claims = snapshot.claims.filter(item => item.window_id === window.window_id);
            const receipt = snapshot.receipts.find(item => item.window_ids.includes(window.window_id));
            return <article className="evidence-row" key={window.window_id}><div className="evidence-time mono">{duration(window.replay_seconds)}<span>REPLAY</span></div><div className="evidence-detail"><div className="evidence-title"><b>{snapshot.streams.find(item => item.stream_id === window.stream_id)?.label ?? window.stream_id}</b><Badge>{window.source_modality ?? 'chat'}</Badge><span className="tiny muted">{window.provider.replaceAll('_', ' ')}</span></div><p>“{window.raw_text || 'No transcribed words available'}”</p><div className="claim-tags">{claims.map(claim => <span key={claim.claim_id} title={claim.abstention_reason ?? undefined}>{claim.aspect?.replaceAll('_', ' ') ?? 'unattributed'} · {claim.sentiment == null ? 'abstained' : signed(claim.sentiment)} · {claim.target ?? 'unknown target'}</span>)}{!claims.length && <span>{window.observation?.abstention_reason ?? 'No attributable claim'}</span>}</div><details className="evidence-provenance"><summary>Source & extraction details</summary><div>Media {window.source_media_seconds.toFixed(2)}s · available +{Math.max(0, (Date.parse(window.available_at) - Date.parse(window.event_at)) / 1000).toFixed(2)}s · {window.evidence_mode.replaceAll('_', ' ')}</div><div>OCR confidence: {window.ocr_confidence == null ? window.confidence_reason ?? 'Unavailable for this source' : percent(window.ocr_confidence)}</div>{window.observation?.track_id && <div>OCR track: <code>{window.observation.track_id}</code></div>}<div>Source ID: <code>{window.observation_id}</code></div>{window.modalities.filter(item => !item.available).map(item => <div key={item.modality}>{item.modality}: {item.reason ?? 'Unavailable'}</div>)}<EvidenceArtifacts window={window} /></details></div><button type="button" className="text-button" disabled={!receipt} onClick={() => receipt && setReceiptId(receipt.receipt_id)}>Receipt<Icon name="arrow" size={15} /></button></article>;
          })}</div> : <div className="empty-state">{search ? 'No evidence matches this search.' : 'No extracted observations are available at this replay time.'}</div>}
          <div className="panel-footnote"><span><i className="live-dot" />Unique evidence only · refreshes do not add observations</span><button type="button" className="text-button" disabled={disabled} onClick={() => void desk.control('replay_observation')}>Replay same evidence<Icon name="reset" size={13} /></button></div>
        </section>
        <section className="panel venue-panel" id="markets"><div className="section-heading"><div><span className="section-index">03</span><h2>Actual GTA VI venue context</h2><Badge tone={quoteModes.includes('live') ? 'green' : 'amber'}>{quoteModes.includes('live') ? 'Live venue quotes' : 'Historical / stale'}</Badge></div><span className="tiny muted">SEPARATE FROM PROXY MODEL</span></div><p className="panel-intro">Returned venue tickers, rules and prices. GTA V demo evidence does not change these quotes or generate GTA VI estimates.</p>{snapshot.venue_context.error && <div className="inline-warning">{snapshot.venue_context.error}</div>}{snapshot.venue_context.quotes.length ? <div className="table-scroll"><table><thead><tr><th>Market / resolution</th><th>Yes bid / ask</th><th>No bid / ask</th><th>Quote state</th><th>Captured</th></tr></thead><tbody>{snapshot.venue_context.quotes.map(quote => {
          const market = snapshot.venue_context.markets.find(item => item.market_id === quote.market_id);
          return <tr key={quote.quote_id}><td><b>{market?.title ?? quote.market_id}</b><small className="mono">{market?.venue_ticker ?? 'Ticker unavailable'}</small>{market && <details><summary>Resolution rules</summary><p>{market.rules_primary}</p></details>}</td><td className="mono">{cents(quote.yes_bid)} <span className="muted">/</span> {cents(quote.yes_ask)}</td><td className="mono">{cents(quote.no_bid)} <span className="muted">/</span> {cents(quote.no_ask)}</td><td><Badge tone={quote.is_stale ? 'amber' : 'green'} dot>{quote.is_stale ? 'Stale' : quote.quote_mode === 'live' ? 'Live' : 'Synthetic'}</Badge><small>{quote.venue_status}</small></td><td title={quote.captured_at}><time dateTime={quote.captured_at}>{quote.captured_at}</time><small>{age(quote.captured_at, now)} / receipt time</small><small>{quote.source_ref.startsWith('data/snapshots/') ? 'Bundled historical capture' : 'Runtime public API receipt'} / {quote.source_ref}</small></td></tr>;
        })}</tbody></table></div> : <div className="empty-state">No venue quotes available. Recorded evidence replay remains independent.</div>}</section>
        <PaperActivity snapshot={snapshot} disabled={disabled} onExit={() => void desk.control('exit')} onTrace={setExecutionOrderId} />
        <div className="bottom-grid g3-coverage"><section className="panel coverage-panel"><div className="section-heading"><div><Icon name="signal" /><h2>Coverage & limitations</h2></div></div><div className="coverage-metrics"><div><strong>{uniqueSources}</strong><span>Observed sources</span></div><div><strong>{manualSceneCount > 0 ? manualSceneCount : 'Unknown'}</strong><span>{manualSceneCount > 0 ? 'Manual scenes' : 'Unassigned scenes'}</span></div><div><strong>{latestFeature?.disagreement == null ? 'N/A' : latestFeature.disagreement.toFixed(2)}</strong><span>Disagreement</span></div></div><ul>{snapshot.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></section></div>
        <footer className="desk-footer"><span><i className="live-dot" />LEONIDA ALPHA · LOCAL RESEARCH DESK</span><span className="mono">SCHEMA {desk.frame?.schema_version} · SEQ {desk.frame?.sequence} · UPDATED {desk.receivedAt ? `${Math.max(0, Math.floor((now - desk.receivedAt) / 1000))}s AGO` : 'UNAVAILABLE'}</span><details><summary>Cache provenance</summary><p className="mono">{snapshot.cache_key}</p><p>Configuration {snapshot.configuration_fingerprint}</p></details></footer>
        <ReceiptDialog receipt={selectedReceipt} snapshot={snapshot} onClose={() => setReceiptId(null)} />
        <ExecutionTraceDialog order={selectedOrder} execution={snapshot.execution} onClose={() => setExecutionOrderId(null)} />
      </>}
    </main>
  </div>;
}

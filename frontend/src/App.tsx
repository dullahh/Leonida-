import { useEffect, useState } from 'react';
import { useDesk } from './transport/useDesk';
import { Badge, Icon, age, cents, dollars, duration, percent, signed } from './components/Primitives';
import { SourceCard } from './components/SourceCard';
import { ReceiptDialog } from './components/ReceiptDialog';
import { EvidenceArtifacts } from './components/EvidenceArtifacts';
import { ScenarioChooser } from './components/ScenarioChooser';
import { PaperActivity } from './components/PaperActivity';
import { ExecutionTraceDialog } from './components/ExecutionTraceDialog';
import { UnavailableSources } from './components/UnavailableSources';
import { MarketRail } from './components/MarketRail';
import { ReactionTelemetry } from './components/ReactionTelemetry';
import { EvidenceTrail } from './components/EvidenceTrail';
import { TwitchLiveCapture, type LiveAudioChunk, type LiveAudioResult } from './components/TwitchLiveCapture';

const unassignedSceneIds = new Set(['unknown', 'unassigned', 'manual-unassigned', 'manual-unknown']);
const isAssignedScene = (sceneId: string) => {
  const normalized = sceneId.trim().toLowerCase().replaceAll('_', '-');
  return normalized.length > 0 && !unassignedSceneIds.has(normalized);
};

export default function App() {
  const desk = useDesk();
  const [now, setNow] = useState(Date.now());
  const [receiptId, setReceiptId] = useState<string | null>(null);
  const [executionOrderId, setExecutionOrderId] = useState<string | null>(null);
  const [streamFilter, setStreamFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [activeSource, setActiveSource] = useState('');
  const [activeSection, setActiveSection] = useState(window.location.hash || '#streams');
  const [activeView, setActiveView] = useState<'trail' | 'desk'>(() => ['#streams', '#markets', '#paper'].includes(window.location.hash) ? 'desk' : 'trail');
  const [seekDraft, setSeekDraft] = useState<number | null>(null);
  const snapshot = desk.frame?.payload;
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  useEffect(() => { setReceiptId(null); setExecutionOrderId(null); setSeekDraft(null); setStreamFilter('all'); setSearch(''); setActiveSource(''); }, [snapshot?.run_id]);
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
  const replayQuote = snapshot?.quotes.at(-1);
  const replayQuoteLabel = !replayQuote ? 'NO REPLAY QUOTE' : replayQuote.is_stale ? 'STALE REPLAY QUOTE' : `${replayQuote.quote_mode.replaceAll('_', ' ').toUpperCase()} QUOTE`;
  const latestFeature = snapshot?.features.at(-1);
  const manualSceneCount = new Set(snapshot?.claims.map(item => item.scene_id).filter(isAssignedScene) ?? []).size;
  const seek = () => { if (seekDraft != null) void desk.control('seek', { position_seconds: forwardOnly ? Math.max(position, seekDraft) : seekDraft }); setSeekDraft(null); };
  const submitLiveAudio = async (audio: Blob, metadata: LiveAudioChunk): Promise<LiveAudioResult> => {
    const response = await fetch('/api/live-audio/chunks', {
      method: 'POST',
      headers: {
        'Content-Type': audio.type.startsWith('audio/webm') ? 'audio/webm' : audio.type || metadata.mediaType,
        'X-Leonida-Source': metadata.channel,
        'X-Leonida-Chunk-Id': metadata.chunkId,
        'X-Leonida-Chunk-Index': String(metadata.chunkIndex),
        'X-Leonida-Started-At': metadata.startedAt,
      },
      body: audio,
      signal: AbortSignal.timeout(30_000),
    });
    const result = await response.json().catch(() => null);
    if (!response.ok) throw new Error(typeof result?.detail === 'string' ? result.detail : `Live audio processing failed (${response.status}).`);
    if (!result || typeof result !== 'object') throw new Error('The live audio endpoint returned an invalid result.');
    const segments = Array.isArray(result.accepted_segments) ? result.accepted_segments : [];
    const transcript = segments.map((segment: unknown) => segment && typeof segment === 'object' && typeof (segment as { text?: unknown }).text === 'string' ? (segment as { text: string }).text.trim() : '').filter(Boolean).join(' ');
    const auditSegments = Array.isArray(result.audit_segments) ? result.audit_segments : [];
    const notAccepted = auditSegments.filter((entry: unknown) => !entry || typeof entry !== 'object' || (entry as { status?: unknown }).status !== 'accepted');
    const reasonCounts = new Map<string, number>();
    for (const entry of notAccepted) {
      if (!entry || typeof entry !== 'object') continue;
      const reasons = (entry as { reasons?: unknown }).reasons;
      if (!Array.isArray(reasons)) continue;
      for (const reason of reasons) if (typeof reason === 'string') reasonCounts.set(reason, (reasonCounts.get(reason) ?? 0) + 1);
    }
    const reasonSummary = [...reasonCounts.entries()].slice(0, 3).map(([reason, count]) => `${reason.replaceAll('_', ' ')} (${count})`).join(', ');
    const auditSummary = segments.length
      ? `${segments.length} accepted speech segment${segments.length === 1 ? '' : 's'}${notAccepted.length ? ` · ${notAccepted.length} uncertain/rejected` : ''}`
      : `No speech passed quality gates · ${auditSegments.length} audited${reasonSummary ? ` · ${reasonSummary}` : ''}`;
    const modelIdentity = result.model_identity && typeof result.model_identity === 'object' ? result.model_identity as { name?: unknown; version?: unknown } : null;
    const provenance = [
      result.evidence_mode,
      typeof modelIdentity?.name === 'string' ? modelIdentity.name : null,
      typeof modelIdentity?.version === 'string' ? `model ${modelIdentity.version.slice(0, 12)}` : null,
      result.asr_version,
      result.gate_version,
    ].filter((item): item is string => typeof item === 'string').join(' · ');
    return {
      status: result.status === 'unavailable' ? 'ASR unavailable' : auditSummary,
      transcript: transcript || undefined,
      reason: typeof result.unavailable_reason === 'string' ? result.unavailable_reason : undefined,
      provenance: provenance || undefined,
    };
  };

  return <div className="app">
    <a className="skip-link" href="#streams" onClick={() => setActiveView('desk')}>Skip to source workspace</a>
    <header className="topbar"><a className="brand" href="#" aria-label="Leonida Alpha home"><span className="brand-mark">L<span>α</span></span><div><strong>LEONIDA <span>ALPHA</span></strong><small>EVIDENCE & MARKET RESEARCH</small></div></a><div className="command-run"><span className="eyebrow">RUN</span><span className="mono" title={snapshot?.run_id}>{snapshot?.run_id ?? 'Awaiting snapshot'}</span></div><div className="header-right"><span className={`connection ${desk.connection}`}><i />{({ connecting: 'Connecting', streaming: 'Stream connected', polling: 'REST fallback', offline: 'Offline', mock: 'Frozen example' })[desk.connection]}</span><span className="local-label">PAPER / {snapshot?.gate ?? 'G3'}</span></div></header>
    <nav className="desk-nav" aria-label="Desk sections"><div><a className={activeView === 'trail' ? 'active' : ''} aria-current={activeView === 'trail' ? 'page' : undefined} href="#trail" onClick={() => setActiveView('trail')}>Evidence trail</a><a className={activeView === 'desk' && activeSection === '#streams' ? 'active' : ''} aria-current={activeView === 'desk' && activeSection === '#streams' ? 'page' : undefined} href="#streams" onClick={() => { setActiveView('desk'); setActiveSection('#streams'); }}>Full desk</a><a className={activeView === 'desk' && activeSection === '#markets' ? 'active' : ''} aria-current={activeView === 'desk' && activeSection === '#markets' ? 'page' : undefined} href="#markets" onClick={() => { setActiveView('desk'); setActiveSection('#markets'); }}>Venue context</a><a className={activeView === 'desk' && activeSection === '#paper' ? 'active' : ''} aria-current={activeView === 'desk' && activeSection === '#paper' ? 'page' : undefined} href="#paper" onClick={() => { setActiveView('desk'); setActiveSection('#paper'); }}>Paper activity</a></div><span className="nav-provenance">{snapshot?.evidence_mode === 'recorded' ? 'LOCAL RECORDINGS' : 'SYNTHETIC FIXTURE'}<span> / </span> {replayQuoteLabel} <span> / </span> HEURISTIC MODEL</span></nav>
    <section id="live-demo-main"><TwitchLiveCapture onAudioChunk={submitLiveAudio} /></section>
    <main>
      <h1 className="sr-only">Leonida Alpha evidence and prediction-market research terminal</h1>
      {desk.mockMode && <div className="notice amber" role="status">Frozen contract example · read-only preview. No backend or media activity is being shown.</div>}
      {desk.error && <div className="notice error" role="alert"><span>{desk.error}</span><button type="button" onClick={() => void desk.refresh()}>Retry connection</button></div>}
      {desk.notice && <div className="notice success" role="status">{desk.notice}</div>}
      {!snapshot ? <div className="waiting-panel"><Icon name="signal" size={34} /><h2>{desk.connection === 'offline' ? 'The local desk is offline' : 'Connecting to your evidence desk'}</h2><p>Start the backend with <code>python scripts/manage.py demo</code>, then this view will load its full state.</p><a href="?mock=1">Inspect the frozen contract example <Icon name="arrow" size={14} /></a></div> : <>
        <section className="playback-bar" aria-label="Synchronized replay controls"><div className="playback-main"><button type="button" className="play-button" disabled={disabled || playbackDuration <= 0} onClick={() => void desk.control(playback?.playing ? 'pause' : 'play')} aria-label={playback?.playing ? 'Pause replay' : 'Play replay'}><Icon name={playback?.playing ? 'pause' : 'play'} size={17} /></button><div><strong>{snapshot.scenario_name === 'recordings' ? 'Local recordings' : snapshot.scenario_name?.replaceAll('-', ' ') ?? 'Evidence replay'}</strong><span>{snapshot.run_status?.toUpperCase()} · {playbackDuration > 0 ? 'Synchronized event time' : 'Single fixture observation'}</span></div></div><div className="timeline"><span className="mono">{duration(seekDraft ?? position)}</span><input type="range" aria-label="Replay position" min={forwardOnly ? position : 0} max={Math.max(playbackDuration, 1)} step="0.1" value={forwardOnly ? Math.max(position, seekDraft ?? position) : seekDraft ?? position} disabled={disabled || playbackDuration <= 0} onChange={event => setSeekDraft(Number(event.target.value))} onPointerUp={seek} onKeyUp={event => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) seek(); }} /><span className="mono muted">{duration(playbackDuration)}</span></div><div className="playback-actions"><label className="sr-only" htmlFor="replay-speed">Replay speed</label><select id="replay-speed" aria-label="Replay speed" value={playback?.speed ?? 1} onChange={event => void desk.control('set_speed', { speed: Number(event.target.value) })} disabled={disabled || playbackDuration <= 0}>{[0.5, 1, 2, 5].map(speed => <option value={speed} key={speed}>{speed}× speed</option>)}</select><button type="button" className="icon-button" disabled={disabled} onClick={() => void desk.control('reset')} aria-label="Reset to a new run" title="Reset to a new run"><Icon name="reset" /></button></div></section>
        <ScenarioChooser activeScenario={snapshot.scenario_name} disabled={disabled} onLoad={scenario => void desk.loadScenario(scenario)} />
        {activeView === 'trail' ? <EvidenceTrail snapshot={snapshot} onOpenDesk={() => { setActiveView('desk'); setActiveSection('#streams'); }} onLoadDemo={() => void desk.loadScenario('courtroom-praise')} onReceipt={setReceiptId} /> : <>
        <section className="metric-strip" aria-label="Evidence coverage"><div><span>Recording sources</span><strong>{sourcesReady}<small> / {snapshot.recording_manifest.recordings.length}</small></strong><em>{sourcesReady ? 'Ready for synchronized playback' : 'Fixture fallback available'}</em></div><div><span>Unique observations</span><strong>{snapshot.windows.length.toString().padStart(2, '0')}</strong><em>{uniqueSources} contributing source{uniqueSources === 1 ? '' : 's'}</em></div><div><span>Supported claims</span><strong>{snapshot.claims.filter(item => item.sentiment != null).length.toString().padStart(2, '0')}</strong><em>{snapshot.claims.filter(item => item.sentiment == null).length} abstained · missing stays missing</em></div><div><span>Paper cash</span><strong>{dollars(snapshot.cash_usd)}</strong><em>{snapshot.order_count ?? 0} orders · {snapshot.fill_count ?? 0} fills</em></div></section>
        {forwardOnly && <p className="seek-guidance">Synthetic accounting advances forward only. Use Reset to inspect an earlier point in a fresh run.</p>}
        <div className="terminal-grid"><div className="desk-workspace"><section id="streams" className="stream-section"><div className="section-heading"><div><span className="section-index">01</span><h2>Source monitor</h2><Badge>{snapshot.streams.length} source slots</Badge></div><span className="tiny muted">SYNCHRONIZED / {duration(position)}</span></div><div className="mobile-source-selector"><label htmlFor="active-source">Active source</label><select id="active-source" value={activeSource || snapshot.recording_manifest.recordings[0]?.asset_id || ''} onChange={event => setActiveSource(event.target.value)}>{snapshot.recording_manifest.recordings.map((asset, index) => <option key={asset.asset_id} value={asset.asset_id}>{String(index + 1).padStart(2, '0')} / {asset.label}</option>)}</select></div><div className="stream-grid">{snapshot.recording_manifest.recordings.map((asset, index) => {
          const windows = snapshot.windows.filter(item => item.stream_id === asset.stream_id);
          const claims = snapshot.claims.filter(item => item.stream_id === asset.stream_id);
          const latestClaim = claims.filter(item => item.sentiment != null && (item.target ?? 'game') === 'game').at(-1);
          const feature = snapshot.features.filter(item => (!latestClaim || (item.aspect === latestClaim.aspect && (item.source_modality === latestClaim.source_modality || item.source_modality === 'mixed'))) && item.claim_ids.some(id => claims.some(claim => claim.claim_id === id))).at(-1);
          return <div className={`source-slot ${asset.asset_id === (activeSource || snapshot.recording_manifest.recordings[0]?.asset_id) ? 'active-source' : ''}`} key={asset.asset_id}><SourceCard asset={asset} index={index} status={snapshot.streams.find(item => item.stream_id === asset.stream_id)} window={windows.at(-1)} windows={windows} claims={claims} feature={feature} playback={playback} runId={snapshot.run_id} /></div>;
        })}<UnavailableSources sources={unassignedSources} /></div><details className="input-guide"><summary><Icon name="folder" />Add your own recordings<span>Local files + manifest</span></summary><p>Put 2–6 GTA V screen recordings with visible chat in <code>data/recordings/inbox/</code>. Configure each file, streamer ID, trim start, timeline offset and chat crop in the recording manifest.</p><p>See <code>data/recordings/README.md</code> for preprocessing and launch commands. Extracted evidence is cached; playback does not rerun OCR or speech models.</p><p className="tiny muted">Current manifest: {snapshot.recording_manifest.manifest_version} · OCR: {snapshot.recording_manifest.ocr_version}</p></details></section>
        <section className="panel reaction-panel" aria-label="Reaction and supported-claim timeline"><div className="section-heading"><div><span className="section-index">02</span><h2>Reaction & supported claims</h2></div><span className="tiny muted">CONTEXT / QUALITY</span></div><div className="timeline-legend"><span className="cyan-text">Contextual reaction telemetry</span><span className="green-text">Supported quality claim</span><span className="negative">Excluded from estimate</span></div>{snapshot.recording_manifest.recordings.map(asset => <div className="reaction-source" key={asset.asset_id}><div className="reaction-source-name"><b>{asset.stream_id}</b><span>{asset.evidence_mode === 'recorded' ? 'Local recording' : 'Synthetic fixture'}</span></div><ReactionTelemetry reactions={(snapshot.reactions ?? []).filter(r => r.stream_id === asset.stream_id)} position={position} end={playbackDuration} recentSeconds={snapshot.reaction_recent_window_seconds ?? 30} /></div>)}<div className="claim-timeline">{snapshot.claims.filter(claim => claim.sentiment != null && claim.target === 'game').slice(-6).map(claim => <div key={claim.claim_id}><span className="mono cyan-text">{duration(snapshot.windows.find(w => w.window_id === claim.window_id)?.replay_seconds ?? 0)}</span><b>{claim.stream_id}</b><span className="green-text">Supported quality claim</span><span>“{claim.supporting_quote}”</span></div>)}</div><p className="panel-footnote">Text cues are heuristic. Loudness and facial emotion are not measured; activity alone does not establish game quality.</p></section>
        <section className="panel evidence-panel" id="evidence"><div className="section-heading"><div><span className="section-index">03</span><h2>Evidence tape</h2><Badge>{snapshot.windows.length} observations</Badge></div><div className="ledger-filters"><input type="search" placeholder="Find evidence…" aria-label="Search evidence" value={search} onChange={event => setSearch(event.target.value)} /><select aria-label="Filter by source" value={streamFilter} onChange={event => setStreamFilter(event.target.value)}><option value="all">All sources</option>{snapshot.streams.map(item => <option value={item.stream_id} key={item.stream_id}>{item.label}</option>)}</select></div></div>
          {displayedWindows.length ? <div className="evidence-list">{displayedWindows.map(window => {
            const claims = snapshot.claims.filter(item => item.window_id === window.window_id);
            const receipt = snapshot.receipts.find(item => item.window_ids.includes(window.window_id));
            return <article className="evidence-row" key={window.window_id}><div className="evidence-time mono">{duration(window.replay_seconds)}<span>REPLAY</span></div><div className="evidence-detail"><div className="evidence-title"><b>{snapshot.streams.find(item => item.stream_id === window.stream_id)?.label ?? window.stream_id}</b><span className="cyan-text tiny">{window.evidence_mode === 'synthetic_replay' ? 'Synthetic fixture' : window.source_modality === 'speech' ? 'Machine ASR' : 'Machine OCR'}</span><span className="tiny muted">{window.provider.replaceAll('_', ' ')}</span></div><p>“{window.raw_text || 'No transcribed words available'}”</p><div className="claim-tags">{claims.map(claim => <span key={claim.claim_id} title={claim.abstention_reason ?? undefined}>{claim.aspect?.replaceAll('_', ' ') ?? 'unattributed'} · {claim.sentiment == null ? 'abstained' : signed(claim.sentiment)} · {claim.target ?? 'unknown target'}</span>)}{!claims.length && <span>{window.observation?.abstention_reason ?? 'No attributable claim'}</span>}</div><details className="evidence-provenance"><summary>Source & extraction details</summary><div>Media {window.source_media_seconds.toFixed(2)}s · available +{Math.max(0, (Date.parse(window.available_at) - Date.parse(window.event_at)) / 1000).toFixed(2)}s · {window.evidence_mode.replaceAll('_', ' ')}</div><div>OCR confidence: {window.ocr_confidence == null ? window.confidence_reason ?? 'Unavailable for this source' : percent(window.ocr_confidence)}</div>{window.observation?.track_id && <div>OCR track: <code>{window.observation.track_id}</code></div>}<div>Source ID: <code>{window.observation_id}</code></div>{window.modalities.filter(item => !item.available).map(item => <div key={item.modality}>{item.modality}: {item.reason ?? 'Unavailable'}</div>)}<EvidenceArtifacts window={window} /></details></div><button type="button" className="text-button" disabled={!receipt} onClick={() => receipt && setReceiptId(receipt.receipt_id)}>Receipt<Icon name="arrow" size={15} /></button></article>;
          })}</div> : <div className="empty-state">{search ? 'No evidence matches this search.' : 'No extracted observations are available at this replay time.'}</div>}
          <div className="panel-footnote"><span><i className="live-dot" />Unique evidence only · refreshes do not add observations</span><button type="button" className="text-button" disabled={disabled} onClick={() => void desk.control('replay_observation')}>Replay same evidence<Icon name="reset" size={13} /></button></div>
        </section>
        <PaperActivity snapshot={snapshot} disabled={disabled} onExit={() => void desk.control('exit')} onTrace={setExecutionOrderId} />
        <section className="panel venue-panel" id="markets"><div className="section-heading"><div><span className="section-index">05</span><h2>Actual GTA VI venue context</h2><Badge tone={quoteModes.includes('live') ? 'green' : 'red'}>{quoteModes.includes('live') ? 'Live venue quotes' : 'Historical / stale'}</Badge></div><span className="tiny muted">SEPARATE FROM PROXY MODEL</span></div><p className="panel-intro">Returned venue tickers, rules and prices. GTA V demo evidence does not change these quotes or generate GTA VI estimates.</p>{snapshot.venue_context.error && <div className="inline-warning">{snapshot.venue_context.error}</div>}{snapshot.venue_context.quotes.length ? <div className="table-scroll" role="region" aria-label="Scrollable venue context table" tabIndex={0}><table><thead><tr><th>Market / resolution</th><th>Yes bid / ask</th><th>No bid / ask</th><th>Quote state</th><th>Captured</th></tr></thead><tbody>{snapshot.venue_context.quotes.map(quote => {
          const market = snapshot.venue_context.markets.find(item => item.market_id === quote.market_id);
          return <tr key={quote.quote_id}><td><b>{market?.title ?? quote.market_id}</b><small className="mono">{market?.venue_ticker ?? 'Ticker unavailable'}</small>{market && <details><summary>Resolution rules</summary><p>{market.rules_primary}</p></details>}</td><td className="mono">{cents(quote.yes_bid)} <span className="muted">/</span> {cents(quote.yes_ask)}</td><td className="mono">{cents(quote.no_bid)} <span className="muted">/</span> {cents(quote.no_ask)}</td><td><Badge tone={quote.is_stale ? 'red' : 'green'} dot>{quote.is_stale ? 'Stale' : quote.quote_mode === 'live' ? 'Live' : 'Synthetic'}</Badge><small>{quote.venue_status}</small></td><td title={quote.captured_at}><time dateTime={quote.captured_at}>{quote.captured_at}</time><small>{age(quote.captured_at, now)} / receipt time</small><small>{quote.source_ref.startsWith('data/snapshots/') ? 'Bundled historical capture' : 'Runtime public API receipt'} / {quote.source_ref}</small></td></tr>;
        })}</tbody></table></div> : <div className="empty-state">No venue quotes available. Recorded evidence replay remains independent.</div>}</section>

        <div className="bottom-grid g3-coverage"><section className="panel coverage-panel"><div className="section-heading"><div><Icon name="signal" /><h2>Coverage & limitations</h2></div></div><div className="coverage-metrics"><div><strong>{uniqueSources}</strong><span>Observed sources</span></div><div><strong>{manualSceneCount > 0 ? manualSceneCount : 'Unknown'}</strong><span>{manualSceneCount > 0 ? 'Manual scenes' : 'Unassigned scenes'}</span></div><div><strong>{latestFeature?.disagreement == null ? 'N/A' : latestFeature.disagreement.toFixed(2)}</strong><span>Disagreement</span></div></div><ul>{snapshot.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></section></div>
        </div><MarketRail snapshot={snapshot} onReceipt={setReceiptId} /></div>
        <footer className="desk-footer"><span><i className="live-dot" />LEONIDA ALPHA · LOCAL RESEARCH DESK</span><span className="mono">SCHEMA {desk.frame?.schema_version} · SEQ {desk.frame?.sequence} · UPDATED {desk.receivedAt ? `${Math.max(0, Math.floor((now - desk.receivedAt) / 1000))}s AGO` : 'UNAVAILABLE'}</span><details><summary>Cache provenance</summary><p className="mono">{snapshot.cache_key}</p><p>Configuration {snapshot.configuration_fingerprint}</p></details></footer>
        </>}
        <ReceiptDialog receipt={selectedReceipt} snapshot={snapshot} onClose={() => setReceiptId(null)} />
        <ExecutionTraceDialog order={selectedOrder} execution={snapshot.execution} onClose={() => setExecutionOrderId(null)} />
      </>}
    </main>
  </div>;
}

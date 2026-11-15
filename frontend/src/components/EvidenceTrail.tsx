import type { DashboardSnapshot } from '../generated/contracts';
import { Badge, Icon, cents, percent, signed } from './Primitives';

/** A compact, snapshot-backed walkthrough of one evidence-to-action chain. */
export function EvidenceTrail({ snapshot, onOpenDesk, onLoadDemo, onReceipt }: {
  snapshot: DashboardSnapshot;
  onOpenDesk: () => void;
  onLoadDemo: () => void;
  onReceipt: (receiptId: string) => void;
}) {
  const claim = snapshot.claims.filter(item => item.sentiment != null && item.target === 'game').at(-1)
    ?? snapshot.claims.at(-1);
  const window = claim ? snapshot.windows.find(item => item.window_id === claim.window_id) : snapshot.windows.at(-1);
  const feature = claim ? snapshot.features.find(item => item.claim_ids.includes(claim.claim_id)) : undefined;
  const estimate = feature ? snapshot.estimates.find(item => item.feature_ids.includes(feature.feature_id)) : undefined;
  const decision = estimate ? snapshot.decisions.find(item => item.estimate_id === estimate.estimate_id) : undefined;
  const market = snapshot.markets.find(item => item.market_id === (estimate?.market_id ?? decision?.market_id));
  const venueMatch = market ? snapshot.venue_context.markets.find(item => item.market_id === market.market_id) : undefined;
  const venueMarketsForGame = snapshot.venue_context.markets.filter(item => item.target_game_id && item.target_game_id === snapshot.target_game_id);
  const quoteId = estimate?.quote_id ?? decision?.quote_id;
  const quote = quoteId ? snapshot.quotes.find(item => item.quote_id === quoteId) : undefined;
  const receipt = snapshot.receipts.find(item => item.decision_id === decision?.decision_id)
    ?? snapshot.receipts.find(item => item.claim_ids.includes(claim?.claim_id ?? ''));
  const fills = (snapshot.execution?.fills ?? []).filter(fill => fill.market_id === (decision?.market_id ?? estimate?.market_id));
  const orders = (snapshot.execution?.orders ?? []).filter(order => order.market_id === (decision?.market_id ?? estimate?.market_id));
  const supported = claim?.sentiment != null && claim.target === 'game';
  const syntheticEvidence = window?.evidence_mode === 'synthetic_replay';
  const quoteLabel = !quote ? 'Quote unavailable' : quote.is_stale ? `${quote.quote_mode.replaceAll('_', ' ')} · stale` : `${quote.quote_mode.replaceAll('_', ' ')} quote`;

  return <section className="evidence-trail" id="trail" aria-labelledby="trail-title">
    <div className="trail-intro">
      <div><span className="eyebrow">DEMO WALKTHROUGH / CURRENT RUN</span><h2 id="trail-title">Follow one observation to its paper outcome</h2>
        <p>Each step below comes from this replay snapshot. Missing or blocked stages stay visible.</p></div>
      <div className="trail-labels"><Badge tone={syntheticEvidence ? 'amber' : window ? 'blue' : 'muted'}>{window ? (syntheticEvidence ? 'Synthetic replay evidence' : 'Recorded evidence') : `${snapshot.evidence_mode ?? 'Evidence'} · awaiting observation`}</Badge><Badge tone={!quote ? 'muted' : quote.is_stale ? 'red' : quote.quote_mode === 'live' ? 'green' : 'amber'}>{quoteLabel}</Badge><Badge>Heuristic · uncalibrated</Badge></div>
    </div>

    {!supported && snapshot.scenario_name === 'recordings' && <div className="trail-callout" role="status">
      <div><b>The included recordings currently abstain from quality scoring.</b><p>That is a real result: the clips provide context, but no supported game-quality claim enters the estimate. Load the labelled Courtroom scenario to see a complete synthetic walkthrough.</p></div>
      <button type="button" className="button" onClick={onLoadDemo}>Load Courtroom walkthrough <Icon name="arrow" size={14} /></button>
    </div>}

    <ol className="trail-steps">
      <li className="trail-step">
        <span className="trail-number">01</span><div className="trail-step-head"><h3>Source observation</h3><Badge tone={window ? 'blue' : 'muted'}>{window ? (window.source_modality === 'speech' ? 'Machine transcript' : window.provider.replaceAll('_', ' ')) : 'Waiting for evidence'}</Badge></div>
        {window ? <><blockquote>“{window.raw_text || 'No text available for this observation'}”</blockquote><p className="trail-meta">{snapshot.streams.find(item => item.stream_id === window.stream_id)?.label ?? window.stream_id} · replay {window.replay_seconds.toFixed(1)}s · {window.evidence_mode.replaceAll('_', ' ')} · {window.source_modality}</p><code className="trail-id">{window.observation_id}</code></> : <p className="trail-empty">No observation is available at this replay position yet. Press Play to advance.</p>}
      </li>
      <li className="trail-step">
        <span className="trail-number">02</span><div className="trail-step-head"><h3>Claim & eligibility</h3><Badge tone={supported ? 'green' : 'red'}>{supported ? 'Supported claim' : 'Abstained / excluded'}</Badge></div>
        {claim ? <><p>{claim.aspect?.replaceAll('_', ' ') ?? 'Aspect unavailable'} · target {claim.target ?? 'unknown'} · sentiment <b>{signed(claim.sentiment, 2)}</b></p><p className="trail-quote">“{claim.supporting_quote}”</p><p className="trail-meta">{supported ? 'Eligible for feature calculation, subject to market relevance.' : claim.abstention_reason ?? 'No supported game-quality claim is available.'}</p><code className="trail-id">{claim.claim_id}</code></> : <p className="trail-empty">No claim available yet.</p>}
      </li>
      <li className="trail-step">
        <span className="trail-number">03</span><div className="trail-step-head"><h3>Market match & estimate</h3><Badge tone={estimate ? 'green' : 'muted'}>{estimate ? 'Routed' : 'No model route'}</Badge></div>
        {market ? <><p><b>{market.title}</b></p><p className="trail-meta">{market.market_namespace.replaceAll('_', ' ')} · {market.venue_ticker || 'No venue ticker'} · evidence relevance {estimate ? percent(estimate.relevance) : 'unavailable'}</p><p className="trail-meta">{venueMatch ? `Matched venue contract: ${venueMatch.venue_ticker}` : 'This model route is not a matched Kalshi contract. Venue context below is shown separately and does not affect this estimate.'}</p></> : <p className="trail-empty">No market was matched to this evidence. {venueMarketsForGame.length ? `${venueMarketsForGame.length} Kalshi contract${venueMarketsForGame.length === 1 ? '' : 's'} for the target game appear in venue context, but none is linked to this model estimate.` : 'No target-game Kalshi contract is currently linked in venue context.'}</p>}
        {feature && <p>Absolute sentiment <b>{signed(feature.absolute_sentiment)}</b> · pre-update surprise <b>{signed(feature.mean_z)}</b></p>}
        {estimate ? <>{quote && <p className="trail-meta"><b>50% reference quote:</b> {market?.title ?? estimate.market_id} · YES bid {cents(quote.yes_bid)} / ask {cents(quote.yes_ask)} · {quote.quote_mode.replaceAll('_', ' ')}</p>}<p className="trail-probabilities">Quote-derived market reference <b>{percent(estimate.market_reference_probability)}</b><span aria-hidden="true">→</span> model estimate <b>{percent(estimate.model_probability)}</b></p><p className="trail-meta">Correction {signed(estimate.correction_log_odds, 3)} log-odds · {estimate.calibration_status ?? 'uncalibrated'} · {market?.title ?? estimate.market_id}</p><code className="trail-id">{estimate.estimate_id}</code></> : <p className="trail-empty">No estimate is produced without supported, relevant evidence and a valid quote.</p>}
      </li>
      <li className="trail-step">
        <span className="trail-number">04</span><div className="trail-step-head"><h3>Paper decision & execution</h3><Badge tone={decision?.eligible_for_fill ? 'green' : 'amber'}>{decision ? `${decision.action ?? 'candidate'} · ${decision.side.toUpperCase()}` : 'No decision'}</Badge></div>
        {decision ? <><p>{decision.eligible_for_fill ? 'Eligible for simulated fill' : 'Not eligible for fill'} · quantity {decision.quantity} · estimated fee {decision.estimated_total_fee}</p><p className="trail-meta">{decision.reasons[0] ?? snapshot.execution?.reason ?? 'Paper-only simulation'}</p>{quote && <p className="trail-meta">{quote.quote_mode.replaceAll('_', ' ')} quote Yes bid / ask {cents(quote.yes_bid)} / {cents(quote.yes_ask)} · captured {new Date(quote.captured_at).toLocaleTimeString()}</p>}<code className="trail-id">{decision.decision_id}</code>
          {fills.length > 0 ? <p className="trail-outcome">{fills.reduce((sum, item) => sum + Number(item.quantity), 0)} contracts filled across {fills.length} simulated fill{fills.length === 1 ? '' : 's'}.</p> : orders.length > 0 ? <p className="trail-meta">Order state: {orders.map(item => item.status).join(', ')}. No fill is shown unless one exists in the snapshot.</p> : <p className="trail-meta">No paper order or fill in this snapshot.</p>}
        </> : <p className="trail-empty">No paper decision is produced while the estimate is unavailable.</p>}
      </li>
    </ol>
    <div className="trail-footer"><span>Evidence: {window ? (syntheticEvidence ? 'synthetic fixture' : 'recorded source') : 'unavailable'} · Quote: {quoteLabel} · Execution: paper simulation only</span><div>{receipt && <button type="button" className="text-button" onClick={() => onReceipt(receipt.receipt_id)}>Open linked receipt <Icon name="arrow" size={14} /></button>}<button type="button" className="button secondary-button" onClick={onOpenDesk}>Open full evidence desk <Icon name="arrow" size={14} /></button></div></div>
  </section>;
}

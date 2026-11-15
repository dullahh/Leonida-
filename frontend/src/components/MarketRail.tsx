import type { DashboardSnapshot, MarketQuote } from '../generated/contracts';
import { Badge, Icon, age, cents, dollars, percent, signed } from './Primitives';
import { quoteReference } from './quoteReference';

function QuotePrice({ quote, side }: { quote?: MarketQuote; side: 'yes' | 'no' }) {
  return <div className="quote-price"><span>{side.toUpperCase()}</span><div><b title={quote?.missing_reasons?.[`${side}_bid`]}>{cents(quote?.[`${side}_bid`])}</b><i>/</i><b title={quote?.missing_reasons?.[`${side}_ask`]}>{cents(quote?.[`${side}_ask`])}</b></div><small>Bid / Ask · per contract</small></div>;
}

export function MarketRail({ snapshot, onReceipt }: { snapshot: DashboardSnapshot; onReceipt: (id: string) => void }) {
  const estimate = snapshot.estimates.at(-1);
  const decision = snapshot.decisions.at(-1);
  const market = snapshot.markets.find(item => item.market_id === estimate?.market_id) ?? snapshot.markets[0];
  const quote = snapshot.quotes.find(item => item.quote_id === estimate?.quote_id) ?? snapshot.quotes.at(-1);
  const receipt = snapshot.receipts.find(item => item.decision_id === decision?.decision_id);
  const candidateEv = decision?.side === 'yes' ? decision.yes_ev_per_contract : decision?.no_ev_per_contract;
  const hasSupportedClaims = snapshot.claims.some(claim => claim.sentiment != null && claim.target === 'game');
  const reference = quoteReference(quote, snapshot.replay_time);
  return <aside className="panel scenario-panel" id="scenario" aria-label="Market and model summary">
    <div className="rail-heading"><span className="eyebrow">MARKET / MODEL</span><span className="tiny amber-text">Synthetic quote</span></div>
    <div className="rail-market"><h2>{market?.title ?? 'Waiting for a scenario'}</h2><p className="tiny muted">GTA V proxy · actual GTA VI venue context is separate</p></div>
    <div className="quote-pair"><QuotePrice quote={quote} side="yes" /><QuotePrice quote={quote} side="no" /></div>
    <div className="quote-freshness" aria-label="Synthetic quote freshness"><Badge tone={!quote ? 'muted' : reference.midpoint == null ? 'red' : 'green'} dot>{!quote ? 'Quote unavailable' : reference.midpoint == null ? 'Stale / unavailable' : 'Fresh synthetic quote'}</Badge><span title={quote?.captured_at}>{quote ? `${quote.venue_status} · ${age(quote.captured_at, Date.parse(snapshot.replay_time))} · replay clock` : 'No scenario quote received'}</span></div>
    <div className="estimate-grid"><div><span>Market midpoint</span><strong className="amber-text" data-testid="quote-midpoint">{percent(reference.midpoint, 2)}</strong><small>Synthetic Yes midpoint / quote-derived</small></div><div><span>Model estimate</span><strong className={estimate ? 'green-text' : 'abstained'} data-testid="model-estimate">{estimate ? percent(estimate.model_probability) : hasSupportedClaims ? 'Evidence-adjusted estimate unavailable' : 'No supported quality claims'}</strong><small>Heuristic · uncalibrated</small></div></div>
    <p className="model-state" aria-label="Market and model state">Market midpoint {percent(reference.midpoint, 2)} · {estimate ? `Model estimate ${percent(estimate.model_probability)}` : 'Model abstained'} · {hasSupportedClaims ? 'Supported quality claim' : 'No supported quality claim'} · {decision ? `${decision.side.toUpperCase()} paper candidate` : 'No paper candidate'}</p>
    {reference.reason && <p className="rail-warning">{reference.reason}</p>}
    {estimate && <div className="probability-track" aria-label={`Market reference ${percent(estimate.market_reference_probability)}, model estimate ${percent(estimate.model_probability)}`}><div className="track-line" /><span className="marker market-marker" style={{ left: `${estimate.market_reference_probability * 100}%` }} /><span className="marker model-marker" style={{ left: `${estimate.model_probability * 100}%` }} /><div className="track-labels"><span>0%</span><span>100%</span></div></div>}
    <div className="correction-row"><span>Log-odds correction</span><b className="mono" data-testid="log-odds-correction">{signed(estimate?.correction_log_odds, 3)}</b></div>
    <div className="candidate-box"><div className="candidate-title"><span className="eyebrow">PAPER CANDIDATE</span><span className={decision ? 'green-text' : 'muted'}>{decision ? `${decision.side.toUpperCase()} side` : 'None'}</span></div><div className="candidate-value"><strong className={candidateEv == null ? 'candidate-unavailable' : ''} data-testid="paper-candidate">{candidateEv == null ? (!estimate ? 'Evidence-adjusted estimate unavailable' : 'No executable EV') : `${Number(candidateEv) > 0 ? '+' : ''}${(Number(candidateEv) * 100).toFixed(3)}¢`}</strong>{candidateEv != null && <span>net EV / contract</span>}</div><p>{decision?.reasons[0] ?? (!hasSupportedClaims ? reference.reason ? 'No current executable quote. No supported quality claim.' : 'Market quote available; no evidence-adjusted estimate because no supported quality claims exist.' : 'Evidence-adjusted estimate unavailable; no paper candidate can be formed.')}</p>{decision && <details><summary>Candidate eligibility & reasons</summary><ul>{decision.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul></details>}</div>
    <button className="button receipt-button" type="button" disabled={!receipt} onClick={() => receipt && onReceipt(receipt.receipt_id)}><Icon name="document" size={15} />Inspect full receipt<Icon name="arrow" size={15} /></button>
    <div className="rail-account"><span>Paper cash <b className="mono">{dollars(snapshot.cash_usd)}</b></span><span>{snapshot.order_count ?? 0} orders / {snapshot.fill_count ?? 0} simulated fills</span></div>
    {market && <details className="market-rules"><summary>Resolution & model context</summary><p>{market.rules_primary}</p><p className="mono tiny">{estimate?.model_version ?? 'Model unavailable'}</p><p className="mono tiny">Quote source: {quote?.source_ref ?? 'Unavailable'}</p></details>}
  </aside>;
}

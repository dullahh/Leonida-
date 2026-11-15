import { useEffect, useState } from 'react';
import type { LiveMarketCandidate, LiveMarketContext } from '../generated/live-market-context';
import { Badge, cents } from './Primitives';

type Props = {
  context: LiveMarketContext | null;
  loading: boolean;
  error: string | null;
};

const statusText: Record<LiveMarketContext['discovery_status'], string> = {
  matched: 'Named outcome markets found',
  stream_offline: 'Twitch channel is offline',
  twitch_unavailable: 'Twitch metadata unavailable',
  no_game_category: 'No game category reported',
  no_matching_markets: 'No matching open outcome markets',
  kalshi_unavailable: 'Kalshi discovery unavailable',
};

function quoteAge(capturedAt: string, now: number) {
  const seconds = Math.max(0, Math.floor((now - Date.parse(capturedAt)) / 1000));
  if (seconds < 60) return `${seconds}s old`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m old`;
  return `${Math.floor(seconds / 3600)}h old`;
}

function LiveMarketCard({ market, now }: { market: LiveMarketCandidate; now: number }) {
  return <article className="live-market-card">
    <div className="live-market-card-head">
      <div><span className="live-market-category">{market.category === 'video_games' ? 'VIDEO GAMES' : 'ESPORTS'}</span><h4>{market.event_title}</h4><p>{market.market_title}</p></div>
      <Badge tone={market.market_is_open === false ? 'red' : 'green'} dot>{market.market_status}</Badge>
    </div>
    <div className="live-market-outcome"><span>{market.match_rationale}</span><strong>{market.matched_game_name} · {market.outcome_name}</strong><code>{market.match_method} · {market.ticker}</code></div>
    <div className="live-market-quotes" aria-label={`Quote for ${market.ticker}`}>
      <div><span>YES bid / ask</span><strong>{cents(market.yes_bid)} / {cents(market.yes_ask)}</strong></div>
      <div><span>NO bid / ask</span><strong>{cents(market.no_bid)} / {cents(market.no_ask)}</strong></div>
    </div>
    <div className="live-market-provenance">
      <span>{market.quote_mode === 'live' && !market.is_stale ? 'Live quote' : 'Stale quote'} · {quoteAge(market.captured_at, now)} · captured <time dateTime={market.captured_at}>{market.captured_at}</time></span>
      <span>Event <code>{market.event_ticker}</code> · series <code>{market.series_ticker}</code></span>
      <span>Source <code>{market.source_ref}</code></span>
      {Object.entries(market.missing_reasons ?? {}).map(([field, reason]) => <span key={field}>{field}: {reason}</span>)}
    </div>
    <details className="live-market-rules"><summary>Resolution rules</summary>
      <p>{market.rules_primary ?? 'Primary resolution rules were not returned.'}</p>
      {market.rules_secondary && <p>{market.rules_secondary}</p>}
    </details>
  </article>;
}

export function LiveMarketMatches({ context, loading, error }: Props) {
  const candidates = context?.candidates ?? [];
  const decisionReviews = context?.decision_reviews ?? [];
  const candidatesById = new Map(candidates.map(candidate => [candidate.market_id, candidate]));
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  return <section className="live-markets-panel" aria-label="Live game market matches">
    <header><div><span className="eyebrow">LIVE GAME → KALSHI OUTCOMES</span><h3>Live market candidates</h3></div>
      {context && <Badge tone={context.discovery_status === 'matched' ? 'green' : 'amber'} dot>{statusText[context.discovery_status]}</Badge>}
    </header>
    {loading && <p className="live-markets-empty" role="status">Checking Twitch game metadata and current Video Games / Esports markets…</p>}
    {error && <p className="twitch-error" role="alert">{error}</p>}
    {!loading && context && <>
      <div className="live-game-context">
        <span>{context.game_source === 'manual' ? 'Manually entered game' : 'Stream category'}</span>
        <strong>{context.twitch.game_name ?? 'Unavailable'}</strong>
        <code>{context.twitch.game_id ?? (context.game_source === 'manual' ? 'User-provided game name' : 'No Twitch game ID')}</code>
        <span>{context.twitch.status === 'live' ? 'Live channel' : context.twitch.status === 'offline' ? 'Channel offline' : context.twitch.status === 'user_provided' ? 'Manual game selection' : 'Metadata unavailable'} · {context.twitch.channel_login ?? 'No Twitch channel linked'} · {context.twitch.source}</span>
        {context.twitch.reason && <span className="muted">{context.twitch.reason}</span>}
      </div>
      {context.market_error && <p className="inline-warning">Market discovery detail: {context.market_error}</p>}
      {candidates.length ? <div className="live-market-list">{candidates.map(market => <LiveMarketCard key={market.market_id} market={market} now={now} />)}</div>
        : <p className="live-markets-empty">{statusText[context.discovery_status]}{context.discovery_status === 'no_matching_markets' ? ' in the Video Games or Esports categories.' : '.'}</p>}
      {decisionReviews.length > 0 && <section className="live-decision-reviews" aria-label="Live decision review">
        <header><div><span className="eyebrow">PAPER ONLY · LIVE EVIDENCE</span><h4>Decision review</h4></div><Badge tone="amber">No orders</Badge></header>
        {decisionReviews.map(review => {
          const candidate = candidatesById.get(review.market_id);
          return <article className="live-decision-review" key={review.review_id}>
            <div><strong>ABSTAIN · no live paper estimate</strong><code>{candidate?.ticker ?? review.market_id}</code></div>
            <span>{review.model_version} · {review.calibration_status} · {review.execution_mode}</span>
            <ul>{review.reasons.map((reason, index) => <li key={`${review.review_id}-${index}`}>{reason}</li>)}</ul>
          </article>;
        })}
      </section>}
      <p className="live-market-disclaimer">These are exact named-outcome matches from live market data. The transcript is shown for review. Live reviews abstain until a validated live evidence-to-probability model is available; no probabilities, trade sides, or orders are implied.</p>
    </>}
    {!loading && !context && !error && <p className="live-markets-empty">Load a Twitch channel to resolve its game and candidate markets.</p>}
  </section>;
}

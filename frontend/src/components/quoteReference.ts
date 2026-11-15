import type { MarketQuote } from '../generated/contracts';

/** Display-only reference; never creates an estimate, candidate or order. */
export function quoteReference(quote: MarketQuote | undefined, replayTime: string): { midpoint: number | null; reason: string | null } {
  if (!quote) return { midpoint: null, reason: 'Market quote missing; no quote-derived reference available.' };
  const age = (Date.parse(replayTime) - Date.parse(quote.captured_at)) / 1000;
  if (quote.is_stale || age >= 10) return { midpoint: null, reason: 'Market quote stale; no current quote-derived reference available.' };
  if (!Number.isFinite(age) || age < 0) return { midpoint: null, reason: 'Market quote is not available at the current replay time.' };
  if (!['active', 'open'].includes(quote.venue_status)) return { midpoint: null, reason: `Market quote inactive (${quote.venue_status}).` };
  if (quote.yes_bid == null || quote.yes_ask == null) return { midpoint: null, reason: quote.missing_reasons?.yes_bid ?? quote.missing_reasons?.yes_ask ?? 'Two-sided Yes quote missing; midpoint unavailable.' };
  const bid = Number(quote.yes_bid), ask = Number(quote.yes_ask);
  if (!Number.isFinite(bid) || !Number.isFinite(ask) || bid < 0 || ask > 1 || bid > ask) return { midpoint: null, reason: 'Invalid Yes bid/ask; midpoint unavailable.' };
  if (ask - bid > .050000000001) return { midpoint: null, reason: 'Yes spread exceeds the current reference limit of 5¢.' };
  const midpoint = (bid + ask) / 2;
  return midpoint > 0 && midpoint < 1 ? { midpoint, reason: null } : { midpoint: null, reason: 'Endpoint quote cannot supply a model reference.' };
}

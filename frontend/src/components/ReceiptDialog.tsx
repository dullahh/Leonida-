import { useEffect, useRef } from 'react';
import type { DashboardSnapshot, Receipt } from '../generated/contracts';
import { Badge, Icon, signed, percent, cents, dollars } from './Primitives';

export function ReceiptDialog({ receipt, snapshot, onClose }: { receipt: Receipt | null; snapshot: DashboardSnapshot; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (receipt && !dialog.current?.open) dialog.current?.showModal();
    else if (!receipt && dialog.current?.open) dialog.current?.close();
  }, [receipt]);
  const estimate = snapshot.estimates.find(item => item.estimate_id === receipt?.estimate_id);
  const decision = snapshot.decisions.find(item => item.decision_id === receipt?.decision_id);
  const quote = snapshot.quotes.find(item => item.quote_id === receipt?.quote_id);
  return <dialog ref={dialog} className="receipt-dialog" onCancel={onClose} onClick={event => { if (event.target === dialog.current) onClose(); }} aria-labelledby="receipt-title">
    {receipt && <>
      <header><div><span className="eyebrow">Evidence → model → decision</span><h2 id="receipt-title">Decision receipt</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close receipt"><Icon name="close" /></button></header>
      <div className="receipt-content"><div className="badge-row"><Badge tone="amber">GTA V proxy evidence</Badge><Badge tone="blue">Paper</Badge><Badge>Heuristic · not calibrated</Badge></div>
        <section><h3>01 / Supporting evidence</h3>{receipt.window_ids.map(id => snapshot.windows.find(item => item.window_id === id)).filter(item => item != null).map(window => <blockquote key={window.window_id}><p>“{window.raw_text}”</p><footer>{window.stream_id} · {window.provider.replaceAll('_', ' ')} · media {window.source_media_seconds}s / replay {window.replay_seconds}s</footer></blockquote>)}</section>
        <section><h3>02 / Feature inputs</h3>{receipt.feature_ids.map(id => snapshot.features.find(item => item.feature_id === id)).filter(item => item != null).map(feature => <div className="receipt-feature" key={feature.feature_id}><div><span>Absolute sentiment</span><b>{signed(feature.absolute_sentiment)}</b></div><div><span>Pre-update surprise</span><b>{signed(feature.mean_z)} z</b></div><div><span>Baseline observations</span><b>{feature.baseline_count}</b></div><div><span>Unique observations</span><b>{feature.unique_observation_count}</b></div></div>)}</section>
        <section><h3>03 / Scenario estimate and costs</h3><div className="receipt-feature"><div><span>Synthetic market anchor</span><b>{percent(estimate?.market_reference_probability, 4)}</b></div><div><span>Heuristic estimate</span><b>{percent(estimate?.model_probability, 4)}</b></div><div><span>Bounded log-odds correction</span><b>{signed(estimate?.correction_log_odds, 5)}</b></div><div><span>Candidate / quantity</span><b>{decision?.side.toUpperCase() ?? 'Unavailable'} / {decision?.quantity ?? 'Unavailable'}</b></div><div><span>Yes ask / No ask</span><b>{cents(quote?.yes_ask)} / {cents(quote?.no_ask)}</b></div><div><span>Estimated fee (USD)</span><b>{dollars(decision?.estimated_total_fee)}</b></div></div><p className="tiny muted">Model {estimate?.model_version ?? 'unavailable'} · fee schedule {decision?.fee_schedule_version ?? 'unavailable'}</p></section>
        <section><h3>04 / Calculation and eligibility</h3><ol>{receipt.explanation.map((line, index) => <li key={index}>{line}</li>)}</ol>{decision && <div className="notice amber">{decision.reasons.map((reason, index) => <p key={index}>{reason}</p>)}</div>}</section>
        <section><h3>Limitations</h3><ul>{receipt.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul></section>
        <details><summary>Audit identifiers</summary><pre>{JSON.stringify({ run_id: receipt.run_id, receipt_id: receipt.receipt_id, window_ids: receipt.window_ids, claim_ids: receipt.claim_ids, feature_ids: receipt.feature_ids, estimate_id: receipt.estimate_id, decision_id: receipt.decision_id, quote_id: receipt.quote_id }, null, 2)}</pre></details>
      </div>
    </>}
  </dialog>;
}

'use strict';
const $ = id => document.getElementById(id);
let activeRun = null, sequence = -1, socket = null, lastFrame = null, reconnectTimer = null, fallbackTimer = null, connecting = false;
const money = value => value === null || value === undefined ? 'Unavailable' : '$' + Number(value).toFixed(3);
const probability = value => (100 * value).toFixed(2) + '%';
const text = (id, value) => { $(id).textContent = value; };
function el(tag, content, cls) { const node = document.createElement(tag); if (content !== undefined) node.textContent = content; if (cls) node.className = cls; return node; }
function notice(value) { text('notice', value); }
function accept(frame, fromRest = false) {
  if (frame.schema_version !== '2' || frame.type !== 'snapshot' || frame.run_id !== frame.payload.run_id || !Number.isSafeInteger(frame.sequence)) throw new Error('Unsupported or invalid state envelope');
  if (activeRun && frame.run_id !== activeRun) return;
  if (frame.sequence <= sequence) return;
  if (!fromRest && sequence >= 0 && frame.sequence > sequence + 1) { fetchState().catch(showError); return; }
  activeRun = frame.run_id; sequence = frame.sequence; lastFrame = frame;
  render(frame);
}
function render(frame) {
  const p = frame.payload, f = p.features[0], estimate = p.estimates[0], d = p.decisions[0], q = p.quotes[0], claim = p.claims[0], w = p.windows[0], receipt = p.receipts[0];
  text('run-label', frame.run_id); text('sequence', 'SCHEMA ' + frame.schema_version + ' / SEQUENCE ' + frame.sequence);
  text('evidence-mode', p.evidence_mode === 'synthetic_replay' ? 'Synthetic fixture · cached' : 'Recorded · cached');
  text('sentiment', f.absolute_sentiment.toFixed(2)); text('surprise', f.mean_z.toFixed(2) + ' z');
  text('baseline-note', 'Seeded baseline · ' + f.unique_observation_count + ' unique observation');
  text('probability', probability(estimate.model_probability));
  text('anchor-note', 'Reference ' + probability(estimate.market_reference_probability) + ' · Δ log-odds ' + estimate.correction_log_odds.toFixed(3));
  text('ev', money(d.side === 'no' ? d.no_ev_per_contract : d.yes_ev_per_contract));
  text('side-note', 'BUY ' + d.side.toUpperCase() + ' candidate · USD / contract');
  text('market-title', p.markets[0].title); text('yes-price', money(q.yes_bid) + ' / ' + money(q.yes_ask)); text('no-price', money(q.no_bid) + ' / ' + money(q.no_ask));
  text('reference-number', probability(estimate.market_reference_probability)); text('model-number', probability(estimate.model_probability));
  $('reference-bar').style.width = (estimate.market_reference_probability * 100) + '%'; $('model-bar').style.width = (estimate.model_probability * 100) + '%';
  text('decision-side', 'BUY ' + d.side.toUpperCase() + ' · ' + d.quantity + ' contracts proposed');
  $('decision-reasons').replaceChildren(...d.reasons.map(reason => el('li', reason)));
  text('cash', '$' + Number(p.cash_usd).toLocaleString('en-GB', {minimumFractionDigits:2})); text('orders', String(p.order_count)); text('fills', String(p.fill_count));
  text('supporting-quote', '“' + claim.supporting_quote + '”'); text('scene', claim.scene_id);
  text('source-offset', 'Media ' + w.source_media_seconds + 's → replay ' + w.replay_seconds + 's · Chat text is fixture supplied; OCR has not run.');
  $('explanation').replaceChildren(...receipt.explanation.map(line => el('li', line)));
  text('receipt-ids', ['Window  ' + w.window_id, 'Claim   ' + claim.claim_id, 'Feature ' + f.feature_id, 'Quote   ' + q.quote_id, 'Model   ' + estimate.model_version, 'Receipt ' + receipt.receipt_id].join('\n'));
  $('receipt-link').href = '/api/runs/' + encodeURIComponent(activeRun) + '/receipts/' + encodeURIComponent(receipt.receipt_id);
  text('cache-key', p.cache_key); $('cache-key').title = p.cache_key;
  const sourceNodes = p.recording_manifest.recordings.map((asset, index) => {
    const row = el('article', undefined, 'source'); const preview = el('div', String(index + 1).padStart(2, '0') + ' / V', 'source-placeholder');
    preview.setAttribute('aria-label', 'No video supplied'); const info = el('div'); info.append(el('h3', asset.label));
    info.append(el('div', 'Trim ' + asset.media_start_seconds + 's · timeline ' + asset.timeline_start_seconds + 's · sample every ' + asset.sample_interval_seconds + 's', 'source-info'));
    info.append(el('div', 'Chat crop configured · GTA V proxy', 'source-info'));
    info.append(el('div', p.streams.find(s => s.stream_id === asset.stream_id)?.reason || 'Unavailable', 'source-status'));
    row.append(preview, info); return row;
  });
  $('source-list').replaceChildren(...sourceNodes);
  renderVenue(p.venue_context);
}
function renderVenue(context) {
  const opened = new Set([...document.querySelectorAll('#venue-rows details[open]')].map(node => node.dataset.marketId));
  const rows = context.quotes.map(q => {
    const m = context.markets.find(m => m.market_id === q.market_id); const row = el('tr'); const name = el('td', m?.title || q.market_id);
    name.append(el('small', m?.venue_ticker || q.market_id));
    const rules = el('details'); rules.dataset.marketId = q.market_id; rules.open = opened.has(q.market_id); rules.append(el('summary', 'Inspect captured rules')); rules.append(el('p', m?.rules_primary || 'Unavailable')); name.append(rules);
    const age = Math.max(0, (Date.now() - Date.parse(q.captured_at)) / 1000);
    const stale = q.is_stale || age >= 10;
    const freshness = (stale ? 'STALE · ' : 'LIVE · ') + (age < 60 ? Math.floor(age) + 's' : Math.floor(age / 60) + 'm');
    const cell = el('td', freshness); cell.title = 'Captured ' + q.captured_at; cell.dataset.quoteTime = q.captured_at; cell.dataset.stale = String(q.is_stale);
    row.append(name, el('td', money(q.yes_bid) + ' / ' + money(q.yes_ask)), el('td', money(q.no_bid) + ' / ' + money(q.no_ask)), cell); return row;
  });
  if (!rows.length) { const row=el('tr'), cell=el('td', 'No actual venue quotes available. Scenario still works offline.'); cell.colSpan=4; row.append(cell); rows.push(row); }
  $('venue-rows').replaceChildren(...rows);
  const live = context.quotes.some(q => !q.is_stale && q.quote_mode === 'live' && Date.now() - Date.parse(q.captured_at) < 10000);
  text('venue-mode', live ? 'LIVE PUBLIC QUOTE' : 'HISTORICAL / UNAVAILABLE');
  text('venue-note', context.error || ('Observed ' + context.observed_at + ' · public data · candidate context only'));
}
function refreshVenueAges() {
  let anyLive = false;
  document.querySelectorAll('[data-quote-time]').forEach(cell => {
    const age = Math.max(0, (Date.now() - Date.parse(cell.dataset.quoteTime)) / 1000);
    const stale = cell.dataset.stale === 'true' || age >= 10;
    anyLive = anyLive || !stale;
    cell.textContent = (stale ? 'STALE · ' : 'LIVE · ') + (age < 60 ? Math.floor(age) + 's' : Math.floor(age / 60) + 'm');
  });
  text('venue-mode', anyLive ? 'LIVE PUBLIC QUOTE' : 'HISTORICAL / UNAVAILABLE');
}
async function fetchState() {
  const requested = activeRun; const response = await fetch('/api/state' + (requested ? '?run_id=' + encodeURIComponent(requested) : ''));
  if (!response.ok) throw new Error('State request failed: ' + response.status);
  const frame = await response.json(); if (requested && requested !== activeRun) return; accept(frame, true);
}
function showError(error) { notice(error.message || String(error)); }
function connect() {
  if (!activeRun || connecting) return; connecting = true;
  const run = activeRun; const next = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws?run_id=' + encodeURIComponent(run)); socket = next;
  next.onopen = () => { connecting = false; if (next !== socket) return; text('connection', 'State connected'); clearInterval(fallbackTimer); fallbackTimer = null; };
  next.onmessage = event => { if (next !== socket || run !== activeRun) return; try { accept(JSON.parse(event.data)); } catch (error) { showError(error); } };
  next.onerror = () => { if (next === socket) text('connection', 'Reconnecting'); };
  next.onclose = () => {
    if (next !== socket || run !== activeRun) return; connecting = false; text('connection', 'REST fallback');
    if (!fallbackTimer) fallbackTimer = setInterval(() => fetchState().catch(showError), 2000);
    clearTimeout(reconnectTimer); reconnectTimer = setTimeout(connect, 1500);
  };
}
async function command(action) {
  $('reset').disabled = $('replay').disabled = true;
  try {
    const response = await fetch('/api/runs/' + encodeURIComponent(activeRun) + '/control', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command_id:crypto.randomUUID(), action})});
    if (!response.ok) throw new Error('Command failed: ' + response.status); const result = await response.json();
    if (action === 'reset') {
      activeRun = result.run_id; sequence = -1; lastFrame = null; connecting = false;
      const old = socket; socket = null; if (old) old.close(); clearTimeout(reconnectTimer); clearInterval(fallbackTimer); fallbackTimer = null;
      await fetchState(); connect(); notice('New isolated demo run. Cached inputs and calculated result are repeatable.');
    } else { await fetchState(); notice('Duplicate observation recognized. Baseline, estimate, cash and fill count are unchanged.'); }
  } catch (error) { showError(error); } finally { $('reset').disabled = $('replay').disabled = false; }
}
$('replay').onclick = () => command('replay_observation'); $('reset').onclick = () => command('reset');
fetchState().then(() => { notice('One cached fixture observation. Actual video decoding and sampled-frame OCR are the next pipeline increment.'); connect(); }).catch(showError);
setInterval(() => { if (lastFrame) refreshVenueAges(); }, 1000);

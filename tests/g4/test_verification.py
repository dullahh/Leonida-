"""G4 checks against the G3 checkpoint. No external services or media providers."""
import asyncio
from collections import Counter
from decimal import Decimal as D
import json
from pathlib import Path
import socket
import tempfile
import unittest

import httpx
import uvicorn
from playwright.async_api import async_playwright
from websockets.asyncio.client import connect

from backend.core.config import ROOT
from backend.core.runtime import Runtime
from backend.core.schemas import RunCommand, StreamEnvelope
from backend.execution.paper import BrokerState, QuoteBook, DepthLevel, execute_due, dump_state, plan_entry, plan_exit
from backend.quant.normalization import Baseline, normalize
from datetime import timedelta
from backend.main import create_app

CACHE = ROOT / 'var/evidence-cache/aa20c31e1a27bbf0fe075f2c9136360e7096731d9365cdd247c89ade4afe95b6.json'


class Verification(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().set_debug(False)
        self.temp = tempfile.TemporaryDirectory(prefix='leonida-g4-')
        self.folder = Path(self.temp.name)
        self.runtimes = []

    async def asyncTearDown(self):
        for runtime in self.runtimes:
            await runtime.close()
        self.temp.cleanup()

    def runtime(self, name='courtroom-praise', cache=None, db=None):
        r = Runtime(db or self.folder / f'{len(self.runtimes)}.sqlite3', self.folder / 'cache', scenario=name, evidence_cache_path=cache)
        self.runtimes.append(r)
        return r

    async def seek(self, r, at):
        await r.control(r.active_run_id, RunCommand(command_id=f'seek-{at}', action='seek', position_seconds=at))
        return r.snapshot().payload

    async def test_three_speed_partitions_and_restart_full_state(self):
        results = []
        for speed in (.5, 2, 5):
            r = self.runtime()
            await r.control(r.active_run_id, RunCommand(command_id='speed', action='set_speed', speed=speed))
            for at in range(int(10 * speed), 310, int(10 * speed)):
                await self.seek(r, at)
            p = await self.seek(r, 310)
            results.append(([(f.direction, f.quantity, f.fee, f.at) for f in p.execution.fills], p.cash_usd,
                            [(e.correction_log_odds, e.model_probability) for e in p.estimates],
                            [(x.observation_id, x.valence, x.intensity, x.included_in_estimate) for x in p.reactions]))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        r = self.runtimes.pop()
        before = r.snapshot().payload
        broker = dump_state(r.store.load_broker(r.active_run_id)[1])
        db = r.store.connection.execute('PRAGMA database_list').fetchone()[2]
        await r.close()
        restored = self.runtime(db=Path(db))
        await restored.start()
        self.assertEqual(restored.snapshot().payload, before)
        self.assertEqual(dump_state(restored.store.load_broker(restored.active_run_id)[1]), broker)

    async def test_all_five_cached_reactions_recovery_and_read_dedup(self):
        self.assertTrue(CACHE.is_file(), 'Local five-recording cache required for this acceptance check')
        r = self.runtime(cache=CACHE)
        p = await self.seek(r, r.snapshot().payload.playback.duration_seconds)
        self.assertEqual(Counter(w.stream_id for w in p.windows), {'t1':105,'t2':221,'t3':303,'t4':467,'t5':555})
        self.assertEqual(len({x.observation_id for x in p.reactions}), 1651)
        self.assertFalse(any(x.pricing_eligible for x in p.reactions))
        self.assertFalse(p.estimates)
        self.assertFalse(p.execution.orders)
        before = r.snapshot()
        for index in range(3):
            await r.control(r.active_run_id, RunCommand(command_id=f'duplicate-{index}', action='replay_observation'))
            self.assertEqual(r.snapshot(), before)
        db = Path(r.store.connection.execute('PRAGMA database_list').fetchone()[2])
        self.runtimes.remove(r)
        await r.close()
        restored = self.runtime(cache=CACHE, db=db)
        await restored.start()
        self.assertEqual(restored.snapshot().payload, before.payload)

    async def test_missing_quote_cancels_pending_without_cash_change(self):
        r = self.runtime()
        await self.seek(r, 1)
        state = r.store.load_broker(r.active_run_id)[1]
        self.assertTrue(state.reserved_cash > 0)
        result = execute_due(state, books={}, probabilities={}, as_of=state.orders[0].eligible_at)
        self.assertEqual(result.state.cash, D('10000'))
        self.assertFalse(result.state.fills)
        self.assertEqual(result.state.orders[0].status, 'cancelled')
        self.assertEqual(result.state.reserved_cash, 0)

    async def test_no_side_depth_fee_exit_and_mode_gates(self):
        r = self.runtime()
        quote = r.snapshot().payload.quotes[0].model_copy(update={
            'yes_bid':D('.14'),'yes_ask':D('.15'),'no_bid':D('.85'),'no_ask':D('.86')})
        now = quote.captured_at
        book = QuoteBook(quote,'no-depth',no_asks=(DepthLevel(D('.86'),D(4)),),no_bids=(DepthLevel(D('.85'),D(4)),))
        state = BrokerState('no-check')
        blocked = plan_entry(state,intent_id='recorded',game_id='gta5',side='no',probability=D('.097'),book=book,as_of=now,evidence_mode='recorded',simulation_authorized=True)
        self.assertIsNone(blocked.order)
        pending = plan_entry(state,intent_id='entry',game_id='gta5',side='no',probability=D('.097'),book=book,as_of=now,evidence_mode='synthetic_replay',simulation_authorized=True).state
        filled = execute_due(pending,books={quote.market_id:book},probabilities={quote.market_id:D('.097')},as_of=now+timedelta(seconds=.25)).state
        self.assertEqual(filled.cash,D('9996.52'))
        self.assertEqual(filled.fills[0].fee,D('.04'))
        self.assertEqual(filled.positions[0].quantity,D(4))
        exit_state = plan_exit(filled,intent_id='exit',market_id=quote.market_id,book=book,as_of=now+timedelta(seconds=1)).state
        closed = execute_due(exit_state,books={quote.market_id:book},probabilities={},as_of=now+timedelta(seconds=1.25)).state
        self.assertFalse(closed.positions)
        self.assertEqual(closed.cash,D('9999.88'))
        self.assertEqual(closed.realized_pnl,D('-.12'))
        self.assertEqual(execute_due(closed,books={quote.market_id:book},probabilities={},as_of=now+timedelta(seconds=2)).state,closed)

    async def test_warmup_constant_inputs_and_preupdate_surprise(self):
        baseline = Baseline()
        for index in range(21):
            result = normalize(.2,baseline)
            self.assertEqual(result.previous,baseline)
            if index<20:self.assertIsNone(result.z)
            else:self.assertTrue(-4<=result.z<=4)
            baseline=result.updated
        result=normalize(-.4,Baseline(mean=-.8,variance=.04,count=20))
        self.assertAlmostEqual(result.z,2)
        self.assertLess(result.absolute,0)

    async def test_isolated_browser_transport_receipts_and_layout(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(create_app(self.folder/'browser.sqlite3', evidence_cache_path=CACHE),
            host='127.0.0.1', port=port, log_level='error', timeout_graceful_shutdown=3))
        task = asyncio.create_task(server.serve())
        url = f'http://127.0.0.1:{port}'
        try:
            async with httpx.AsyncClient(base_url=url, timeout=30, trust_env=False) as client:
                for _ in range(100):
                    if server.started: break
                    await asyncio.sleep(.1)
                self.assertTrue(server.started)
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(channel='msedge', headless=True)
                    try:
                        page = await browser.new_page(base_url=url, viewport={'width':1440,'height':1050})
                        errors = []
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
                        await page.goto('/', wait_until='networkidle')
                        await page.locator('video').evaluate_all('(vs)=>vs.forEach(v=>v.load())')
                        await page.wait_for_function('[...document.querySelectorAll("video")].length===5 && [...document.querySelectorAll("video")].every(v=>v.videoWidth===1920)', timeout=30000)
                        await page.get_by_label('Replay speed').select_option('2')
                        await asyncio.sleep(.3)
                        await page.get_by_role('button', name='Play replay', exact=True).click()
                        await asyncio.sleep(1.5)
                        await page.get_by_role('button', name='Pause replay', exact=True).click()
                        await asyncio.sleep(.4)
                        f = (await client.get('/api/state')).json()
                        times = await page.locator('video').evaluate_all('(vs)=>vs.map(v=>v.currentTime)')
                        self.assertTrue(all(abs(t-f['payload']['playback']['position_seconds'])<.7 for t in times), (times,f['payload']['playback']))
                        rid = f['run_id']
                        response = await client.post(f'/api/runs/{rid}/control', json={'command_id':'end','action':'seek','position_seconds':67.566667})
                        response.raise_for_status()
                        await asyncio.sleep(1.5)
                        f = StreamEnvelope.model_validate_json((await client.get('/api/state')).text)
                        async with connect(url.replace('http','ws')+'/ws?run_id='+rid, max_size=16*1024*1024, proxy=None) as ws:
                            self.assertEqual(StreamEnvelope.model_validate_json(await ws.recv()), f)
                        for source, count in [('t1',105),('t2',221),('t3',303),('t4',467),('t5',555)]:
                            await page.get_by_label('Filter by source').select_option(source)
                            self.assertEqual(await page.locator('.evidence-row').count(), count)
                        window = next(w for w in f.payload.windows if w.frame_ref)
                        self.assertEqual((await client.get('/api/evidence/artifact',params={'run_id':rid,'ref':window.frame_ref})).status_code,200)
                        self.assertEqual((await client.get('/api/evidence/artifact',params={'ref':'../secrets'})).status_code,404)
                        await page.set_viewport_size({'width':390,'height':844})
                        self.assertTrue(await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                        await page.set_viewport_size({'width':1440,'height':1050})
                        self.assertTrue(await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                        await page.locator('#scenario-selector').select_option('courtroom-praise')
                        await page.get_by_role('button',name='Load isolated scenario').click()
                        await asyncio.sleep(1)
                        fresh = (await client.get('/api/state')).json()['run_id']
                        self.assertNotEqual(rid,fresh)
                        await client.post(f'/api/runs/{fresh}/control',json={'command_id':'quality','action':'seek','position_seconds':7})
                        await asyncio.sleep(1.5)
                        self.assertEqual(await page.locator('.reaction-exclusion.included').count(),3)
                        p = (await client.get('/api/state')).json()['payload']
                        self.assertGreater(p['estimates'][0]['model_probability'],.5)
                        for receipt in p['receipts']:
                            self.assertEqual((await client.get(f"/api/runs/{fresh}/receipts/{receipt['receipt_id']}")).status_code,200)
                        await page.get_by_role('button',name='Inspect full receipt').click()
                        await page.get_by_role('heading',name='Decision receipt',exact=True).wait_for()
                        await page.get_by_role('button',name='Close receipt',exact=True).click()
                        fallback = await browser.new_page(base_url=url)
                        await fallback.route_web_socket('**/ws*', lambda ws: ws.close())
                        await fallback.goto('/',wait_until='networkidle')
                        await fallback.get_by_text('REST fallback',exact=True).wait_for(timeout=10000)
                        self.assertEqual((await client.get('/api/state')).json()['payload']['fill_count'],p['fill_count'])
                        await fallback.close()
                        # A new socket receives the same committed full state.
                        async with connect(url.replace('http','ws')+'/ws?run_id='+fresh, max_size=16*1024*1024, proxy=None) as ws:
                            socket_frame=StreamEnvelope.model_validate_json(await ws.recv())
                            self.assertEqual(socket_frame,StreamEnvelope.model_validate_json((await client.get('/api/state')).text))
                        await page.get_by_role('button',name='Reset to a new run').click()
                        await asyncio.sleep(1)
                        reset = (await client.get('/api/state')).json()
                        self.assertNotEqual(reset['run_id'],fresh)
                        self.assertEqual(reset['payload']['fill_count'],0)
                        self.assertEqual((await client.get('/api/state',params={'run_id':fresh})).json()['payload']['fill_count'],p['fill_count'])
                        self.assertEqual((await client.post(f'/api/runs/{rid}/control',json={'command_id':'old','action':'play'})).status_code,409)
                        self.assertFalse(errors,errors)
                    finally:
                        await browser.close()
        finally:
            server.should_exit = True
            await asyncio.wait_for(task,15)

"""Display-only regression: quote availability is independent of evidence."""
import asyncio
import json
from pathlib import Path
import socket
import tempfile
import unittest

import uvicorn
from playwright.async_api import async_playwright

from backend.core.clock import utc_now
from backend.core.market import historical_context
from backend.core.config import ROOT, read_config
from backend.core.media_projection import project
from backend.core.schemas import StreamEnvelope
from backend.ingestion.replay import load_scenario
from backend.main import create_app


class QuoteClarity(unittest.IsolatedAsyncioTestCase):
    async def test_midpoint_abstention_reasons_and_venue_separation(self):
        asyncio.get_running_loop().set_debug(False)
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            cache = load_scenario('courtroom-praise', folder/'cache')
            observation = cache.observations[0].model_copy(update={
                'raw_text':'Give me a phone.', 'supporting_quote':'Give me a phone.',
                'sentiment':None, 'abstention_reason':'No attributable quality opinion.',
                'target':'unrelated', 'aspect':'overall', 'replay_seconds':0,
                'available_replay_seconds':0})
            cache = cache.model_copy(update={'observations':[observation]})
            venue = historical_context(ROOT/'data/snapshots',read_config('market_registry.json')['aliases'])
            payload = project('quote-display-test',cache,2,1,False,'quote-display',venue)
            self.assertFalse(payload.estimates)
            self.assertFalse(payload.decisions)
            self.assertEqual(payload.order_count,0)
            frame = StreamEnvelope(run_id=payload.run_id,sequence=1,generated_at=utc_now(),payload=payload).model_dump(mode='json')
            with socket.socket() as bound:
                bound.bind(('127.0.0.1',0))
                port=bound.getsockname()[1]
            server=uvicorn.Server(uvicorn.Config(create_app(folder/'display.sqlite3',folder/'runtime-cache'),host='127.0.0.1',port=port,log_level='error',timeout_graceful_shutdown=3))
            task=asyncio.create_task(server.serve())
            try:
                for _ in range(100):
                    if server.started: break
                    await asyncio.sleep(.1)
                self.assertTrue(server.started)
                async with async_playwright() as pw:
                    browser=await pw.chromium.launch(channel='msedge',headless=True)
                    try:
                        page=await browser.new_page(viewport={'width':1440,'height':1050})
                        errors=[]
                        page.on('pageerror',lambda error:errors.append(str(error)))
                        page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
                        await page.route('**/api/state*',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(frame)))
                        await page.route_web_socket('**/ws*',lambda ws:ws.close())
                        await page.goto(f'http://127.0.0.1:{port}',wait_until='networkidle')
                        self.assertEqual(await page.get_by_test_id('quote-midpoint').inner_text(),'14.50%')
                        self.assertEqual(await page.get_by_test_id('model-estimate').inner_text(),'No supported quality claims')
                        self.assertEqual(await page.get_by_test_id('log-odds-correction').inner_text(),'Unavailable')
                        self.assertEqual(await page.get_by_test_id('paper-candidate').inner_text(),'Evidence-adjusted estimate unavailable')
                        await page.get_by_text('Market quote available; no evidence-adjusted estimate because no supported quality claims exist.',exact=True).wait_for()
                        self.assertIn('Synthetic Yes midpoint',await page.locator('#scenario').inner_text())
                        self.assertIn('Bundled historical capture',await page.locator('#markets').inner_text())
                        self.assertIn('2026-11-14T22:52:',await page.locator('#markets').inner_text())
                        self.assertIn('Historical / stale',await page.locator('#markets').inner_text())
                        self.assertEqual(len(frame['payload']['execution']['orders']),0)
                        self.assertTrue(await page.get_by_role('button',name='Inspect full receipt').is_disabled())
                        self.assertGreater(await page.get_by_text('No attributable quality opinion',exact=True).count(),0)
                        self.assertGreater(await page.get_by_text('Qualifying baseline not established',exact=True).count(),0)
                        for width in (1440,390):
                            await page.set_viewport_size({'width':width,'height':900})
                            self.assertTrue(await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                        frame['payload']['quotes'][0]['is_stale']=True
                        await page.reload(wait_until='networkidle')
                        self.assertEqual(await page.get_by_test_id('quote-midpoint').inner_text(),'Unavailable')
                        await page.get_by_text('Market quote stale; no current quote-derived reference available.',exact=True).wait_for()
                        frame['payload']['quotes'][0]['is_stale']=False
                        frame['payload']['quotes'][0]['yes_ask']=None
                        frame['payload']['quotes'][0]['missing_reasons']={'yes_ask':'Yes ask absent from source quote.'}
                        await page.reload(wait_until='networkidle')
                        await page.get_by_text('Yes ask absent from source quote.',exact=True).wait_for()
                        frame['payload']['quotes']=[]
                        await page.reload(wait_until='networkidle')
                        await page.get_by_text('Market quote missing; no quote-derived reference available.',exact=True).wait_for()
                        self.assertEqual(await page.get_by_test_id('model-estimate').inner_text(),'No supported quality claims')
                        self.assertFalse(errors,errors)
                    finally:
                        await browser.close()
            finally:
                server.should_exit=True
                await asyncio.wait_for(task,15)

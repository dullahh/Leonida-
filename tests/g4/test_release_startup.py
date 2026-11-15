"""Release input selection and missing-input recovery; no media processing."""
import json
from pathlib import Path
import tempfile
import unittest
from backend.core.runtime import Runtime
from backend.core.schemas import CreateRunRequest
from scripts.manage import select_demo


class ReleaseStartup(unittest.TestCase):
    def test_empty_checkout_and_stale_pointer_fall_back(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(select_demo('auto',root=root)[:2],('courtroom-praise',None))
            (root/'var').mkdir()
            (root/'var/last-recording-cache.txt').write_text('missing.json')
            self.assertEqual(select_demo('recordings',root=root)[:2],('courtroom-praise',None))

    def test_existing_cache_missing_video_offers_portable(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            cache=root/'cache.json'
            cache.write_text(json.dumps({'manifest':{'recordings':[{'local_path':'missing.mp4'}]}}))
            scenario,cache,note=select_demo('auto',cache,root)
            self.assertEqual((scenario,cache),('courtroom-praise',None))
            self.assertIn('portable',note)

    def test_explicit_portable_ignores_local_inputs(self):
        self.assertEqual(select_demo('portable',Path('missing'))[:2],('courtroom-praise',None))


class ReleaseModeRecovery(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_launch_does_not_restore_another_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            first=Runtime(root/'run.sqlite3',root/'cache',scenario='courtroom-praise')
            await first.create_run(CreateRunRequest(command_id='outage',scenario='venue-outage-reset'))
            old_id=first.active_run_id
            await first.close()
            restored=Runtime(root/'run.sqlite3',root/'cache',scenario='courtroom-praise')
            try:
                self.assertEqual(restored.snapshot().payload.scenario_name,'courtroom-praise')
                self.assertNotEqual(restored.active_run_id,old_id)
                self.assertEqual(restored.snapshot(old_id).payload.scenario_name,'venue-outage-reset')
            finally:
                await restored.close()

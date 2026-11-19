import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from curio25.recovery import choose_episode, prepare
from curio25.state import connect, restore, sha


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root/'data'
        (self.data/'snapshots').mkdir(parents=True)
        proof=self.data/'snapshots/proof.txt'
        proof.write_text('reviewed proof')
        digest=sha(proof)
        (self.data/'source_audit.json').write_text(json.dumps([{
            'url':'https://example.org/proof','path':'data/snapshots/proof.txt','sha256':digest}]))
        (self.data/'facts.json').write_text(json.dumps([
            {'id':f'f{i}','claim':f'claim {i}','review_status':'verified',
             'source_url':'https://example.org/proof','source_snapshot_sha256':digest,
             'evidence_query':'reviewed proof','narration':f'narration {i}'} for i in range(25)]))
        self.history([])

    def history(self, records):
        (self.data/'history.json').write_text(json.dumps({'episodes':records,'used_facts':[],'claims':[]}))

    def test_oldest_reservation_is_reused_next_day(self):
        self.history([{'id':'daily-2026-11-18','status':'reserved','video_id':None,'sha':None}])
        self.assertEqual(choose_episode(self.root,'daily-2026-11-19'),'daily-2026-11-18')

    def test_uncertain_upload_never_retried(self):
        self.history([{'id':'daily-2026-11-18','status':'uploading'}])
        with self.assertRaises(ValueError):
            choose_episode(self.root,'daily-2026-11-19')

    def test_pilot_and_future_reservations_not_recovered(self):
        for ident in ('pilot-001','daily-2026-11-20'):
            self.history([{'id':ident,'status':'reserved'}])
            with self.assertRaises(ValueError):
                choose_episode(self.root,'daily-2026-11-19')

    def test_multiple_reservations_block(self):
        self.history([{'id':f'daily-2026-11-{i}','status':'reserved'} for i in (17,18)])
        with self.assertRaises(ValueError):
            choose_episode(self.root,'daily-2026-11-19')

    @patch('curio25.recovery.audit')
    def test_durable_reservation_survives_fresh_runner(self, audit):
        ident='daily-2026-11-18'
        first=prepare(self.root,ident)
        self.assertEqual(first['fact_count'],25)
        (self.data/'history.sqlite').unlink()
        second=prepare(self.root,ident)
        self.assertEqual(first,second)
        db=connect(':memory:')
        restore(db,self.data/'history.json')
        self.assertEqual(db.execute('SELECT COUNT(*) FROM episodes').fetchone()[0],1)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM used').fetchone()[0],25)
        db.close()

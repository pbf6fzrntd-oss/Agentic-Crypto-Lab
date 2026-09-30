import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest
from research_v2.engine import Engine,timestamp,validate_snapshot
from research_v2.demo import snapshots,cockpit

class SnapshotTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.path=str(Path(self.temp.name)/'journal.sqlite');self.engine=Engine(self.path)
    def tearDown(self):self.engine.close();self.temp.cleanup()
    def test_fill_is_after_formation_and_policy_is_persisted(self):
        source=snapshots();first=self.engine.apply(source[0])[0]
        self.assertEqual(first['state'],'AWAITING_FILL');self.assertIsNone(first['entry_date'])
        opened=self.engine.apply(source[1])[0]
        self.assertGreater(timestamp(opened['entry_date']),timestamp(opened['decision_formed_at']))
        self.assertEqual(opened['interval'],'1d');self.assertEqual(opened['holding_period_bars'],5)
        completed=self.engine.apply(source[2])[0];self.assertEqual(completed['state'],'COMPLETE');self.assertAlmostEqual(completed['benchmark_return'],1.12/1.045-1);self.assertAlmostEqual(completed['net_return'],108/103-1-0.003)
    def test_repeated_and_overlapping_runs_create_one_economic_decision(self):
        source=snapshots()[0]
        def apply(_):
            engine=Engine(self.path)
            try:engine.apply(source)
            finally:engine.close()
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(apply,range(2)))
        self.assertEqual(len(self.engine.rows()),1)
    def test_mature_review_happens_before_new_signal(self):
        source=snapshots();self.engine.apply(source[0]);opened=self.engine.apply(source[1])[0]
        for n in range(9):
            seeded={**opened,'id':f'seed-{n}','economic_key':f'seed-{n}'};self.engine._put(seeded)
        last=copy.deepcopy(source[2]);last['theses']=copy.deepcopy(source[0]['theses']);last['theses']['BTC-USD'].update(completed_at=last['observed_at'],input_cutoff='2026-09-08T00:00:00+00:00')
        rows=self.engine.apply(last);self.assertEqual(sum(r['state']=='COMPLETE' for r in rows),10);self.assertEqual(sum(r['state']=='AWAITING_FILL' for r in rows),1)
    def test_invalid_stale_missing_future_data_and_symbols_fail_without_writes(self):
        for change in ['nan','missing','future','symbol','stale','cutoff']:
            source=copy.deepcopy(snapshots()[0])
            if change=='nan':source['markets']['BTC-USD']['bars'][0]['open']=float('nan')
            if change=='missing':del source['markets']['ETH-USD']
            if change=='future':source['markets']['BTC-USD']['bars'][-1]['start']='2026-09-04T00:00:00+00:00'
            if change=='symbol':source['markets']['BTC-USD']['provider_symbol']='OTHER/USD'
            if change=='stale':source['observed_at']='2026-09-10T12:00:00+00:00'
            if change=='cutoff':source['theses']['BTC-USD']['completed_at']='2026-09-02T00:00:00+00:00'
            with self.assertRaises(ValueError):self.engine.apply(source)
            self.assertEqual(self.engine.rows(),[])
    def test_demo_and_paper_cannot_mix_and_benchmark_anchor_cannot_change(self):
        self.engine.apply(snapshots()[0]);next_snapshot=copy.deepcopy(snapshots()[1]);next_snapshot['evidence_class']='SNAPSHOT_PAPER'
        with self.assertRaises(ValueError):self.engine.apply(next_snapshot)
        next_snapshot=snapshots()[1];next_snapshot['markets']['ETH-USD']['bars'][0]['open']=51
        with self.assertRaises(ValueError):self.engine.apply(next_snapshot)
    def test_revised_same_time_snapshot_rejected(self):
        self.engine.apply(snapshots()[0]);revised=snapshots()[0];revised['theses']['BTC-USD']['reasoning']='revised'
        with self.assertRaises(ValueError):self.engine.apply(revised)
    def test_cockpit_escapes_thesis_and_legacy_content(self):
        source=snapshots()[0];source['theses']['BTC-USD']['reasoning']='<script>alert(1)</script>'
        rows=self.engine.apply(source);page=cockpit(rows,[{'ticker':'<script>alert(2)</script>'}]);self.assertIn('&lt;script&gt;',page);self.assertNotIn('<script>alert(',page)

if __name__=='__main__':unittest.main()

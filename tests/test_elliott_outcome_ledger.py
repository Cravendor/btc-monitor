from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts import elliott_outcome_ledger as ledger
from scripts.market_scenarios import iso
from tests.test_elliott_candidates import source, P


class FrozenLedgerTests(unittest.TestCase):
    def test_fixed_candidate_invalidated_by_later_wick_without_mutation(self):
        rows=source(); now=iso(rows[-1]['open_time_ms']+P)
        snap=ledger.freeze(rows,'4h',now,'complete'); saved=deepcopy(snap)
        extra=dict(rows[-1],open_time_ms=rows[-1]['open_time_ms']+P,low=140,high=160,open=155,close=155)
        result=ledger.evaluate(snap,rows+[extra],iso(extra['open_time_ms']+P),'complete')
        target=next(x for x in result['results'] if x['candidate_id']==snap['inventory']['candidates'][-1]['id'])
        self.assertEqual(target['status'],'invalidated')
        self.assertEqual(target['first_invalid_known_at'],iso(extra['open_time_ms']+P))
        self.assertEqual(snap,saved);self.assertIsNone(result['probability'])

    def test_source_conflict_stale_gap_and_revision_are_not_silent(self):
        rows=source();now=iso(rows[-1]['open_time_ms']+P)
        with self.assertRaises(ValueError): ledger.freeze(rows,'4h',now,'conflict')
        with self.assertRaises(ValueError): ledger.freeze(rows,'4h',iso(rows[-1]['open_time_ms']+2*P),'complete')
        snap=ledger.freeze(rows,'4h',now,'complete')
        extra=dict(rows[-1],open_time_ms=rows[-1]['open_time_ms']+P)
        revised=deepcopy(rows);revised[0]['close']+=.01
        for bad in (revised+[extra],rows[:-1]+[extra]):
            with self.assertRaises(ValueError): ledger.evaluate(snap,bad,iso(extra['open_time_ms']+P),'complete')
        altered=deepcopy(snap);altered['inventory']['candidates'][0]['direction']='forged'
        with self.assertRaises(ValueError): ledger.evaluate(altered,rows+[extra],iso(extra['open_time_ms']+P),'complete')
        with self.assertRaises(ValueError): ledger.evaluate(snap,rows+[extra],iso(extra['open_time_ms']+P),'conflict')

    def test_atomic_content_addressed_idempotence_and_tamper_detection(self):
        with TemporaryDirectory() as folder:
            p=ledger.save_immutable(folder,{'value':1})
            self.assertEqual(p,ledger.save_immutable(folder,{'value':1}))
            p.write_text('changed')
            with self.assertRaises(ValueError):ledger.save_immutable(folder,{'value':1})
            self.assertEqual(p.read_text(),'changed')
            self.assertEqual(len(list(Path(folder).iterdir())),1)

    def test_weekly_closed_boundaries_align_to_monday(self):
        from scripts.elliott_history import floor_time
        week=7*24*3600000
        rows=source();start=floor_time(rows[0]['open_time_ms'],'1w')
        rows=[dict(r,open_time_ms=start+i*week) for i,r in enumerate(rows)]
        snap=ledger.freeze(rows,'1w',iso(rows[-1]['open_time_ms']+week),'complete')
        extra=dict(rows[-1],open_time_ms=rows[-1]['open_time_ms']+week)
        outcome=ledger.evaluate(snap,rows+[extra],iso(extra['open_time_ms']+week),'complete')
        self.assertEqual(outcome['closed_through'],iso(extra['open_time_ms']+week))

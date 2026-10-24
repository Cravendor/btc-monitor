from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse,parse_qs
from scripts.cycle_history import run,reference,rows_from,load,DAY,START
from scripts.market_scenarios import time_ms
from scripts.collect import main as collect_main

NOW='2022-02-01T05:30:00Z'


class Source:
    def __init__(self,fault=None):self.calls=[];self.fault=fault
    def __call__(self,url,transform,bitget):
        q=parse_qs(urlparse(url).query);self.calls.append(q)
        self_outer=self
        assert bitget and q['granularity']==['1Dutc']
        start=int(q['startTime'][0]);end=int(q['endTime'][0])
        assert end-start<=90*DAY
        raw=[[str(t),'100','110','90','100','10','1000'] for t in range(start,end+DAY,DAY)]
        if self.fault=='error':return dict(status='error',data=None)
        if self.fault=='empty':raw=[]
        if self.fault=='gap':raw.pop(3)
        if self.fault=='malformed':raw[2][2]='nan'
        if self.fault=='conflict':raw[0][2]='999'
        try:return dict(status='ok',data=transform(raw),observed_at=NOW)
        except ValueError:return dict(status='error',data=None)


class CycleHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'history.json'

    def test_complete_history_exact_utc_coverage_and_open_upper_day_excluded(self):
        source=Source();r=run(self.path,NOW,requester=source)
        self.assertEqual(r['status'],'complete');self.assertEqual(r['missing_days'],0)
        expected=(time_ms(NOW)//DAY*DAY-time_ms(START))//DAY
        self.assertEqual(r['candle_count'],expected)
        self.assertEqual(len(source.calls),(expected+83)//84)
        rows,pages=load(self.path,time_ms(NOW)//DAY*DAY)
        self.assertEqual(len(rows),expected)
        self.assertLess(max(rows),time_ms(NOW)//DAY*DAY)
        self.assertEqual(reference(self.path,NOW)['status'],'complete')

    def test_checkpoints_resume_without_repeating_completed_windows(self):
        first=Source();r=run(self.path,NOW,max_pages=1,requester=first)
        self.assertEqual(r['status'],'partial');self.assertEqual(r['candle_count'],84)
        second=Source();complete=run(self.path,NOW,requester=second)
        self.assertEqual(complete['status'],'complete')
        self.assertEqual(int(second.calls[0]['startTime'][0]),time_ms(START)+83*DAY)
        no_call=Source();again=run(self.path,NOW,requester=no_call)
        self.assertEqual(again['content_sha256'],complete['content_sha256']);self.assertFalse(no_call.calls)

    def test_incomplete_bad_or_inaccessible_window_does_not_claim_coverage(self):
        for fault in ('gap','empty','error','malformed'):
            with self.subTest(fault=fault):
                p=Path(self.tmp.name)/(fault+'.json');r=run(p,NOW,requester=Source(fault))
                self.assertEqual(r['status'],'partial');self.assertEqual(r['candle_count'],0)
                self.assertEqual(r['first_missing_at'],'2021-01-01T00:00:00+00:00')

    def test_revision_conflict_preserves_previously_saved_candles(self):
        old=run(self.path,NOW,max_pages=1,requester=Source())
        failed=run(self.path,NOW,requester=Source('conflict'))
        self.assertEqual(failed['reason'],'source_revision_conflict')
        self.assertEqual(failed['content_sha256'],old['content_sha256'])

    def test_cached_identity_checksum_and_duplicates_are_rejected(self):
        run(self.path,NOW,requester=Source());original=self.path.read_text()
        for fault in ('identity','checksum','duplicate'):
            d=json.loads(original)
            if fault=='identity':d['market']='SPOT'
            if fault=='checksum':d['candles'][0]['high']=999
            if fault=='duplicate':d['candles'].append(d['candles'][0])
            self.path.write_text(json.dumps(d));before=self.path.read_text()
            with self.assertRaises(ValueError):run(self.path,NOW,requester=Source())
            self.assertEqual(self.path.read_text(),before)
            self.assertEqual(reference(self.path,NOW)['status'],'unavailable')

    def test_time_budget_stops_before_next_request_and_new_day_becomes_partial(self):
        source=Source();r=run(self.path,NOW,seconds=1,requester=source)
        self.assertFalse(source.calls);self.assertEqual(r['reason'],'time_budget')
        run(self.path,NOW,requester=Source())
        tomorrow='2022-02-02T05:30:00Z';r=reference(self.path,tomorrow)
        self.assertEqual(r['status'],'partial');self.assertEqual(r['missing_days'],1)
        self.assertNotIn('candles',r)

    def test_same_and_conflicting_duplicate_responses(self):
        row=[str(time_ms(START)),'100','110','90','100','0','0']
        self.assertEqual(len(rows_from([row,row],time_ms(NOW)//DAY*DAY)),1)
        other=list(row);other[2]='120'
        with self.assertRaises(ValueError):rows_from([row,other],time_ms(NOW)//DAY*DAY)

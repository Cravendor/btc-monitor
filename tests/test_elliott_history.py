from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse,parse_qs
from scripts import elliott_history as eh
from scripts.elliott_dashboard import build,render
from scripts.market_scenarios import iso,time_ms
from scripts.cycle_history import report as daily_report,save
from tests.test_price_roadmap import fixture

NOW='2025-07-25T13:30:00Z'


def provider(calls, missing=False, revision=False):
    def get(url,transform,bitget):
        q={k:v[0] for k,v in parse_qs(urlparse(url).query).items()}
        calls.append(q)
        tf=next(t for t in eh.TF if eh.GRANULARITIES[t]==q['granularity'])
        period=eh.PERIOD_MS[tf]
        rows=[[str(t),'100','110','90','105','10','1000'] for t in range(int(q['startTime']),int(q['endTime']),period)]
        if missing and tf=='4h':rows.pop(2)
        if revision and tf=='1h' and int(q['startTime'])>time_ms(eh.START):rows[0][1]='101'
        return dict(status='ok',observed_at=NOW,data=transform(rows))
    return get


class HistoryTests(unittest.TestCase):
    def test_preserved_live_probe_isolates_week_close_and_base_conflict(self):
        path=Path(__file__).resolve().parents[1]/'data/history/source-audits/20261026T172221Z-week-day-4h.json'
        audit=json.loads(path.read_text());start=time_ms(audit['window_start']);end=time_ms(audit['window_end'])
        rows={tf:{t:r for t,r in eh.rows_from(s['data'],tf,end).items() if start<=t<end}
              for tf,s in audit['sources'].items()}
        self.assertEqual([len(rows[tf]) for tf in ('1w','1d','4h')],[1,7,42])
        q=eh.reconcile(rows['1d'],list(rows['1w'].values()),'1d','1w')
        self.assertEqual(q['status'],'conflict')
        fields=q['mismatch_details'][0]['fields']
        self.assertEqual(set(fields),{'close','base_volume_btc'})
        self.assertEqual(fields['close'],dict(native='80125.5',from_children='80119.2',native_minus_children='6.3'))
        self.assertEqual(fields['base_volume_btc']['native_minus_children'],'-0.0432')
        self.assertEqual(q['quote_volume_max_abs_difference_usdt'],'3461.34025')
        lower=eh.reconcile(rows['4h'],list(rows['1d'].values()),'4h','1d')
        self.assertEqual(lower['checked_candles'],7)
        self.assertEqual(lower['mismatch_details'],[])
        self.assertEqual(lower['status'],'consistent_checked_groups')

    def test_conflict_detail_is_bounded_and_does_not_change_source_rows(self):
        base=dict(open=100,high=110,low=90,close=105,base_volume_btc=10,quote_volume_usdt=1000)
        source={t:dict(base,open_time_ms=t) for t in range(0,6*14400000,3600000)}
        parents=[dict(base,open_time_ms=t,base_volume_btc=40,quote_volume_usdt=4000,high=111)
                 for t in range(0,6*14400000,14400000)]
        before=deepcopy((source,parents));q=eh.reconcile(source,parents,'1h','4h')
        self.assertEqual(q['mismatch_candles'],6)
        self.assertEqual(len(q['mismatch_details']),5)
        self.assertTrue(q['mismatch_details_truncated'])
        self.assertEqual((source,parents),before)

    def test_batch_checkpoints_resume_and_skip_completed_degrees(self):
        with tempfile.TemporaryDirectory() as folder:
            calls=[]
            first=eh.run(folder,NOW,max_pages=3,requester=provider(calls))
            self.assertEqual(first['1h']['status'],'partial')
            self.assertEqual(first['4h']['status'],'complete')
            self.assertEqual(first['1w']['status'],'complete')
            before=len(calls)
            second=eh.run(folder,NOW,max_pages=6,requester=provider(calls))
            self.assertTrue(all(q['status']=='complete' for q in second.values()))
            self.assertTrue(all(q['granularity']=='1H' for q in calls[before:]))
            again=eh.run(folder,NOW,max_pages=6,requester=provider(calls))
            self.assertEqual(len(calls),before+3)
            for tf in eh.TF:
                rows,pages=eh.load(eh.filename(folder,tf),tf,eh.floor_time(time_ms(NOW),tf))
                self.assertEqual(len(rows),again[tf]['required_candles'])
                self.assertLessEqual(max(time_ms(p['end'])-time_ms(p['start'])+eh.PERIOD_MS[tf] for p in pages),90*86400000)

    def test_gap_rejected_without_fabricated_candles_other_degrees_continue(self):
        with tempfile.TemporaryDirectory() as folder:
            q=eh.run(folder,NOW,max_pages=8,requester=provider([],missing=True))
            self.assertEqual(q['4h']['reason'],'incomplete_response_window')
            self.assertEqual(q['4h']['candle_count'],0)
            self.assertEqual(q['1h']['status'],'complete')

    def test_revision_conflict_preserves_first_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            eh.run(folder,NOW,max_pages=3,requester=provider([]))
            path=eh.filename(folder,'1h')
            before=json.loads(path.read_text())['candles']
            q=eh.run(folder,NOW,max_pages=8,requester=provider([],revision=True))
            self.assertEqual(q['1h']['reason'],'source_revision_conflict')
            self.assertEqual(json.loads(path.read_text())['candles'],before)

    def test_cache_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            eh.run(folder,NOW,max_pages=3,requester=provider([]))
            path=eh.filename(folder,'1h');data=json.loads(path.read_text())
            data['candles'][0]['close']=104
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'checksum'):
                eh.run(folder,NOW,max_pages=3,requester=provider([]))

    def test_budget_and_next_closed_hour_are_independently_recomputed(self):
        with tempfile.TemporaryDirectory() as folder:
            eh.run(folder,NOW,max_pages=8,requester=provider([]))
            rows,_=eh.load(eh.filename(folder,'1h'),'1h',eh.floor_time(time_ms(NOW)+3600000,'1h'))
            self.assertEqual(eh.coverage(rows,'1h',iso(time_ms(NOW)+3600000))['missing_candles'],1)
        with tempfile.TemporaryDirectory() as folder:
            calls=[];times=iter([0,10,10,10])
            q=eh.run(folder,NOW,max_pages=3,seconds=16,clock=lambda:next(times),requester=provider(calls))
            self.assertEqual(calls,[])
            self.assertTrue(all(x['reason']=='time_budget' for x in q.values()))

    def test_original_daily_archive_is_reused_without_rewriting(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'data/history/bitget_btcusdt_daily.json'
            start=time_ms(eh.START);end=eh.floor_time(time_ms(NOW),'1d')
            rows={t:dict(open_time_ms=t,open=100.,high=110.,low=90.,close=105.,base_volume_btc=10.,quote_volume_usdt=1000.) for t in range(start,end,86400000)}
            save(path,daily_report(rows,[dict(observed_at=NOW)],start,end,NOW,'test'))
            original=path.read_bytes();q=eh.read(root,NOW)
            self.assertEqual(q['1d']['status'],'complete')
            self.assertEqual(q['1d']['candle_count'],24)
            self.assertEqual(path.read_bytes(),original)

    def test_long_source_is_not_replaced_by_short_snapshot_when_missing(self):
        f,now=fixture()
        incomplete={tf:dict(status='partial',rows=[],missing_candles=1,candle_count=23,required_candles=24) for tf in ('1w','1d','4h','1h')}
        b=build(f,now,incomplete)
        self.assertTrue(all(h['status']=='unavailable' for h in b['horizons']))
        self.assertEqual(render(b).count('class="ew-chart"'),0)
        self.assertIn('niet stilzwijgend vervangen',render(b))

    def test_complete_archive_can_be_inspected_with_stale_snapshot_no_old_ticker(self):
        f,now=fixture();history={}
        for tf,metric in f['measurements'][0]['metrics']['multi_timeframe']['data'].items():
            history[tf]=dict(status='complete',rows=deepcopy(metric['data']['candles']),source_at=now,source_path='test.json')
        b=build(f,iso(time_ms(now)+7200000),history)
        self.assertEqual(b['horizons'][0]['status'],'available')
        self.assertIsNone(b['horizons'][0]['price'])
        self.assertIsNone(b['current_wave'])

    def test_missing_newest_candle_keeps_dated_history_visible_without_bridging(self):
        f,now=fixture();metric=f['measurements'][0]['metrics']['multi_timeframe']['data']['4h']
        rows=deepcopy(metric['data']['candles'])
        gap=rows[-1]['open_time_ms']+eh.PERIOD_MS['4h']
        history={'4h':dict(status='partial',rows=rows+[dict(rows[-1],open_time_ms=gap+eh.PERIOD_MS['4h'])],
                 source_at=now,source_path='test.json',first_missing_at=iso(gap),
                 candle_count=25,required_candles=26,missing_candles=1)}
        b=build(f,now,history);h=b['horizons'][2]
        self.assertEqual(h['status'],'available')
        self.assertEqual(len(h['rows']),24)
        self.assertEqual(b['status'],'partial')
        self.assertIn('ONVOLLEDIGE HISTORIE',render(b))

    def test_cross_timeframe_rejects_price_conflict_and_skips_incomplete_groups(self):
        base=dict(open=100,high=110,low=90,close=105,base_volume_btc=10,quote_volume_usdt=1000)
        source={t:dict(base,open_time_ms=t) for t in range(0,14400000,3600000)}
        parent=dict(base,open_time_ms=0,base_volume_btc=40,quote_volume_usdt=4000.000001)
        q=eh.reconcile(source,[parent],'1h','4h')
        self.assertEqual(q['mismatch_candles'],0)
        self.assertEqual(q['quote_volume_max_abs_difference_usdt'],'0.000001')
        parent['high']=111
        self.assertEqual(eh.reconcile(source,[parent],'1h','4h')['status'],'conflict')
        del source[0]
        q=eh.reconcile(source,[parent],'1h','4h')
        self.assertEqual(q['checked_candles'],0)
        self.assertEqual(q['skipped_incomplete_groups'],1)

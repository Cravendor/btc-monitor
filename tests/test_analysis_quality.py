from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest
import re
from unittest.mock import patch
from scripts.analysis_quality import assess,review,stage,METHOD,WINDOW,report_findings

END=1792915200000
NOW='2026-10-25T08:02:00Z'


def record():
    row=dict(open_time_ms=END-WINDOW,open=100,high=102,low=99,close=101,
             base_volume_btc=2,quote_volume_usdt=201)
    return dict(exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',collection_source='nas',
        status='ok',finished_at=NOW,metrics={
            'futures_price':dict(status='ok',observed_at=NOW,data=dict(lastPr='101',symbol='BTCUSDT')),
            'candles_4h':dict(status='ok',data=dict(candles=[row],closed_only=True,interval='4H',gap_count=0))},
        cvd_4h=dict(markets={m:dict(status='ok',coverage_verified=True,coverage_method=METHOD,
            coverage_scope='bitget_public_history_only',exchange='bitget',symbol='BTCUSDT',market=m,
            unit='BTC',validated_delta_btc='-0.5',interval_start_ms=END-WINDOW,interval_end_ms=END)
            for m in ('spot','usdt_futures')}))


class QualityTests(unittest.TestCase):
    def test_release_gate_accepts_zoom_and_checks_each_chart_against_sources(self):
        from scripts.home_dashboard import build as build_home
        from scripts.elliott_dashboard import build as build_visual
        from tests.test_price_roadmap import fixture
        from tests.test_elliott_dashboard import wave_rows
        feed, now = fixture()
        for metric in feed['measurements'][0]['metrics']['multi_timeframe']['data'].values():
            metric['data']['candles'] = wave_rows(metric['data']['candles'])
        with tempfile.TemporaryDirectory() as root, patch('scripts.elliott_history.read', return_value=None):
            folder = Path(root)
            source = folder/'data/latest.json'
            source.parent.mkdir()
            source.write_text(json.dumps(feed))
            for name in ('btc-dashboard.html','btc-status.html','btc-timeframes.html',
                         'btc-signal-history.html','status.mjs','status.css'):
                (folder/name).write_text('fixture')
            build_home(source, folder/'index.html', now)
            page = (folder/'index.html').read_text()
            svg = re.findall(r'<svg\b[^>]*\bclass="ew-chart"[^>]*>.*?</svg>', page, re.S)
            available = sum(h['status']=='available' for h in build_visual(feed,now)['horizons'])
            self.assertGreater(len(svg), 2*available)
            self.assertEqual(stage(source,folder,now)['elliott_visuals']['charts'],len(svg))
            for broken in (page.replace(svg[0],'',1), page.replace(svg[0],svg[0]*2,1)):
                (folder/'index.html').write_text(broken)
                with self.assertRaisesRegex(ValueError,'source/chart count mismatch'):
                    stage(source,folder,now)
            # Same count, wrong source window / geometry must still fail.
            (folder/'index.html').write_text(page.replace(svg[0],svg[-1],1))
            with self.assertRaisesRegex(ValueError,'source/chart content mismatch'):
                stage(source,folder,now)

    def test_upload_success_does_not_hide_unverified_or_wrong_interval_cvd(self):
        r=record();self.assertEqual(assess(r,NOW)['status'],'ready_for_scoped_report')
        for change in ({'coverage_verified':False},{'interval_end_ms':END-WINDOW},
                       {'validated_delta_btc':'NaN'},{'market':'spot'}):
            x=deepcopy(r);x['cvd_4h']['markets']['usdt_futures'].update(change)
            q=assess(x,NOW)
            self.assertEqual(q['status'],'degraded')
            self.assertEqual(q['price_structure'],'available')
            self.assertIn('cvd_usdt_futures',[i['code'] for i in q['issues']])
        self.assertEqual(assess(r,NOW)['macro_cycle_verdict'],'requires_separate_macro_evidence')

    def test_native_timeframe_grade_is_recomputed_not_trusted(self):
        from scripts.multi_timeframe_signals import assess as signal
        r=record();rows=[]
        for i in range(24):
            rows.append(dict(open_time_ms=END-(24-i)*300000,open=100,high=101,low=99,
                             close=100,base_volume_btc=1,quote_volume_usdt=100))
        native=dict(status='ok',observed_at=NOW,data=dict(candles=rows),signal=signal(rows,'5m',NOW))
        r['metrics']['multi_timeframe']=dict(status='ok',data={'5m':native})
        self.assertEqual(assess(r,NOW)['status'],'ready_for_scoped_report')
        native['signal']['grade']='bullish'
        self.assertIn('timeframe_5m',[i['code'] for i in assess(r,NOW)['issues']])

    def test_direct_script_import_works_in_isolated_nas_style_runtime(self):
        import subprocess,sys
        code="import sys,json;sys.path.insert(0,sys.argv[1]);from analysis_quality import assess;print(json.dumps(assess(json.loads(sys.argv[2]),sys.argv[3])))"
        r=subprocess.run([sys.executable,'-I','-c',code,str(Path(__file__).resolve().parents[1]/'scripts'),json.dumps(record()),NOW],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['status'],'ready_for_scoped_report')

    def test_stale_invalid_prices_candles_and_future_data_rejected(self):
        for value in ('NaN',None,'-1','0'):
            r=record();r['metrics']['futures_price']['data']['lastPr']=value
            self.assertEqual(assess(r,NOW)['price_structure'],'unavailable')
        for change in ({'open_time_ms':END},{'high':98},{'quote_volume_usdt':-1}):
            r=record();r['metrics']['candles_4h']['data']['candles'][0].update(change)
            self.assertEqual(assess(r,NOW)['price_structure'],'unavailable')
        self.assertEqual(assess(record(),'2026-10-25T14:00:00Z')['price_structure'],'unavailable')

    def test_broken_scenario_processing_is_not_approved(self):
        r=record();r['scenario_snapshot']={'status':'ready','horizons':{}}
        self.assertEqual(assess(r,NOW)['scenario_processing'],'rejected')

    def test_repeat_snapshots_are_not_independent_failed_intervals_and_recovery_closes_blocker(self):
        r=record();r['cvd_4h']['markets']['spot']['coverage_verified']=False
        with tempfile.TemporaryDirectory() as root:
            same=review({'measurements':[r,deepcopy(r)]},NOW,root)
            self.assertEqual(same['recurring_blockers'],[])
            old=deepcopy(r);old['finished_at']='2026-10-25T04:02:00Z'
            many=review({'measurements':[r,old]},NOW,root)
            self.assertEqual(many['recurring_blockers'][0]['affected_closed_intervals'],2)
            recovered=review({'measurements':[record(),r,old]},NOW,root)
            self.assertEqual(recovered['recurring_blockers'],[])

    def test_original_report_contradiction_is_flagged_without_rewriting(self):
        from scripts.monitor_archive import checksum,extract_bias
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'reports/2026/10/25/daily.json';p.parent.mkdir(parents=True)
            text='Richting: macro Neutraal/gemengd wegens ONVOLDOENDE DATA.'
            raw=dict(schema_version=2,monitor='daily',source='chatgpt_monitor',reported_at=NOW,
                     report_text=text,content_sha256=checksum(text),bias=extract_bias(text))
            p.write_text(json.dumps(raw));before=p.read_bytes()
            (Path(root)/'reports/index.json').write_text(json.dumps({'reports':[dict(monitor='daily',path='reports/2026/10/25/daily.json',reported_at=NOW)]}))
            self.assertEqual(report_findings(root)[0]['code'],'missing_macro_presented_as_neutral')
            self.assertEqual(p.read_bytes(),before)

    def test_degraded_dashboard_still_publishes_explicit_quality_but_broken_assets_fail(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root);feed=folder/'feed.json';feed.write_text(json.dumps({'measurements':[record()]}))
            with self.assertRaises(ValueError):stage(feed,folder,NOW)
            for name in ('index.html','btc-dashboard.html','btc-status.html','btc-timeframes.html',
                         'btc-signal-history.html','status.mjs','status.css'):
                (folder/name).write_text('<section id="analysis-quality"></section><section id="elliott-scenarios"></section>')
            result=stage(feed,folder,NOW)
            self.assertEqual(result['dashboard_assets'],'checked')
            self.assertTrue((folder/'btc-quality.json').is_file())
            (folder/'index.html').write_text('<section id="analysis-quality"></section>')
            with self.assertRaisesRegex(ValueError,'Elliott visual panel missing'):
                stage(feed,folder,NOW)

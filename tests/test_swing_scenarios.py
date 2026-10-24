from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.test_price_roadmap import fixture
from scripts.swing_scenarios import build_swing_scenarios,validate_frozen,KINDS
from scripts.scenario_archive import freeze
from scripts.market_scenarios import time_ms,iso
from scripts.elliott_rules import impulse_checks,assess_candidates,confirmed_pivots
from scripts.scenario_evaluation import evaluate,build
from scripts.swing_dashboard import render


def directional(feed,mode='swing',close=119,now=None):
    feed=deepcopy(feed);m=feed['measurements'][0]
    if now:
        delta=time_ms(now)-time_ms(m['finished_at'])
        m['started_at']=m['finished_at']=now
        m['metrics']['futures_price']['data']['ts']=str(time_ms(now))
        for metric in m['metrics']['multi_timeframe']['data'].values():
            metric['observed_at']=now
            # fixtures used here advance by whole weeks only for weekly sources.
            tf=metric['data']['interval'];period={'4h':14400000,'1d':86400000,'1w':604800000}[tf]
            shift=delta//period*period
            for row in metric['data']['candles']:row['open_time_ms']+=shift
    tf='1d' if mode=='swing' else '1w'
    rows=m['metrics']['multi_timeframe']['data'][tf]['data']['candles']
    for row in rows:row.update(open=100,high=110,low=90,close=100,base_volume_btc=10)
    rows[-1].update(high=max(110,close+1),low=min(90,close-1),close=close,base_volume_btc=20)
    m['metrics']['futures_price']['data']['lastPr']=str(close)
    return feed


def frozen_record(feed):
    r=deepcopy(feed['measurements'][0]);r['scenario_snapshot']=freeze(r);return r


class ScenarioTests(unittest.TestCase):
    def test_four_routes_and_independent_daily_weekly_data(self):
        feed,now=fixture()
        del feed['measurements'][0]['metrics']['candles_4h']
        r=build_swing_scenarios(feed,now)
        for mode,tf in (('swing','1d'),('position','1w')):
            x=r['horizons'][mode]
            self.assertEqual(x['status'],'ready');self.assertEqual(x['timeframe'],tf)
            self.assertEqual(tuple(s['id'] for s in x['scenarios']),KINDS)
            self.assertTrue(validate_frozen(x))
            self.assertIsNone(x['psychology']['current_phase'])
            self.assertIsNone(x['elliott']['current_wave'])
            self.assertIsNone(x['probability'])

    def test_range_atr_no_lookahead_and_strong_labels_need_volume(self):
        feed,now=fixture();feed=directional(feed)
        r=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertEqual((r['support'],r['resistance'],r['atr14']),(90,110,20))
        self.assertEqual(r['preferred_scenario'],'very_bullish')
        self.assertEqual(r['scenarios'][3]['trigger_price'],112)
        self.assertEqual([t['price'] for t in r['scenarios'][3]['targets']],[132,152])
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1d']['data']['candles'][-1]['base_volume_btc']=10
        self.assertEqual(build_swing_scenarios(feed,now)['horizons']['swing']['preferred_scenario'],'bullish')
        feed=directional(feed,close=60)
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1d']['data']['candles'][-1]['base_volume_btc']=10
        self.assertEqual(build_swing_scenarios(feed,now)['horizons']['swing']['preferred_scenario'],'bearish')
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1d']['data']['candles'][-1]['base_volume_btc']=20
        self.assertEqual(build_swing_scenarios(feed,now)['horizons']['swing']['preferred_scenario'],'very_bearish')

    def test_strict_quality_inputs_and_no_old_fallback(self):
        feed,now=fixture()
        for change in ('duplicate','gap','missinglast','boolean','nonfinite','future','wrongtf'):
            f=deepcopy(feed);f['measurements'].append(deepcopy(f['measurements'][0]))
            m=f['measurements'][0];metric=m['metrics']['multi_timeframe']['data']['1d'];rows=metric['data']['candles']
            if change=='duplicate':rows.append(deepcopy(rows[-1]))
            if change=='gap':rows.pop(-3)
            if change=='missinglast':rows.pop()
            if change=='boolean':rows[-1]['close']=True
            if change=='nonfinite':rows[-1]['close']=float('nan')
            if change=='future':metric['observed_at']=iso(time_ms(now)+7200000)
            if change=='wrongtf':metric['data']['interval']='4h'
            self.assertEqual(build_swing_scenarios(f,now)['horizons']['swing']['status'],'unavailable',change)
        self.assertEqual(build_swing_scenarios(feed,iso(time_ms(now)+3600000))['horizons']['swing']['status'],'unavailable')

    def test_frozen_integrity_and_originals_not_replaced(self):
        feed,now=fixture();m=feed['measurements'][0]
        original=freeze(m)
        changed=deepcopy(original['horizons']['swing']);changed['support']-=1
        with self.assertRaisesRegex(ValueError,'mismatch'):validate_frozen(changed)
        self.assertEqual(original,freeze(m))
        self.assertNotIn('model_trades',m)

    def test_level_reaction_and_current_disagreement(self):
        feed,now=fixture();feed=directional(feed)
        feed['measurements'][0]['metrics']['multi_timeframe']['data'].pop('4h')
        r=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertEqual(r['level_assessment']['reaction'],'closed_above')
        self.assertEqual(r['level_assessment']['vote'],1)
        self.assertEqual(r['level_assessment']['selected']['price'],110)
        feed['measurements'][0]['metrics']['futures_price']['data']['lastPr']='105'
        r=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertTrue(r['level_assessment']['current_disagrees'])
        self.assertEqual(r['level_assessment']['vote'],0)
        self.assertTrue(r['level_assessment']['next_higher'])

    def test_render_all_routes_and_rule_limitations(self):
        feed,now=fixture();page=render(build_swing_scenarios(feed,now))
        self.assertEqual(page.count('class="scenario route-'),8)
        for text in ('Sterk bearish','Bearish','Bullish','Sterk bullish','geen automatisch bevestigde','Alle Fib-'):
            if text=='geen automatisch bevestigde':self.assertIn(text.lower(),page.lower())
            else:self.assertIn(text,page)
        self.assertIn('geen persoonlijke posities',page)

    def test_direct_nas_import(self):
        proc=subprocess.run([sys.executable,'-c','import sys;sys.path.insert(0,"scripts");from scenario_archive import freeze;print(freeze({"finished_at":"2026-10-24T08:00:00Z"})["schema_version"])'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(proc.stdout.strip(),'1')


class ElliottTests(unittest.TestCase):
    def points(self,prices):
        return [dict(price=p,open_time_ms=i*1000) for i,p in enumerate(prices)]

    def test_rules_and_no_full_validation_from_six_points(self):
        checks=impulse_checks(self.points([100,120,110,150,130,160]),'up')
        self.assertFalse(any(x['result']=='geschonden' for x in checks))
        self.assertEqual(checks[-1]['result'],'niet toetsbaar')
        cases=[([100,120,99,150,130,160],'golf_2_begin_1'),
               ([100,120,110,115,113,140],'golf_3_voorbij_1'),
               ([100,130,120,140,135,180],'golf_3_niet_kortste'),
               ([100,120,110,150,119,160],'golf_4_geen_overlap_1')]
        for prices,rule in cases:
            checks=impulse_checks(self.points(prices),'up')
            self.assertEqual(next(x for x in checks if x['rule']==rule)['result'],'geschonden')
        down=impulse_checks(self.points([200,180,190,150,170,140]),'down')
        self.assertFalse(any(x['result']=='geschonden' for x in down))

    def test_truncation_not_automatically_forbidden_and_bad_points_rejected(self):
        checks=impulse_checks(self.points([100,120,110,150,130,145]),'up')
        self.assertFalse(any(x['result']=='geschonden' for x in checks))
        with self.assertRaises(ValueError):impulse_checks(self.points([100,120,-1,150,130,145]),'up')

    def test_no_forced_count_from_flat_or_outside_candles(self):
        feed,now=fixture();feed=directional(feed)
        rows=feed['measurements'][0]['metrics']['multi_timeframe']['data']['1d']['data']['candles']
        self.assertEqual(assess_candidates(rows,'1d')['status'],'insufficient_data')
        self.assertEqual(confirmed_pivots(rows),[])


class EvaluationTests(unittest.TestCase):
    def series(self,days=7):
        feed,now=fixture();feed=directional(feed)
        records=[(frozen_record(feed),'2026/10/24/start.json')]
        for i in range(1,days+1):
            at=iso(time_ms(now)+i*86400000)
            next_feed=directional(feed,close=140,now=at)
            records.append((frozen_record(next_feed),f'future-{i}.json'))
        return records,records[-1][0]['finished_at']

    def test_all_four_original_routes_and_no_reconstruction(self):
        feed,now=fixture()
        self.assertEqual(evaluate([(feed['measurements'][0],'old.json')],now,7),[])
        records,end=self.series()
        result=evaluate(records,end,7)
        first=[x for x in result if x.get('source_path')=='2026/10/24/start.json' and x['mode']=='swing']
        self.assertEqual(len(first),4)
        bull=next(x for x in first if x['route']=='very_bullish')
        self.assertEqual(bull['status'],'target_reached')
        self.assertEqual(bull['missing_closes'],0)
        self.assertEqual(bull['target_events'][0]['price'],132)
        self.assertEqual(next(x for x in first if x['route']=='very_bearish')['status'],'not_activated')

    def test_pending_gaps_tamper_and_repeat_sampling(self):
        records,end=self.series()
        start=records[0][0]['finished_at']
        result=evaluate(records,start,7)
        self.assertTrue(all(x['status']=='pending' for x in result))
        gap=records[:2]+records[3:]
        first=[x for x in evaluate(gap,end,7) if x.get('source_path')=='2026/10/24/start.json' and x['mode']=='swing']
        self.assertTrue(all(x['status']=='incomplete_path' for x in first))
        same=deepcopy(records[0]);same[0]['finished_at']=iso(time_ms(start)+1800000)
        # A mere repeated source snapshot must not inflate the scenario sample.
        same[0]['started_at']=same[0]['finished_at']
        same[0]['metrics']['multi_timeframe']['data']['1d']['observed_at']=same[0]['finished_at']
        same[0]['metrics']['multi_timeframe']['data']['1w']['observed_at']=same[0]['finished_at']
        same[0]['scenario_snapshot']=freeze(same[0])
        repeated=evaluate([records[0],same],same[0]['finished_at'],7)
        self.assertEqual(len(repeated),8)
        bad=deepcopy(records[0]);bad[0]['scenario_snapshot']['horizons']['swing']['scenarios'][0]['trigger_price']=1
        only=evaluate([bad],start,7)
        self.assertTrue(all(x['mode']=='position' for x in only))

    def test_empty_build_explicitly_no_trade_tracking(self):
        with tempfile.TemporaryDirectory() as root:
            build(root,root,'2026-10-24T08:00:00Z')
            result=json.loads((Path(root)/'btc-action-history.json').read_text())
            self.assertEqual(result['scenario_results'],[])
            page=(Path(root)/'btc-action-history.html').read_text()
            self.assertIn('Geen tradeadvies',page)
            self.assertNotIn('Model versus vasthouden',page)


class AdditionalQualityTests(unittest.TestCase):
    def test_4h_confirmation_preserves_daily_zone_anchors(self):
        feed,now=fixture();feed=directional(feed)
        r=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertEqual(r['level_assessment']['zone_timeframe'],'1d')
        self.assertEqual(r['level_assessment']['confirmation_timeframe'],'4h')
        self.assertNotEqual(r['candle_closed_at'],r['level_assessment']['confirmation_closed_at'])
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['4h']['status']='error'
        fallback=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertEqual(fallback['status'],'ready')
        self.assertEqual(fallback['level_assessment']['confirmation_timeframe'],'1d')
        self.assertEqual(fallback['fibonacci'],r['fibonacci'])
        self.assertEqual(fallback['support'],r['support'])

    def test_actual_candidates_remain_provisional_and_invalid_overlap_rejected(self):
        def bars(p4):
            knots={0:102,1:101,2:100,7:120,12:110,17:150,22:p4,27:160,31:156}
            points=sorted(knots);rows=[]
            for i in range(32):
                left=max(x for x in points if x<=i);right=min(x for x in points if x>=i)
                value=knots[left] if left==right else knots[left]+(knots[right]-knots[left])*(i-left)/(right-left)
                rows.append(dict(open_time_ms=i*86400000,open=value,close=value,low=value-.1,high=value+.1,base_volume_btc=10))
            return rows
        r=assess_candidates(bars(130),'1d')
        self.assertEqual(r['candidates'][0]['status'],'provisional_price_pattern')
        self.assertEqual(next(c for c in r['candidates'][0]['checks'] if c['rule']=='interne_5_3_5_3_5')['result'],'niet toetsbaar')
        self.assertEqual(assess_candidates(bars(119),'1d')['candidates'][0]['status'],'invalid')
        self.assertIsNone(r['current_wave'])

    def test_already_passed_target_not_awarded_as_future_success(self):
        records,end=EvaluationTests().series()
        original=deepcopy(records[0])
        # Fresh scenario snapshot generated when reference price has already passed target 1.
        feed={'measurements':[original[0]]}
        feed['measurements'][0]['metrics']['futures_price']['data']['lastPr']='140'
        original=(frozen_record(feed),original[1])
        result=evaluate([original,*records[1:]],end,7)
        row=next(x for x in result if x.get('source_path')==original[1] and x['mode']=='swing' and x['route']=='very_bullish')
        self.assertFalse(any(t['index']==0 for t in row['target_events']))


class CollectorIntegrationTests(unittest.TestCase):
    def test_original_routes_reach_snapshot_and_feed_without_trade_fields(self):
        import contextlib,io,os
        from unittest.mock import patch
        from scripts import collect
        feed,at=fixture();m=feed['measurements'][0];now=datetime.fromisoformat(at)
        metrics=m['metrics'];native=metrics['multi_timeframe']['data'];prior=Path.cwd()
        with tempfile.TemporaryDirectory() as root:
            try:
                os.chdir(root)
                def fake_fetch(url,nums,stamps):
                    return metrics['futures_price'] if nums==['lastPr'] else {'status':'ok','data':{}}
                extras={k:v for k,v in metrics.items() if k not in ('futures_price','multi_timeframe')}
                with patch.dict(os.environ,{},clear=True),patch.object(collect,'utcnow',return_value=now),patch.object(collect,'fetch',side_effect=fake_fetch),patch.object(collect,'collect_extra',return_value=extras),patch.object(collect,'collect_cvd',return_value={'status':'missing_data'}),patch('scripts.multi_timeframe_collector.collect_native_timeframes',return_value=native),contextlib.redirect_stdout(io.StringIO()):
                    collect.main()
                latest=json.loads(Path('data/latest.json').read_text())
                frozen=json.loads(next(Path('data').glob('????/??/??/*.json')).read_text())
                self.assertEqual(frozen['scenario_snapshot'],latest['measurements'][0]['scenario_snapshot'])
                self.assertTrue(all(len(x['scenarios'])==4 for x in frozen['scenario_snapshot']['horizons'].values()))
                self.assertNotIn('model_trades',frozen);self.assertNotIn('action_gauge',frozen)
            finally:os.chdir(prior)

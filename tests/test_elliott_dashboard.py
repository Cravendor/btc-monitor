from copy import deepcopy
import unittest
from scripts.elliott_dashboard import build, render, zones
from scripts.elliott_rules import assess_candidates
from scripts.market_scenarios import iso, time_ms
from tests.test_price_roadmap import fixture


def wave_rows(rows):
    anchors = [(0,105),(2,90),(6,120),(10,100),(14,150),
               (18,130),(22,170),(26,140),(30,180),(34,145)]
    result=[]
    period=rows[1]['open_time_ms']-rows[0]['open_time_ms']
    end=rows[-1]['open_time_ms']+period
    for i in range(36):
        a,b=next(((a,b) for a,b in zip(anchors,anchors[1:]) if a[0]<=i<=b[0]),(anchors[-2],anchors[-1]))
        value=a[1]+(b[1]-a[1])*(i-a[0])/(b[0]-a[0])
        result.append(dict(open_time_ms=end-(36-i)*period,open=value,close=value,
                           high=value+1,low=value-1,base_volume_btc=10,quote_volume_usdt=1000))
    return result


class ElliottVisualTests(unittest.TestCase):
    def feed(self):
        f,now=fixture()
        for metric in f['measurements'][0]['metrics']['multi_timeframe']['data'].values():
            metric['data']['candles']=wave_rows(metric['data']['candles'])
        return f,now

    def test_stale_is_historical_and_never_uses_old_ticker_as_current(self):
        feed,now=self.feed(); original=deepcopy(feed)
        r=build(feed,iso(time_ms(now)+7200000))
        self.assertEqual(r['status'],'historical')
        self.assertTrue(all(h.get('price') is None for h in r['horizons']))
        page=render(r)
        self.assertIn('HISTORISCH',page)
        self.assertNotIn('Snapshot 98',page)
        self.assertEqual(feed,original)

    def test_all_degrees_and_both_directions_invalid_visible_not_rescued(self):
        feed,now=self.feed();r=build(feed,now)
        self.assertEqual([h['timeframe'] for h in r['horizons']],['1w','1d','4h','1h'])
        page=render(r)
        self.assertIn('ONGELDIGE standaardimpuls',page)
        self.assertIn('Bull',page);self.assertIn('Bear',page)
        self.assertIsNone(r['current_wave'])
        self.assertEqual(r['nested_count'],'unproven')
        self.assertIn('samenhang tussen graden: nog niet bewezen',page)
        self.assertIn('50% is halvering',page)

    def test_missing_higher_or_lower_source_is_not_filled_from_other_degree(self):
        feed,now=self.feed()
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1w']['status']='error'
        r=build(feed,now)
        self.assertEqual(r['horizons'][0]['status'],'unavailable')
        self.assertEqual(r['horizons'][1]['status'],'available')
        self.assertEqual(r['horizons'][3]['status'],'unavailable')
        for c in r['horizons'][1]['candidates']:
            self.assertEqual(c['parent_legs'],[])

    def test_wrong_market_future_and_empty_rejected(self):
        feed,now=self.feed()
        feed['measurements'][0]['market']='SPOT'
        self.assertEqual(build(feed,now)['status'],'unavailable')
        feed,now=self.feed()
        self.assertEqual(build(feed,iso(time_ms(now)-7200000))['status'],'unavailable')
        self.assertEqual(build({},now)['status'],'unavailable')

    def test_zone_events_are_pivots_not_each_touch_and_no_strength_promise(self):
        feed,now=self.feed()
        rows=feed['measurements'][0]['metrics']['multi_timeframe']['data']['4h']['data']['candles']
        z=zones(rows,'4h')
        self.assertEqual(sum(x['events'] for x in z),8)
        self.assertTrue(all(x['timeframe']=='4h' for x in z))
        self.assertTrue(all(x['low']<x['high'] for x in z))
        page=render(build(feed,now))
        self.assertIn('geen gekalibreerde steunkracht',page)

    def test_gap_in_recent_candles_rejects_only_affected_timeframe(self):
        feed,now=self.feed()
        rows=feed['measurements'][0]['metrics']['multi_timeframe']['data']['4h']['data']['candles']
        rows.pop(-4)
        r=build(feed,now)
        self.assertEqual(r['horizons'][2]['status'],'unavailable')
        self.assertEqual(r['horizons'][1]['status'],'available')

    def test_full_coverage_conflict_blocks_only_affected_degree_and_explains_why(self):
        feed, now = self.feed()
        bundle = build(feed, now)
        week = bundle['horizons'][0]
        week.update(status='unavailable', coverage={
            'status': 'conflict', 'candle_count': 69, 'required_candles': 69,
            'missing_candles': 0, 'first_missing_at': None,
            'cross_timeframe_check': {'child': '1d', 'first_mismatch_at': '2026-10-19T00:00:00Z'}})
        page = render(bundle)
        self.assertNotIn('id="ew-1w-', page)
        self.assertIn('id="ew-1d-', page)
        self.assertIn('BRONCONFLICT', page)
        self.assertIn('2026-10-19T00:00:00Z', page)
        self.assertNotIn('Eerste gat: None', page)

    def linked_history(self, now):
        from scripts.elliott_history import floor_time
        from scripts.native_timeframe_candles import PERIOD_MS
        history={}
        for tf in ('1w','1d','4h','1h'):
            period=PERIOD_MS[tf];end=floor_time(time_ms(now),tf)
            rows=wave_rows([{'open_time_ms':end-2*period},{'open_time_ms':end-period}])
            prefix=[dict(rows[0],open_time_ms=rows[0]['open_time_ms']-(200-i)*period) for i in range(200)]
            rows=prefix+rows
            history[tf]=dict(status='complete',rows=rows,source_at=now,source_path='fixture/'+tf)
        return history

    def test_zoom_does_not_change_candidates_and_preserves_exact_parent_window(self):
        now='2026-10-26T08:30:00Z';history=self.linked_history(now)
        bundle=build({},now,history)
        from scripts.elliott_dashboard import zoom_panel
        from scripts.native_timeframe_candles import PERIOD_MS
        for parent,child in zip(bundle['horizons'],bundle['horizons'][1:]):
            linked=child['parent_window']
            self.assertEqual(linked['start'],parent['focus_start'])
            self.assertEqual(linked['end'],time_ms(parent['closed_at']))
            selected=[r for r in child['rows'] if linked['start']<=r['open_time_ms']<linked['end']]
            self.assertEqual(len(selected)*PERIOD_MS[child['timeframe']],linked['end']-linked['start'])
            before=deepcopy(child['candidates']);page=zoom_panel(child)
            self.assertEqual(child['candidates'],before)
            self.assertIn('ew-zoom-in',page);self.assertIn('ew-zoom-out',page)
            self.assertIn('data-view="0"',page)
            self.assertNotIn('<polyline',page)

    def test_parent_link_not_created_across_a_missing_child_candle(self):
        now='2026-10-26T08:30:00Z';history=self.linked_history(now)
        history['1h']['rows'].pop(-8)
        bundle=build({},now,history)
        self.assertNotIn('parent_window',bundle['horizons'][-1])

    def test_conflicting_parent_never_generates_linked_child_chart(self):
        now='2026-10-26T08:30:00Z';history=self.linked_history(now)
        history['1w']['status']='conflict'
        bundle=build({},now,history)
        self.assertNotIn('parent_window',bundle['horizons'][1])
        self.assertIn('parent_window',bundle['horizons'][2])

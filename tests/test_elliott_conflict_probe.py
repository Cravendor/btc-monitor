from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from urllib.parse import parse_qs,urlparse
from unittest.mock import patch
from scripts import elliott_conflict_probe as probe,elliott_history as history,cycle_history
from scripts.market_scenarios import iso

NOW=iso(probe.END+3600000)
FIELDS=probe.FIELDS


def fixture(root):
    values={}
    hour=history.PERIOD_MS['1h']
    for n in range(4):
        t=probe.START+n*hour
        values[t]=dict(open_time_ms=t,open=100.,high=110.,low=90.,close=105.,base_volume_btc=10.,quote_volume_usdt=1000.)
    parent={probe.START:dict(open_time_ms=probe.START,open=100.,high=110.,low=90.,close=105.,base_volume_btc=40.,quote_volume_usdt=4000.)}
    for tf,rows in [('1h',values),('4h',parent)]:
        path=history.filename(Path(root)/history.DIRECTORY,tf)
        cycle_history.save(path,history.report(rows,[],tf,NOW,'fixture'))
    return {'1h':values,'4h':parent}


def provider(rows,calls,change=None,omit=False,fail=False,observed=NOW):
    def get(url,transform,bitget):
        q={k:v[0] for k,v in parse_qs(urlparse(url).query).items()};calls.append(url)
        tf={'1H':'1h','4H':'4h'}[q['granularity']]
        raw=[[str(t)]+[str(c[k]) for k in FIELDS] for t,c in sorted(rows[tf].items())]
        if change and tf==change[0]:raw[-1][FIELDS.index(change[1])+1]=str(change[2])
        if omit:raw.pop()
        try:data=transform(raw)
        except (ValueError,TypeError,KeyError,IndexError):return dict(status='error',observed_at=observed)
        return dict(status='error' if fail else 'ok',data=data,observed_at=observed,secret='never retain')
    return get


class ConflictProbeTests(unittest.TestCase):
    def test_exact_recheck_comparison_and_original_cache_remains_unchanged(self):
        with TemporaryDirectory() as root:
            rows=fixture(root);paths=list(Path(root).rglob('*.json'));before=[p.read_bytes() for p in paths];calls=[]
            out=probe.build(root,NOW,provider(rows,calls))
            self.assertEqual(out['status'],'checked');self.assertTrue(out['comparison']['price_and_base_match'])
            self.assertFalse(out['comparison']['differences']);self.assertEqual(len(calls),2)
            self.assertEqual([p.read_bytes() for p in paths],before)
            self.assertNotIn('secret',json.dumps(out));self.assertEqual(out['activation'],'none')
            self.assertEqual([len(x['source_rows']) for x in out['sources']],[1,4])

    def test_fresh_change_and_exact_conflict_are_both_visible(self):
        with TemporaryDirectory() as root:
            rows=fixture(root);out=probe.build(root,NOW,provider(rows,[],('4h','close',106)))
            self.assertEqual(out['status'],'checked');self.assertFalse(out['comparison']['price_and_base_match'])
            self.assertEqual(out['comparison']['differences']['close']['native_minus_aggregate'],'1.0')
            self.assertEqual(out['comparison']['cache_changes'][0]['fields']['close']['fresh'],'106')

    def test_quote_difference_alone_is_diagnostic(self):
        with TemporaryDirectory() as root:
            rows=fixture(root);out=probe.build(root,NOW,provider(rows,[],('4h','quote_volume_usdt',4001)))
            self.assertTrue(out['comparison']['price_and_base_match'])
            self.assertIn('quote_volume_usdt',out['comparison']['differences'])

    def test_missing_invalid_stale_sources_or_missing_cache_are_never_success(self):
        for kwargs in (dict(omit=True),dict(fail=True),dict(observed='2026-10-26T00:00:00Z')):
            with self.subTest(kwargs=kwargs),TemporaryDirectory() as root:
                rows=fixture(root);out=probe.build(root,NOW,provider(rows,[],**kwargs))
                self.assertEqual(out['status'],'incomplete');self.assertIsNone(out['comparison'])
        with TemporaryDirectory() as root:
            rows=fixture(root);history.filename(Path(root)/history.DIRECTORY,'1h').unlink()
            self.assertEqual(probe.build(root,NOW,provider(rows,[]))['status'],'incomplete')

    def test_immutable_result_once_then_no_more_network_calls(self):
        with TemporaryDirectory() as root:
            rows=fixture(root);record=probe.build(root,NOW,provider(rows,[]));p=probe.save(root,record)
            self.assertEqual(probe.save(root,record),p);self.assertEqual(probe.existing_completed(root),p)
            calls=[];out=probe.run(root,provider(rows,calls))
            self.assertEqual(out['status'],'already_checked');self.assertEqual(calls,[])
            p.write_text('{}')
            with self.assertRaises(ValueError):probe.existing_completed(root)

    def test_no_request_before_exact_closed_window_and_disagreeing_payload(self):
        with TemporaryDirectory() as root:
            rows=fixture(root);calls=[]
            self.assertEqual(probe.build(root,iso(probe.END-1),provider(rows,calls))['reason'],'window_not_yet_closed')
            self.assertEqual(calls,[])
            source=provider(rows,[])
            def invalid(url,transform,bitget):
                r=source(url,transform,bitget);r['data']['rows'][max(r['data']['rows'])]['close']=106
                return r
            self.assertEqual(probe.build(root,NOW,invalid)['status'],'incomplete')

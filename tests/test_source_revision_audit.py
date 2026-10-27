from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs,urlparse
from unittest.mock import patch
from scripts import source_revision_audit as audit,elliott_history as eh,cycle_history as ch
from scripts.market_scenarios import iso,time_ms

NOW='2026-10-27T07:30:00Z'
FIELDS=ch.FIELDS


def fixture(root, old=False):
    allrows={}
    for tf in audit.TIMEFRAMES:
        boundary=eh.floor_time(time_ms(NOW),tf);period=eh.PERIOD_MS[tf]
        end=boundary-period if old else boundary
        rows={t:dict(open_time_ms=t,open=100.,high=110.,low=90.,close=105.,base_volume_btc=10.,quote_volume_usdt=1000.) for t in range(end-3*period,end,period)}
        allrows[tf]=rows
        path=Path(root)/ch.PATH if tf=='1d' else eh.filename(Path(root)/eh.DIRECTORY,tf)
        data=ch.report(rows,[],min(rows),end,NOW,'test') if tf=='1d' else eh.report(rows,[],tf,NOW,'test')
        ch.save(path,data)
    return allrows


def provider(rows,calls,change=None,omit=False,bad=False,failed=False,observed=NOW):
    def get(url,transform,bitget):
        q={k:v[0] for k,v in parse_qs(urlparse(url).query).items()};calls.append(url)
        tf=next(t for t in audit.TIMEFRAMES if eh.GRANULARITIES[t]==q['granularity'])
        lower=int(q['startTime']);end=int(q['endTime'])
        selected=sorted(rows[tf])
        raw=[[str(t)]+[str(rows[tf][t][k]) for k in FIELDS] for t in selected if lower<=t<end]
        if change and tf==change[0]:
            raw[-1][FIELDS.index(change[1])+1]=str(change[2])
        if omit:raw.pop(-1)
        if bad:raw[-1][2]='1'  # high below open/close
        try:
            data=transform(raw)
        except (ValueError,TypeError,KeyError):
            return dict(status='error',observed_at=observed,error='private requester detail',data=None)
        return dict(status='error' if failed else 'ok',data=data,observed_at=observed,
                    private_debug='must not be retained')
    return get


def bytes_before(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in Path(root).rglob('*.json')}


class RevisionAuditTests(unittest.TestCase):
    def test_four_bounded_closed_tail_requests_preserve_caches_and_unknown_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);original=bytes_before(root);calls=[]
            r=audit.build(root,NOW,requester=provider(rows,calls))
            self.assertEqual(r['status'],'unchanged_checked_windows')
            self.assertEqual(len(calls),4);self.assertEqual(r['activation'],'none')
            self.assertTrue(all(c['cache_tail_current'] for c in r['checks']))
            self.assertEqual(bytes_before(root),original)
            body=json.dumps(r)
            self.assertNotIn(root,body);self.assertNotIn('private',body)
            for c,url in zip(r['checks'],calls):
                self.assertEqual(len(c['cached_rows']),2)
                self.assertEqual(len(c['current_rows']),2)
                self.assertEqual(audit.digest(c['source_rows']),c['source_rows_sha256'])
                q=parse_qs(urlparse(url).query);self.assertEqual(q['limit'],['10'])
                self.assertEqual(urlparse(url).hostname,'api.bitget.com')
                self.assertEqual(c['end'],c['required_through'])

    def test_revision_including_quote_only_is_recorded_with_both_values_not_activated(self):
        for field,value in [('close',106),('base_volume_btc',11),('quote_volume_usdt',1001)]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as root:
                rows=fixture(root);before=bytes_before(root)
                r=audit.build(root,NOW,requester=provider(rows,[],('1w',field,value)))
                self.assertEqual(r['status'],'revision_detected')
                entry=r['checks'][0]
                self.assertEqual(entry['changes'][0]['fields'][field],dict(cached=rows['1w'][max(rows['1w'])][field],current=float(value)))
                self.assertEqual(len(entry['changes']),1)
                self.assertEqual(bytes_before(root),before)
                self.assertTrue(all(c['status']=='unchanged_checked_window' for c in r['checks'][1:]))

    def test_historical_tail_is_not_advertised_as_current_or_complete_history(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root,old=True)
            r=audit.build(root,NOW,requester=provider(rows,[]))
            self.assertEqual(r['status'],'unchanged_checked_windows')
            self.assertTrue(all(not c['cache_tail_current'] for c in r['checks']))
            self.assertTrue(all(c['end']<c['required_through'] for c in r['checks']))

    def test_missing_malformed_failed_or_bad_observation_is_unavailable_not_unchanged(self):
        for kwargs in [dict(omit=True),dict(bad=True),dict(failed=True),dict(observed='2026-10-26T07:30:00Z'),dict(observed='2027-10-27T07:30:00Z')]:
            with self.subTest(kwargs=kwargs),tempfile.TemporaryDirectory() as root:
                rows=fixture(root);before=bytes_before(root)
                r=audit.build(root,NOW,requester=provider(rows,[],**kwargs))
                self.assertEqual(r['status'],'incomplete_audit')
                self.assertTrue(all(c['status']=='unavailable' and c['changes']==[] for c in r['checks']))
                self.assertEqual(bytes_before(root),before)
                self.assertNotIn('private',json.dumps(r))

    def test_missing_wrong_identity_checksum_and_tail_gap_skip_their_requests(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);folder=Path(root)/eh.DIRECTORY
            (folder/'bitget_btcusdt_1w.json').unlink()
            path=Path(root)/ch.PATH;d=json.loads(path.read_text());d['symbol']='OTHER';path.write_text(json.dumps(d))
            path=folder/'bitget_btcusdt_4h.json';d=json.loads(path.read_text());d['candles'][-1]['close']=106;path.write_text(json.dumps(d))
            tf='1h';r=rows[tf];del r[sorted(r)[-2]]
            ch.save(folder/'bitget_btcusdt_1h.json',eh.report(r,[],tf,NOW,'test'))
            calls=[];r=audit.build(root,NOW,requester=provider(rows,calls))
            self.assertEqual(calls,[]);self.assertEqual(r['status'],'incomplete_audit')
            self.assertTrue(all(c['reason']=='cache_unavailable' for c in r['checks']))

    def test_time_budget_never_turns_a_skipped_check_into_success(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);calls=[];times=iter([0,1,20,20,20])
            r=audit.build(root,NOW,seconds=16,requester=provider(rows,calls),clock=lambda:next(times))
            self.assertEqual(len(calls),1)
            self.assertEqual([c['reason'] for c in r['checks'][1:]],['time_budget']*3)
            self.assertEqual(r['status'],'incomplete_audit')
        for budget in [0,15,91,True]:
            with self.assertRaises(ValueError):audit.build('.',NOW,seconds=budget)

    def test_open_upper_edge_excluded_and_unexpected_rows_or_conflicting_duplicates_rejected(self):
        tf='1h';p=3600000;end=eh.floor_time(time_ms(NOW),tf);start=end-2*p
        row=[str(start),'100','110','90','105','10','1000'];nextrow=[str(start+p)]+row[1:];openrow=[str(end),'invalid']
        r=audit.source_rows([row,nextrow,[str(end)]+row[1:]],tf,start,end)
        self.assertNotIn(end,r['rows']);self.assertEqual(len(r['source_rows']),2)
        for bad in [[row,nextrow,list(row)], [row,nextrow,[str(start-2*p)]+row[1:]], [row,nextrow,[row[0],'100','111','90','105','10','1000']], [row], [row,nextrow,openrow]]:
            with self.assertRaises((ValueError,KeyError,IndexError)):audit.source_rows(bad,tf,start,end)

    def test_raw_values_are_retained_and_injected_normalized_disagreement_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);base=provider(rows,[])
            def disagree(url,transform,bitget):
                r=base(url,transform,bitget);r['data']['rows'][max(r['data']['rows'])]['close']=106;return r
            r=audit.build(root,NOW,requester=disagree)
            self.assertEqual(r['status'],'incomplete_audit')
            self.assertTrue(all('source_rows' not in c for c in r['checks']))
            r=audit.build(root,NOW,requester=base)
            self.assertTrue(all(isinstance(c['source_rows'][0][1],str) for c in r['checks']))

    def test_content_addressed_evidence_is_idempotent_and_never_overwrites_a_collision(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);r=audit.build(root,NOW,requester=provider(rows,[]))
            path=audit.save_audit(root,r);before=path.read_bytes()
            self.assertEqual(audit.save_audit(root,r),path);self.assertEqual(path.read_bytes(),before)
            revised=deepcopy(r);revised['status']='revision_detected'
            self.assertNotEqual(audit.save_audit(root,revised),path)
            path.write_text('different original')
            with self.assertRaisesRegex(ValueError,'collision'):audit.save_audit(root,r)
            self.assertEqual(path.read_text(),'different original')

    def test_cache_change_during_validation_is_not_bound_to_wrong_original_hash(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);real=eh.load
            def changing(path,tf,boundary):
                r=real(path,tf,boundary);path.write_text(path.read_text()+' ');return r
            calls=[]
            with patch.object(eh,'load',changing):
                r=audit.build(root,NOW,requester=provider(rows,calls))
            self.assertEqual(len(calls),1) # only separately loaded daily scale
            self.assertEqual(r['status'],'incomplete_audit')

    def test_failed_atomic_publish_leaves_no_partial_audit_or_staging_file(self):
        with tempfile.TemporaryDirectory() as root:
            rows=fixture(root);r=audit.build(root,NOW,requester=provider(rows,[]))
            with patch.object(audit.os,'link',side_effect=OSError('fixture publication failure')):
                with self.assertRaises(OSError):audit.save_audit(root,r)
            self.assertEqual(list((Path(root)/audit.DIRECTORY).iterdir()),[])
            self.assertEqual(list((Path(root)/'data/history').glob('*.tmp')),[])

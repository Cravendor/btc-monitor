import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import collect


class CvdSnapshotTests(unittest.TestCase):
    def run_snapshot(self, path):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ, {'BTC_CVD_DB': str(path)}, clear=True), \
                        patch.object(collect, 'fetch', return_value={'status': 'ok', 'data': {}}), \
                        patch.object(collect, 'collect_extra', return_value={}), \
                        patch('scripts.multi_timeframe_collector.collect_native_timeframes', return_value={}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    collect.main()
                feed = json.loads(Path('data/latest.json').read_text())
                dated = json.loads(next(Path('data').glob('????/??/??/*.json')).read_text())
                return feed, dated
            finally:
                os.chdir(old)

    def test_optional_journal_failure_preserves_market_snapshot_and_explicit_missing(self):
        feed, dated = self.run_snapshot('/nonexistent/private-trades.sqlite3')
        self.assertEqual(dated['status'], 'ok')
        self.assertEqual(dated['cvd_4h']['status'], 'missing_data')
        self.assertIsNone(dated['cvd_4h']['value'])
        self.assertEqual(feed['measurements'][0]['cvd_4h'], dated['cvd_4h'])
        self.assertNotIn('/nonexistent', json.dumps(feed))

    def test_closed_interval_observations_reach_dated_file_and_latest_feed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'trades.sqlite3'
            now = collect.utcnow()
            end = int(now.timestamp()*1000)//14400000*14400000
            with sqlite3.connect(str(path)) as db:
                db.executescript('''
                  CREATE TABLE trades(market,trade_id,ts_ms,received_ms,price,size_btc,taker_side);
                  CREATE TABLE gaps(market,start_ms,end_ms,reason,resolved);
                ''')
                db.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?)',
                           ('spot','1',end-1000,end-999,'100','0.125','buy'))
            feed, dated = self.run_snapshot(path)
        cvd = dated['cvd_4h']
        self.assertEqual(cvd, feed['measurements'][0]['cvd_4h'])
        self.assertEqual(cvd['status'], 'partial')
        self.assertEqual(cvd['markets']['spot']['observed_delta_btc'], '0.125')
        self.assertIsNone(cvd['value'])
        self.assertFalse(cvd['coverage_verified'])


class CvdDashboardTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required for dashboard DOM checks')
    def test_missing_partial_zero_invalid_and_old_feed_render_safely(self):
        html = (Path(__file__).resolve().parents[1]/'index.html').read_text()
        script = html.split('<script>', 1)[1].split('</script>', 1)[0]
        render = script.split('function renderCvd', 1)[1].split("fetch('https://", 1)[0]
        harness = '''
          const assert=require('node:assert/strict');
          class Element {
            constructor(){this.children=[];this.textContent='';}
            append(...items){this.children.push(...items);}
            replaceChildren(){this.children=[];}
          }
          const root=new Element();
          const document={querySelector:()=>root,createElement:()=>new Element()};
          const fmt=(x,n=2)=>Number(x).toLocaleString('nl-NL',{maximumFractionDigits:n});
          function texts(el){return [el.textContent,...el.children.flatMap(texts)];}
        ''' + 'function renderCvd' + render + '''
          renderCvd(undefined);
          assert.equal(root.children.length,2);
          assert(texts(root).includes('Ontbreekt'));
          for(const [value,status,expected] of [
            [null,'partial','Ontbreekt'],['0','partial','0 BTC'],
            ['0.125','partial','0,125 BTC'],['3','invalid_data','Ontbreekt']]){
              renderCvd({markets:{spot:{status,coverage_verified:false,observed_delta_btc:value}}});
              assert.equal(root.children[0].children[1].textContent,expected);
          }
          renderCvd({markets:{spot:{status:'partial',coverage_verified:false,
            observed_delta_btc:'1',journal_trade_status:'stale'}}});
          assert(texts(root).some(t=>t.includes('VEROUDERD')));
          assert(texts(root).some(t=>t.includes('geen gevalideerde CVD')));
        '''
        result = subprocess.run(['node', '-e', harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        compile_result = subprocess.run(['node', '-e', 'new Function(' + json.dumps(script) + ')'],
                                        capture_output=True, text=True)
        self.assertEqual(compile_result.returncode, 0, compile_result.stderr)

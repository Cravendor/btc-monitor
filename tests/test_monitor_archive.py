from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess

from scripts.archive_report import validate
from scripts.monitor_archive import checksum, extract_bias, import_inbox, validate_submission

TEXT = '''BTC-marktmonitor — voorbeeld voor tests
4H–1D: −1 ZWAK BEARISH — steun onder druk.
7D: 0 NEUTRAAL/GEMENGD — tegengesteld bewijs.
30D/macro: ONVOLDOENDE DATA — geen volledige bronreeks.
'''


def payload(text=TEXT):
    return {'schema_version': 2, 'source': 'chatgpt_monitor', 'monitor': 'daily',
            'reported_at': '2026-01-01T12:00:00+00:00', 'report_text': text}


class MonitorArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inbox = self.root/'reports/inbox/daily/20260101T120000Z.json'
        self.inbox.parent.mkdir(parents=True)

    def write(self, obj):
        self.inbox.write_text(json.dumps(obj), encoding='utf-8')

    def test_original_full_text_and_explicit_scores_survive_idempotent_import(self):
        self.write(payload())
        r = import_inbox(self.root)
        self.assertEqual(r, {'imported': 1, 'indexed': 1, 'rejected': 0})
        target = self.root/'reports/2026/01/01/daily-120000.json'
        first = target.read_bytes()
        report = json.loads(first)
        self.assertEqual(report['report_text'], TEXT)
        self.assertEqual(report['content_sha256'], checksum(TEXT))
        self.assertEqual(report['bias']['4h_1d']['score'], -1)
        self.assertEqual(report['bias']['7d']['score'], 0)
        self.assertEqual(report['bias']['30d_macro']['status'], 'ONVOLDOENDE DATA')
        self.assertEqual(import_inbox(self.root)['imported'], 0)
        self.assertEqual(target.read_bytes(), first)
        validate(report)

    def test_new_report_with_missing_macro_claimed_neutral_is_rejected(self):
        self.write(payload('Richting: macro Neutraal/gemengd wegens ONVOLDOENDE DATA.'))
        r=import_inbox(self.root)
        self.assertEqual(r['imported'],0)
        self.assertEqual(r['rejected'],1)
        self.assertTrue(self.inbox.exists())
        self.write(payload())
        self.assertEqual(import_inbox(self.root)['imported'],1)

    def test_psychological_report_is_a_distinct_supported_category(self):
        obj = payload()
        obj['monitor'] = 'psychology'
        path = self.root/'reports/inbox/psychology/20260101T120000Z.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(obj))
        self.assertEqual(import_inbox(self.root)['indexed'], 1)
        entry = json.loads((self.root/'reports/index.json').read_text())['reports'][0]
        self.assertEqual(entry['monitor'], 'psychology')
        self.assertEqual(entry['path'], 'reports/2026/01/01/psychology-120000.json')

    def test_missing_score_is_not_inferred_from_direction_or_low_confidence(self):
        bias = extract_bias('4H–1D: Neutraal/gemengd.\n7D: bearish.\nMacro-cyclus: ONVOLDOENDE DATA.')
        for v in bias.values():
            self.assertIsNone(v['score'])
            self.assertEqual(v['status'], 'NOT_REPORTED')

    def test_table_markdown_and_plus_scores_are_parsed_without_sign_loss(self):
        bias = extract_bias('| **4H–1D** | **+2 STERK BULLISH** | uitleg |\n- **7D: +1 ZWAK BULLISH** — reden\n30D/macro: -2 STERK BEARISH')
        self.assertEqual([bias[h]['score'] for h in ('4h_1d','7d','30d_macro')], [2,1,-2])

    def test_conflicting_or_mismatched_labels_never_create_a_score(self):
        for text in ('4H–1D: -1 STERK BULLISH',
                     '4H–1D: -1 ZWAK BEARISH\n4H–1D: +1 ZWAK BULLISH',
                     '4H–1D: ONVOLDOENDE DATA\n4H–1D: 0 NEUTRAAL'):
            b = extract_bias(text)['4h_1d']
            self.assertIsNone(b['score'])
            self.assertEqual(b['status'], 'NOT_REPORTED')

    def test_conflicting_submission_does_not_overwrite_history_or_block_other_reports(self):
        self.write(payload())
        import_inbox(self.root)
        original = (self.root/'reports/2026/01/01/daily-120000.json').read_bytes()
        self.write(payload(TEXT+'Changed original'))
        r = import_inbox(self.root)
        self.assertEqual(r['rejected'], 1)
        self.assertEqual(r['indexed'], 1)
        self.assertEqual((self.root/'reports/2026/01/01/daily-120000.json').read_bytes(), original)

    def test_bad_identity_schema_future_or_oversized_text_are_rejected(self):
        for change in ({'monitor': '../outside'}, {'reported_at': '2099-01-01T12:00:00Z'},
                       {'source': 'technical_model'}, {'report_text': 'x'*60001},
                       {'report_text': ''}, {'reported_at': '2026-01-01T12:00:00'},
                       {'bias': {'4h_1d': 2}}):
            with self.subTest(change=list(change)):
                obj = dict(payload(), **change)
                with self.assertRaises(ValueError): validate_submission(obj)
        self.write(dict(payload(), reported_at='2026-01-01T13:00:00Z'))
        r = import_inbox(self.root)
        self.assertEqual(r['indexed'], 0)
        self.assertEqual(r['rejected'], 1)

    def test_tampered_stored_text_or_scores_are_excluded_from_index(self):
        self.write(payload());import_inbox(self.root)
        target = self.root/'reports/2026/01/01/daily-120000.json'
        report = json.loads(target.read_text())
        report['bias']['4h_1d']['score'] = 2
        target.write_text(json.dumps(report))
        r = import_inbox(self.root)
        self.assertEqual(r['indexed'], 0)
        self.assertEqual(json.loads((self.root/'reports/index.json').read_text())['reports'], [])

    def test_report_text_is_data_and_never_executed(self):
        marker = self.root/'executed'
        text = '<script>alert(1)</script>\n$(touch '+str(marker)+')\n'+TEXT
        self.write(payload(text))
        import_inbox(self.root)
        self.assertFalse(marker.exists())
        self.assertEqual(json.loads((self.root/'reports/2026/01/01/daily-120000.json').read_text())['report_text'], text)

    def test_legacy_manual_reports_are_preserved_in_rebuilt_index(self):
        legacy = {'schema_version': 1, 'monitor': 'market-risk', 'reported_at': '2026-01-01T09:00:00Z',
                  'bias': {h: {'score': None, 'status': 'ONVOLDOENDE DATA', 'reason': 'Test'}
                           for h in ('4h_1d','7d','30d_macro')}, 'sources': ['https://example.com/']}
        target = self.root/'reports/2026/01/01/market-risk-090000.json'
        target.parent.mkdir(parents=True);target.write_text(json.dumps(legacy))
        self.assertEqual(import_inbox(self.root)['indexed'], 1)
        entry = json.loads((self.root/'reports/index.json').read_text())['reports'][0]
        self.assertFalse(entry['has_report_text'])

    def test_pages_republishes_after_token_created_archive_commits(self):
        root = Path(__file__).resolve().parents[1]
        pages = (root/'.github/workflows/pages.yml').read_text()
        self.assertIn('- Archive BTC bias report', pages)
        self.assertIn('- reports/index.json', pages)
        workflow = (root/'.github/workflows/archive-bias.yml').read_text()
        self.assertIn("'reports/inbox/**'", workflow)
        self.assertIn('python3 -m scripts.monitor_archive', workflow)
        self.assertNotIn('${{ inputs.report_json }}', workflow.split('run: python3')[1])

    @unittest.skipUnless(shutil.which('node'), 'Node required for DOM harness')
    def test_archive_reader_distinguishes_missing_scores_and_never_executes_report_markup(self):
        code = r'''
const fs=require('fs'),vm=require('vm'),{webcrypto,createHash}=require('crypto');
class Element{constructor(){this.children=[];this.hidden=false;this.textContent='';this.value='36500'}append(...items){this.children.push(...items)}replaceChildren(){this.children=[]}addEventListener(){}removeAttribute(name){delete this[name]}set innerHTML(value){throw Error('Untrusted HTML insertion')}}
const elements={};for(const key of ['#days','#state','#rows','#report','#report-title','#report-state','#report-text','#report-source'])elements[key]=new Element();
const text='<script>globalThis.executed=true</script>\nOriginal report';
const hash=createHash('sha256').update(text).digest('hex');
const entry={monitor:'daily',reported_at:'2026-01-01T12:00:00Z',path:'reports/2026/01/01/daily-120000.json',has_report_text:true,content_sha256:hash,bias:{'4h_1d':{score:null,status:'NOT_REPORTED'},'7d':{score:0,status:'REPORTED'},'30d_macro':{score:null,status:'ONVOLDOENDE DATA'}}};
const report={...entry,report_text:text,content_sha256:hash};
const ctx={console,Date,Number,Uint8Array,TextEncoder,crypto:webcrypto,entry,document:{querySelector:s=>elements[s],createElement:()=>new Element()},fetch:async url=>({ok:true,status:200,json:async()=>url.endsWith('index.json')?{reports:[entry]}:report})};
const code=fs.readFileSync('bias.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
vm.createContext(ctx);vm.runInContext(code,ctx);
(async()=>{await new Promise(r=>setImmediate(r));const cells=elements['#rows'].children[0].children;
if(cells[2].textContent!=='NIET GERAPPORTEERD'||cells[3].textContent!=='Neutraal/gemengd'||cells[4].textContent!=='ONVOLDOENDE DATA')throw Error('Score states conflated');
await vm.runInContext('loadReport(entry)',ctx);
if(elements['#report-text'].textContent!==text||ctx.executed)throw Error('Original text altered or executed');
report.content_sha256='wrong';await vm.runInContext('loadReport(entry)',ctx);
if(!elements['#report-state'].textContent.includes('Tekstcontrole mislukt')||elements['#report-text'].textContent!=='')throw Error('Bad hash rendered');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        result = subprocess.run(['node', '-e', code], cwd=str(Path(__file__).resolve().parents[1]),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__': unittest.main()

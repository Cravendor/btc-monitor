import json
from pathlib import Path
from datetime import datetime,timezone
import tempfile
import unittest
from scripts.report_context import read_context,render
from scripts.monitor_archive import checksum,extract_bias


class ContextTests(unittest.TestCase):
    def write(self,root,at,path='reports/2026/10/24/daily.json',text='Algemene marktcontext.',tamper=False):
        raw=dict(schema_version=2,monitor='daily',reported_at=at,report_text=text,source='chatgpt_monitor',
                 content_sha256=checksum(text),bias=extract_bias(text))
        if tamper:raw['report_text']='anders'
        p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(raw))
        index=Path(root)/'reports/index.json';index.write_text(json.dumps({'reports':[dict(path=path,monitor='daily',reported_at=at)]}))

    def test_only_original_valid_recent_context_not_a_news_score(self):
        with tempfile.TemporaryDirectory() as root:
            self.write(root,'2026-10-24T08:00:00Z')
            context=read_context(root,'2026-10-24T09:00:00Z')
            self.assertEqual(len(context),1)
            self.assertNotIn('score',context[0])
            self.assertIn('niet opnieuw onafhankelijk',render(context))
            self.assertEqual(read_context(root,'2026-10-26T09:00:00Z'),[])
            self.assertEqual(read_context(root,'2026-10-23T09:00:00Z'),[])
            self.write(root,'2026-10-24T08:00:00Z',tamper=True)
            self.assertEqual(read_context(root,'2026-10-24T09:00:00Z'),[])

    def test_missing_context_is_explicit(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(read_context(root,'2026-10-24T09:00:00Z'),[])
        self.assertIn('ONTBREEKT',render([]))

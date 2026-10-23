"""Exercise the shipped filter script against its generated DOM structure.

A small read-only DOM adapter covers the script's DOM API; this does not replace
real browser rendering, touch or accessibility verification.
"""
import json
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from scripts.timeframe_history_dashboard import outcome_html


class Tree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = {'tag': 'root', 'attrs': {}, 'children': []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'children': []}
        self.stack[-1]['children'].append(node)
        if tag not in ('meta', 'link', 'br', 'input', 'hr'):
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag not in ('meta', 'link', 'br', 'input', 'hr'):
            assert self.stack[-1]['tag'] == tag, tag
            self.stack.pop()

    def handle_data(self, text):
        self.stack[-1]['children'].append(text)


@unittest.skipUnless(shutil.which('node'), 'Node is required for the client-side smoke test')
class ValidationFilterTests(unittest.TestCase):
    def test_generated_filters_selection_reset_shared_links_and_unchanged_cells(self):
        rows = []
        for model in ('old', 'new'):
            rows.append({'updated_at': '2026-10-20T00:05:00Z', 'signals': {
                tf: {'status': 'ok', 'grade': 'bullish', 'close_price': 100,
                     'candle_closed_at': '2026-10-20T00:00:00Z', 'model_version': model}
                for tf in ('5m', '15m', '30m', '1h', '4h', '1d', '1w')}})
        tree = Tree()
        tree.feed(outcome_html(rows))
        self.assertEqual(len(tree.stack), 1)
        script = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const tree = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
function make(node) {
  if (typeof node === 'string') return node;
  const el = {...node, hidden: 'hidden' in node.attrs, open: false, events: {}};
  el.dataset = Object.fromEntries(Object.entries(el.attrs).filter(([k]) => k.startsWith('data-')).map(([k,v]) => [k.slice(5),v]));
  el.children = node.children.map(make);
  el.matches = selector => selector.startsWith('.') ? (el.attrs.class || '').split(' ').includes(selector.slice(1)) : selector === 'tr[data-tf]' ? el.tag === 'tr' && 'tf' in el.dataset : el.tag === selector;
  el.querySelectorAll = selector => el.children.flatMap(c => typeof c === 'string' ? [] : [...(c.matches(selector) ? [c] : []), ...c.querySelectorAll(selector)]);
  el.addEventListener = (event, handler) => el.events[event] = handler;
  el.value = el.attrs.value || '';
  el.textContent = node.children.filter(c => typeof c === 'string').join('');
  if (el.tag === 'select') { el.options = el.querySelectorAll('option'); el.value = el.options[0].value; }
  return el;
}
function setup(search='') {
  const dom = make(tree);
  const elements = [dom, ...dom.querySelectorAll('section'), ...dom.querySelectorAll('form'), ...dom.querySelectorAll('select'), ...dom.querySelectorAll('button'), ...dom.querySelectorAll('p')];
  const get = id => elements.find(e => e.attrs.id === id);
  const document = { getElementById: get };
  const location = new URL('https://example.test/history.html' + search);
  const history = { replaceState: (_,__,url) => { location.href = String(url); } };
  const context = { document, location, history, URL, URLSearchParams };
  const script = dom.querySelectorAll('script')[0].textContent;
  const cells = dom.querySelectorAll('td').map(c => c.textContent);
  vm.runInNewContext(script, context);
  return {dom,get,location,cells};
}
function selected(dom) {
  const rows=[];
  for (const model of dom.querySelectorAll('.validation-model'))
    for (const sample of model.querySelectorAll('.validation-sample'))
      for (const horizon of sample.querySelectorAll('.validation-horizon'))
        for (const row of horizon.querySelectorAll('tr[data-tf]'))
          if (!model.hidden && !sample.hidden && !horizon.hidden && !row.hidden) rows.push(row);
  return rows;
}
const env=setup();
assert.equal(env.get('validation-filters').hidden,false);
assert.equal(selected(env.dom).length,448);
for (const [id,value] of [['model','new'],['tf','4h'],['horizon','24'],['sample','non_overlapping']]) {
  const field=env.get('validation-'+id); field.value=value; field.events.change();
}
assert.equal(selected(env.dom).length,4);
assert.ok(selected(env.dom).every(row=>row.dataset.tf==='4h'));
assert.match(env.get('validation-filter-status').textContent,/^4 validatieregels/);
assert.equal(env.location.searchParams.get('v_model'),'new');
assert.equal(env.location.searchParams.get('v_tf'),'4h');
assert.deepEqual(env.dom.querySelectorAll('td').map(c=>c.textContent),env.cells);
const restored=setup(env.location.search+'#validation');
assert.equal(selected(restored.dom).length,4);
assert.ok(restored.dom.querySelectorAll('.validation-horizon').some(e=>e.open));
const invalid=setup('?v_tf=%3Cscript%3E&v_model=missing&other=keep#validation');
assert.equal(invalid.get('validation-tf').value,'all');
assert.equal(invalid.get('validation-model').value,'all');
assert.equal(selected(invalid.dom).length,448);
invalid.get('validation-reset').events.click();
assert.equal(invalid.location.searchParams.get('other'),'keep');
assert.equal(invalid.location.searchParams.has('v_tf'),false);
assert.equal(invalid.location.hash,'#validation');
env.get('validation-reset').events.click();
assert.equal(selected(env.dom).length,448);
assert.equal(env.location.search,'');
let prevented=false; env.get('validation-filters').events.submit({preventDefault:()=>prevented=true});
assert.equal(prevented,true);
console.log('Filter selection, restoration, invalid inputs, reset and unchanged cells: OK');
'''
        result = subprocess.run(['node', '-e', script], input=json.dumps(tree.root),
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

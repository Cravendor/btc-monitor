import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const ctx = vm.createContext({});
vm.runInContext(readFileSync(new URL('../web/swing-order.js', import.meta.url),'utf8'),ctx);
const quote = {side:1, entry:100, stop:98, target:110, price:101, expires:1000};
const inputs = {position:0, equity:1000, margin:300, risk:40, fee:5, slip:3, funding:2};
const plan = (s={},p={}) => ctx.decideCard({...quote,...s},{...inputs,...p},1);
test('net gate includes costs, and staleness invalidates every position',()=>{
  assert.equal(plan({target:106}).action,'WACHT');
  assert.equal(plan({expires:1},{position:1,activeStop:95}).action,'WACHT');
  assert.equal(plan({},{fee:NaN}).action,'WACHT');
});
test('risk sizing, margin and missed setups',()=>{
  assert.equal(plan().action,'LIMIET LONG');
  assert.match(plan().reason,/2× isolated/);
  assert.equal(plan({},{margin:1}).action,'WACHT');
  assert.equal(plan({price:97}).action,'WACHT');
  assert.equal(plan({price:111}).action,'WACHT');
});
test('position handling and independently qualifying reversal',()=>{
  assert.equal(plan({},{position:1,activeStop:95}).action,'HOUD VAST');
  assert.equal(plan({},{position:-1,activeStop:110}).action,'SLUIT, DAN LIMIET LONG');
  assert.equal(plan({target:105},{position:-1,activeStop:110}).action,'CONTROLEER / SLUIT');
  assert.equal(plan({side:-1,entry:100,stop:102,target:90,price:99}).action,'LIMIET SHORT');
});

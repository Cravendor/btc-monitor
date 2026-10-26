import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import vm from 'node:vm';

const script=execFileSync('python',['-c','from scripts.elliott_dashboard import SCRIPT; print(SCRIPT)'],{encoding:'utf8'});
test('zoom controls show exactly one window and stop at both boundaries',()=>{
  const plus={listeners:{},addEventListener(n,f){this.listeners[n]=f;}};
  const minus={listeners:{},addEventListener(n,f){this.listeners[n]=f;}};
  const select={selectedIndex:0,options:[{}, {}, {}],listeners:{},get value(){return String(this.selectedIndex);},addEventListener(n,f){this.listeners[n]=f;}};
  const views=[0,1,2].map(i=>({dataset:{view:String(i)},hidden:i!==0}));
  const root={querySelector:s=>s==='select'?select:s==='.ew-zoom-in'?plus:minus,querySelectorAll:()=>views};
  vm.runInNewContext(script,{document:{querySelectorAll:s=>s==='.ew-zoom'?[root]:[]}});
  assert.equal(plus.disabled,true);assert.equal(minus.disabled,false);
  minus.listeners.click();assert.equal(select.selectedIndex,1);
  assert.deepEqual(views.map(v=>v.hidden),[true,false,true]);
  minus.listeners.click();assert.equal(minus.disabled,true);
  minus.listeners.click();assert.equal(select.selectedIndex,2);
  plus.listeners.click();assert.equal(select.selectedIndex,1);
  select.selectedIndex=0;select.listeners.change();
  assert.deepEqual(views.map(v=>v.hidden),[false,true,true]);
  plus.listeners.click();assert.equal(select.selectedIndex,0);
});

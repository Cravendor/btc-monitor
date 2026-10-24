import test from 'node:test';
import assert from 'node:assert/strict';
import {effective,workflowItems} from '../web/status.mjs';
const now=Date.parse('2026-10-24T22:45:00Z');
const descriptor=[{id:'pages',name:'Publicatie',path:'pages.yml',max_age_seconds:7200}];
const workflows=[{path:'.github/workflows/pages.yml',state:'active'}];
const run={id:123,path:'.github/workflows/pages.yml',head_branch:'main',event:'push',
  created_at:'2026-10-24T22:40:00Z',updated_at:'2026-10-24T22:41:00Z',status:'completed',conclusion:'success'};
const get=(runs=[run],w=workflows)=>workflowItems(descriptor,runs,w,now)[0];

test('latest failure, cancellation or running attempt is never masked by older success',()=>{
  const latest={...run,id:124,created_at:'2026-10-24T22:43:00Z',updated_at:'2026-10-24T22:44:00Z'};
  assert.equal(get([run,{...latest,conclusion:'failure'}]).state,'error');
  assert.equal(get([run,{...latest,conclusion:'cancelled'}]).state,'attention');
  assert.equal(get([run,{...latest,status:'in_progress',conclusion:null}]).state,'running');
  assert.equal(get([run,{...latest,status:'queued',conclusion:null}]).state,'attention');
});
test('successful result expires on the client without another deployment',()=>{
  const good=get();assert.equal(good.state,'good');
  assert.equal(effective(good,now+3*3600000).state,'attention');
  assert.equal(effective({...good,expires_at:'invalid'},now).state,'unknown');
  assert.equal(effective({...good,evidence_at:'2027-01-01T00:00:00Z'},now).state,'unknown');
});
test('active GitHub status is distinct from missing, disabled or irrelevant execution',()=>{
  assert.equal(get([]).state,'unknown');
  assert.equal(get([{...run,head_branch:'some-other-branch'}]).state,'unknown');
  assert.equal(get([{...run,event:'pull_request'}]).state,'unknown');
  assert.equal(get([run],[{...workflows[0],state:'disabled_manually'}]).state,'error');
  assert.equal(get([run],[]).state,'unknown');
  assert.equal(get([run],[{...workflows[0],state:null}]).state,'unknown');
  assert.equal(get([{...run,status:'completed',conclusion:null}]).state,'unknown');
});
test('old running status and malformed or missing API data cannot remain green',()=>{
  assert.equal(get([{...run,status:'in_progress',updated_at:'2026-10-24T20:00:00Z'}]).state,'attention');
  assert.equal(get([{...run,updated_at:'2027-01-01T00:00:00Z'}]).state,'unknown');
  assert.throws(()=>get(null));assert.throws(()=>get([],null));
});
test('an on-demand job with an old success becomes unknown, without claiming a stopped schedule',()=>{
  const x=workflowItems([{...descriptor[0],max_age_seconds:null}],[run],workflows,now)[0];
  assert.equal(x.state,'good');
  const older=effective(x,now+8*86400000);
  assert.equal(older.state,'unknown');assert.match(older.label,/op verzoek/);
});

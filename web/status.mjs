const API='https://api.github.com/repos/Cravendor/btc-monitor/actions/';
const STATES=new Set(['good','running','attention','error','unknown']);
const date=value=>typeof value==='string'&&/(Z|[+-]\d{2}:\d{2})$/.test(value)?Date.parse(value):NaN;

export function effective(item,now=Date.now()){
  if(!item||!STATES.has(item.state))return {...item,state:'unknown',label:'Onbekende status'};
  if(item.evidence_at&&(!Number.isFinite(date(item.evidence_at))||date(item.evidence_at)>now+60000))
    return {...item,state:'unknown',label:'Ongeldig tijdsbewijs'};
  if((item.state==='good'||item.state==='running')&&item.expires_at){
    if(!Number.isFinite(date(item.expires_at)))return {...item,state:'unknown',label:'Ongeldige actualiteitsgrens'};
    if(now>date(item.expires_at))return {...item,state:item.expiry_state==='unknown'?'unknown':'attention',label:item.expiry_label||'Statusbewijs verouderd'};
  }
  return item;
}

export function workflowItems(descriptors,runs,workflows,now=Date.now()){
  if(!Array.isArray(runs)||!Array.isArray(workflows))throw Error('Ongeldige GitHub-respons');
  return descriptors.map(d=>{
    const base={id:'gh-'+d.id,name:d.name,system:'GitHub Actions',state:'unknown',label:'Geen uitvoerbewijs',
      detail:'Geen passende uitvoering gevonden in de laatste 100 openbare runs.',evidence_at:null,expires_at:null,
      link:'https://github.com/Cravendor/btc-monitor/actions/workflows/'+d.path};
    const path='.github/workflows/'+d.path;
    const workflow=workflows.find(w=>w.path===path);
    if(!workflow)return {...base,label:'Workflow niet gevonden'};
    if(['disabled_manually','disabled_inactivity','disabled_fork','deleted'].includes(workflow.state))return {...base,state:'error',label:'Workflow uitgeschakeld',detail:'GitHub meldt dat deze workflow niet actief is.'};
    if(workflow.state!=='active')return {...base,label:'Workflowstatus onbekend'};
    // Newest attempt wins even if it failed; never fall back to an older success.
    const found=runs.filter(r=>r.path===path&&r.head_branch==='main'&&r.event!=='pull_request')
      .sort((a,b)=>date(b.created_at)-date(a.created_at))[0];
    if(!found)return base;
    const at=found.updated_at||found.created_at;
    if(!Number.isFinite(date(found.created_at))||date(found.created_at)>now+60000||!Number.isFinite(date(at))||date(at)>now+60000)return {...base,label:'Ongeldige uitvoertijd'};
    const result={...base,evidence_at:at,detail:'Laatste passende uitvoering op main. '+(d.max_age_seconds?'Actualiteit wordt automatisch bewaakt.':'Deze taak wordt op verzoek of bij nieuwe invoer uitgevoerd.'),
      link:Number.isSafeInteger(found.id)&&found.id>0?'https://github.com/Cravendor/btc-monitor/actions/runs/'+found.id:base.link};
    if(found.status==='in_progress')return effective({...result,state:'running',label:'Bezig',expires_at:new Date(date(at)+1200000).toISOString()},now);
    if(['queued','waiting','requested','pending'].includes(found.status))return {...result,state:'attention',label:'Wacht op uitvoering'};
    if(found.status!=='completed')return {...result,label:'Uitvoerstatus onbekend'};
    if(found.conclusion==='success')return effective({...result,state:'good',label:'Laatste run geslaagd',
      expires_at:new Date(date(at)+(d.max_age_seconds||604800)*1000).toISOString(),
      expiry_state:d.max_age_seconds?'attention':'unknown',expiry_label:d.max_age_seconds?'Statusbewijs verouderd':'Geen recente uitvoering (op verzoek)'},now);
    if(['failure','timed_out','action_required','startup_failure'].includes(found.conclusion))return {...result,state:'error',label:found.conclusion==='timed_out'?'Uitvoering verlopen':'Uitvoering mislukt'};
    if(found.conclusion==='cancelled')return {...result,state:'attention',label:'Uitvoering afgebroken'};
    if(['skipped','neutral'].includes(found.conclusion))return {...result,state:'attention',label:'Geen uitvoering / overgeslagen'};
    return {...result,label:'Uitkomst onbekend'};
  });
}

if(typeof document!=='undefined'){
  const $=id=>document.getElementById(id);
  let local=[],github=[],descriptors=[],lastGithub=0,busy=false,localLoaded=null,githubLoaded=null;
  const format=value=>Number.isFinite(date(value))?new Intl.DateTimeFormat('nl-NL',{dateStyle:'medium',timeStyle:'medium',timeZone:'Europe/Amsterdam'}).format(new Date(value)):'Onbekend';
  function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
  function cards(target,items){
    const nodes=items.map(raw=>{
      const x=effective(raw),card=node('article',undefined,'card');
      card.append(node('p',x.system,'kind'),node('h3',x.name));
      const state=node('div',undefined,'state'),dot=node('span',undefined,'dot '+x.state);dot.setAttribute('aria-hidden','true');state.append(dot,node('span',x.label));
      card.append(state,node('p',x.detail));
      if(x.evidence_at){const text=node('p','Laatste bewijs:','evidence'),time=node('time',format(x.evidence_at));time.dateTime=x.evidence_at;text.append(time);card.append(text);}
      if(x.link){const a=node('a','Bekijk uitvoering →');a.href=x.link;card.append(a);}
      return card;
    });$(target).replaceChildren(...nodes);
  }
  function paint(){
    cards('local',local);cards('github',github);
    const all=[...local,...github].map(x=>effective(x));
    const counts=[['Werkt / bezig',all.filter(x=>['good','running'].includes(x.state)).length],['Aandacht',all.filter(x=>x.state==='attention').length],['Fout / uit',all.filter(x=>x.state==='error').length],['Onbekend',all.filter(x=>x.state==='unknown').length]];
    $('counts').replaceChildren(...counts.map(([name,count])=>node('span',count+' '+name,'count')));
  }
  async function get(url){
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
    try{const response=await fetch(url,{cache:'no-store',credentials:'omit',signal:controller.signal});if(!response.ok)throw Error('HTTP '+response.status);return await response.json();}finally{clearTimeout(timer);}
  }
  async function getLocal(){
    try{
      const data=await get('btc-status.json');
      if(data.schema_version!==1||!Array.isArray(data.items)||!Array.isArray(data.workflows)||!Number.isFinite(date(data.generated_at))||date(data.generated_at)>Date.now()+60000)throw Error('Statusbestand ongeldig');
      local=data.items;descriptors=data.workflows;localLoaded=new Date().toISOString();
      $('updated').textContent='Meetbewijs opgehaald: '+format(localLoaded)+' · pagina opgebouwd: '+format(data.generated_at)+'.';
    }catch(error){
      local=(local.length?local:[{id:'missing',name:'NAS en meetbewijs',system:'Statuscontrole'}]).map(x=>({...x,state:'unknown',label:'Statusbron niet bereikbaar',detail:'Er wordt geen eerder groen bewijs als actueel overgenomen.'}));
      $('updated').textContent='Meetstatus kon niet worden opgehaald. Probeer later opnieuw.';
    }paint();
  }
  async function getGithub(){
    if(!descriptors.length){$('api-status').textContent='Statusconfiguratie niet beschikbaar; GitHub-status onbekend.';return;}
    if(Date.now()-lastGithub<30000)return;
    lastGithub=Date.now();
    const results=await Promise.allSettled([get(API+'runs?per_page=100'),get(API+'workflows?per_page=100')]);
    try{
      if(results.some(r=>r.status!=='fulfilled'))throw Error('GitHub niet bereikbaar');
      github=workflowItems(descriptors,results[0].value.workflow_runs,results[1].value.workflows);
      githubLoaded=new Date().toISOString();$('api-status').textContent='GitHub gecontroleerd: '+format(githubLoaded)+'.';
    }catch(error){github=descriptors.map(d=>({id:'gh-'+d.id,name:d.name,system:'GitHub Actions',state:'unknown',label:'GitHub-status onbekend',detail:'API niet bereikbaar, ongeldige respons of limiet bereikt. Geen eerdere groene status overgenomen.'}));$('api-status').textContent='GitHub-status niet beschikbaar; geen API-sleutel of betaald alternatief nodig.';}
    paint();
  }
  async function refresh(){if(busy)return;busy=true;$('refresh').disabled=true;try{await getLocal();await getGithub();}finally{busy=false;$('refresh').disabled=false;}}
  $('refresh').addEventListener('click',refresh);
  refresh();setInterval(async()=>{if(busy)return;busy=true;try{await getLocal();}finally{busy=false;}},60000);setInterval(paint,30000);
}

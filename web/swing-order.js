function decideCard(s, p, now) {
  const wait = reason => ({action: 'WACHT', reason});
  if (!s.expires || now >= s.expires) return wait('Marktmeting ontbreekt of is verlopen. Vernieuw voor een nieuwe beoordeling.');
  const usd = value => value.toLocaleString('nl-NL', {style: 'currency', currency: 'USD'});
  const existing = p.position !== 0;
  if (existing && !(p.activeStop > 0)) return wait('Vul de beschermende stop van je bestaande positie in.');
  const stopPassed = existing && p.position * (s.price - p.activeStop) <= 0;
  // A sampled quote cannot establish an exchange fill between observations.
  const base = existing ? {action: stopPassed || s.side === -p.position ? 'CONTROLEER / SLUIT' : 'HOUD VAST',
    reason: stopPassed ? 'De gemeten koers ligt voorbij je stop. Controleer eerst de uitvoering bij je beurs.' :
      s.side === -p.position ? 'De afgesloten terugtest ondersteunt de andere richting.' :
      'Geen tegengestelde 4H-terugtest. Houd je bestaande beschermende stop actief.'} : wait(s.reason + (s.support && s.resistance ?
        '\nRecente 4H-steun '+usd(s.support)+' · Weerstand '+usd(s.resistance) : ''));
  if (!s.side || p.position === s.side || stopPassed) return base;
  const {entry, stop, target, side} = s;
  const explain = reason => existing ? {...base, reason: base.reason + ' ' + reason} : wait(reason);
  if (side * (s.price-entry) <= 0 || side * (target-s.price) <= 0)
    return explain('De gemeten koers is voorbij de instap of het doel. Wacht op een nieuwe terugtest.');
  if (![p.fee,p.slip,p.funding].every(v => Number.isFinite(v) && v >= 0))
    return explain('Vul de kostenraming in.');
  const cost = exit => (entry+exit)*(p.fee+p.slip)/10000 + entry*p.funding/10000;
  const risk = Math.abs(entry-stop)+cost(stop);
  const reward = side*(target-entry)-cost(target);
  const ratio = reward/risk;
  if (ratio < 3) return explain('Netto verhouding 1:' + ratio.toFixed(2) + '. Minimum 1:3.');
  if (![p.equity,p.risk,p.margin].every(v => Number.isFinite(v) && v > 0) ||
      p.risk > p.equity || p.margin > p.equity)
    return explain('Setup haalt 1:3. Vul kapitaal, verliesplafond en beschikbare marge in bij Risico.');
  const spot = s.deltas?.spot;
  const futures = s.deltas?.usdt_futures;
  const aligned = Number.isFinite(spot) && Number.isFinite(futures) &&
    side*spot > 0 && side*futures > 0 && s.volume_ratio >= 1;
  const budgetFraction = aligned ? 0.5 : 0.25;
  const quantity = Math.floor(p.risk*budgetFraction/risk*1e6)/1e6;
  const value = quantity*entry;
  const leverage = [1,2].find(l => value/l + quantity*cost(stop) <= p.margin);
  if (!Number.isFinite(value) || !quantity || !leverage) return explain('De berekende omvang past niet binnen de marge of precisie.');
  if (quantity*risk > 0.25*value/leverage)
    return explain('Het geplande verlies is groter dan 25% van de isolated marge.');
  const direction = side === 1 ? 'LONG' : 'SHORT';
  return {action: existing ? 'SLUIT, DAN LIMIET '+direction : 'LIMIET '+direction,
    reason: (existing ? 'Controleer eerst dat de oude positie gesloten is. ' : '') +
    (aligned ? 'Spot- en futuresdelta bevestigen de richting. ' : 'Beperkte volumebevestiging. ') +
    'Na bevestigde terugtest. Annuleer een onvervulde limiet bij het volgende 4H-slot of bij invalidatie.\n' +
    'Limiet '+usd(entry)+' · Stop '+usd(stop)+' · Doel '+usd(target)+'\n'+
    quantity.toFixed(6)+' BTC · '+leverage+'× isolated · Marge '+usd(value/leverage)+'\n'+
    'Gepland verlies '+usd(quantity*risk)+' · Nettowinst bij doel '+usd(quantity*reward)+' · 1:'+ratio.toFixed(2)};
}

function mountCard(root, snapshot) {
  const field = id => root.querySelector('#oc-'+id);
  function applyPreset() {
    const choice = field('preset').value;
    if (choice === 'custom') {
      field('settings').open = true;
      return;
    }
    const equity = Number(choice);
    field('equity').value = equity;
    field('risk').value = equity * 0.02;
    field('margin').value = equity * 0.40;
  }
  function update() {
    const params = {position: Number(field('position').value)};
    for (const key of ['equity','risk','margin','fee','slip','funding'])
      params[key] = field(key).valueAsNumber;
    const usd = value => value.toLocaleString('nl-NL', {style:'currency',currency:'USD'});
    const basis = field('preset').value === 'custom' ? 'Eigen berekening' : 'Rekenvoorbeeld';
    field('budget').textContent = [params.equity,params.risk,params.margin].every(v => Number.isFinite(v) && v > 0)
      && params.risk <= params.equity && params.margin <= params.equity
      ? basis+' · Risicobudget per setup '+usd(params.risk*0.25)+' tot '+usd(params.risk*0.5)+
        ' · Margeplafond '+usd(params.margin)
      : 'Controleer je eigen bedragen bij de instellingen.';
    params.activeStop = field('active-stop').valueAsNumber;
    field('stop-row').hidden = !params.position;
    const advice = decideCard(snapshot, params, Date.now());
    field('action').textContent = advice.action;
    field('result').textContent = advice.reason;
  }
  field('time').textContent = snapshot.at ? 'Bitget BTCUSDT · afrekening USDT · USD per USDT '+snapshot.rate+
    ' · Meting '+new Date(snapshot.at).toLocaleString('nl-NL',{timeZone:'Europe/Amsterdam'})+' Amsterdam' : 'Bitget BTCUSDT';
  root.addEventListener('input', event => {
    if (event.target === field('preset')) applyPreset();
    if (['equity','risk','margin'].some(key => event.target === field(key)))
      field('preset').value = 'custom';
    update();
  });
  applyPreset();
  update();
  if (snapshot.expires > Date.now()) setTimeout(update, snapshot.expires-Date.now()+1);
}

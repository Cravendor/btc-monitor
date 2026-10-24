"""Mobile market meters: BNB direction, scenario-linked SHB and sentiment."""
import html
import math
try:
    from scripts.market_scenarios import time_ms
except ModuleNotFoundError:
    from market_scenarios import time_ms

LABELS = {-2:'Sterk bearish',-1:'Zwak bearish',0:'Neutraal',1:'Zwak bullish',2:'Sterk bullish'}


def esc(value):
    return html.escape(str(value),quote=True)


def sentiment_gauge(as_of,sentiment):
    missing=dict(value=None,label='Onvoldoende data',quality='Ontbreekt',reason='Actuele sentimentbron ontbreekt.',valid_until='',observed_at='')
    sentiment=sentiment or {}
    try:
        value=sentiment['value']
        if (sentiment.get('status')!='ok' or type(value) is not int or not 0<=value<=100
            or sentiment['provider'] not in ('CoinMarketCap','Alternative.me')
            or not -60000<=time_ms(as_of)-time_ms(sentiment['source_at'])<36*3600000
            or time_ms(sentiment['valid_until'])!=time_ms(sentiment['source_at'])+36*3600000):
            return missing
        return dict(value=value/50-1,label=str(value)+'/100 · '+sentiment['label'],quality='Actueel',
            reason='Dagindex, geen koop-/verkoopsignaal.',valid_until=sentiment['valid_until'],
            observed_at=sentiment['source_at'],provider=sentiment['provider'],fallback=sentiment.get('fallback',False))
    except (ValueError,TypeError,KeyError,OverflowError):
        return missing


def svg(value, title, sentiment=False):
    def point(deg, radius=112):
        angle = math.radians(deg)
        return 160 + radius * math.cos(angle), 140 - radius * math.sin(angle)
    colors = ['#e88f96', '#dcad81', '#aab6ca', '#8bcbb7', '#55cda0']
    if sentiment:
        colors = ['#a49ce9', '#849bcb', '#aab6ca', '#d7bb84', '#f1a957']
    arcs = []
    for i, color in enumerate(colors):
        x1, y1 = point(180 - i*36 - 1)
        x2, y2 = point(180 - (i+1)*36 + 1)
        arcs.append(f'<path d="M{x1:.2f},{y1:.2f} A112,112 0 0,1 {x2:.2f},{y2:.2f}" stroke="{color}"/>')
    needle = ''
    if value is not None:
        x, y = point(90 - value*90, 91)
        needle = (f'<g class="gauge-needle"><path d="M160,140 L{x:.2f},{y:.2f}" '
                  'stroke="#f5f8ff" stroke-width="4" stroke-linecap="round"/>'
                  '<circle cx="160" cy="140" r="8" fill="#f5f8ff"/></g>')
    return ('<svg class="dial" viewBox="0 0 320 163" role="img" aria-label="' + esc(title) + '">'
            '<g fill="none" stroke-width="17">' + ''.join(arcs) + '</g>'
            '<path d="M160 14 V23" stroke="#e6edf9" stroke-width="2"/>' + needle + '</svg>')


CSS = '''
.meter-stack{display:grid;grid-template-columns:1fr;gap:16px;max-width:640px;margin:0 auto 32px}
.meter{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:20px;min-width:0}
.meter-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.meter h3{font-size:1rem;margin:0}.meter .data-badge{font-size:.7rem;white-space:nowrap;border:1px solid #71849e;border-radius:30px;padding:3px 8px;color:#c6d7ed}
.meter .data-badge[data-quality="Actueel"]{color:#9ee7c4;border-color:#4f8a73}
.meter .data-badge[data-quality="Beperkt"]{color:#ffcb88;border-color:#aa844e}
.meter .dial{display:block;width:100%;max-width:360px;height:auto;margin:5px auto 0}
.meter .dial-labels{display:flex;justify-content:space-between;gap:5px;font-size:.74rem;color:var(--muted)}
.meter .dial-labels span{flex:1}.meter .dial-labels span:nth-child(2){text-align:center}.meter .dial-labels span:last-child{text-align:right}
.meter .meter-reading{text-align:center;font-size:1.12rem;font-weight:700;color:var(--text);margin:10px 0}
.meter p,.meter details{font-size:.85rem}.meter .meter-time{font-size:.72rem;overflow-wrap:anywhere}.meter details{padding-bottom:0}.meter summary{min-height:36px}
.meter-stack-title{max-width:640px;margin:0 auto 16px}.meter .model-tag{text-align:center;font-size:.72rem;color:#d3b993}
@media(max-width:380px){.meter{padding:14px}.meter-head{gap:6px}.meter .data-badge{font-size:.65rem}}
'''

SCRIPT = '''
function refreshGauges(){document.querySelectorAll('.meter[data-expires]').forEach(el=>{
const expiry=Date.parse(el.dataset.expires);if(!Number.isFinite(expiry)||Date.now()<expiry)return;
el.querySelectorAll('.gauge-needle').forEach(n=>n.remove());
el.querySelectorAll('.meter-reading').forEach(n=>n.textContent='Onvoldoende actuele data');
el.querySelectorAll('.shb-levels').forEach(n=>n.hidden=true);
el.querySelectorAll('.dial').forEach(n=>n.setAttribute('aria-label','Onvoldoende actuele data'));
const badge=el.querySelector('.data-badge');badge.textContent='Data: verouderd';badge.dataset.quality='Verouderd';
el.querySelectorAll('.meter-reason').forEach(n=>n.textContent='Deze meting is verlopen. Vernieuw de pagina voor de laatste publicatie.');
});}
refreshGauges();setInterval(refreshGauges,30000);
'''


MODE_NAMES={'swing':'Swing · 1D','position':'Positietrade · 1W'}


def build_gauges(feed,as_of,sentiment=None,mode='swing'):
    try:
        from .swing_scenarios import build_swing_scenarios
    except ImportError:
        from swing_scenarios import build_swing_scenarios
    if mode not in MODE_NAMES:
        raise ValueError('unknown mode')
    missing=dict(value=None,label='Onvoldoende data',quality='Ontbreekt',reason='Actuele native brondata ontbreken.',valid_until='',observed_at='')
    r=build_swing_scenarios(feed,as_of)['horizons'][mode]
    momentum,action=dict(missing),dict(missing)
    if r['status']=='ready':
        signal=r['momentum']
        common=dict(quality='Actueel' if signal['volume_ratio'] is not None else 'Beperkt',
                    observed_at=r['candle_closed_at'],valid_until=r['valid_until'])
        momentum=dict(common,value=signal['score']/2,label=LABELS[signal['score']],
            reason='Slot versus voorafgaand 20-candlegemiddelde: {:+.2f}%; koersverandering over 6 candles: {:+.2f}%; relatief volume: {}. Voorlopig prijs-/volumemodel.'.format(signal['price_vs_20_prior_pct'],signal['momentum_6_pct'],signal['volume_ratio']))
        from .two_routes import assess as assess_two_routes
        assessment=assess_two_routes(r)
        code=assessment['combined']['score']
        if code is not None:
            action=dict(common,value=code/2,label=assessment['combined']['label'],
                        reason=assessment['context'],quality='Beperkt')
        else:
            action['reason']=assessment['context']
    fear=sentiment_gauge(as_of,sentiment)
    return [momentum,action,fear]


def render(feed,as_of,sentiment=None,mode='swing'):
    items=build_gauges(feed,as_of,sentiment,mode)
    titles=['BNB · richting · '+MODE_NAMES[mode],'SHB · scenario · '+MODE_NAMES[mode],'Fear & Greed · dagindex']
    ends=[('Bearish','Neutraal','Bullish'),('Bearish','Afwachten','Bullish'),('Angst · 0','Midden · 50','Hebzucht · 100')]
    explanations=[
        'BNB staat hier voor Bear–Neutraal–Bull: de marktrichting. Dagcandles voor swing, weekcandles voor positie. De huidige gesloten candle wordt met de 20 voorafgaande vergeleken; momentum meet 6 candles. Richting vereist overeenstemming boven ±0,5%. Sterk vereist ook meer dan ±2% afwijking en volume ≥1,2×. Dit zijn gecorreleerde prijsmetingen, geen onafhankelijke bevestigingen. Een losse 4H-beweging bepaalt de dag-/weekbeoordeling niet zelfstandig.',
        '',
        'Dagelijkse sentimentcontext, geen koop-/verkoopregel. Eerst CoinMarketCap; Alternative.me is een expliciet genoemde reservebron. De categorie komt van de bron; indices worden niet samengevoegd. Brondata ouder dan 36 uur worden verborgen.'
    ]
    cards=[]
    for i,item in enumerate(items):
        if i==1:
            from .two_routes import render_meter
            from .swing_scenarios import build_swing_scenarios
            cards.append(render_meter(build_swing_scenarios(feed,as_of)['horizons'][mode],mode))
            continue
        quality=item['quality'] if item['value'] is not None else 'Ontbreekt'
        source=''
        if i==2 and item.get('provider'):
            provider=item['provider'];url='https://alternative.me/crypto/fear-and-greed-index/' if provider=='Alternative.me' else 'https://coinmarketcap.com/charts/fear-and-greed-index/'
            source='<p>Bron: <a href="'+url+'">'+provider+'</a>'+(' · reservebron' if item.get('fallback') else '')+'</p>'
        stamp='<p class="meter-time">Bronmoment / candle-einde: <time>'+esc(item['observed_at'])+'</time></p>' if item['observed_at'] else ''
        cards.append('<article class="meter" data-expires="'+esc(item['valid_until'])+'"><div class="meter-head"><h3>'+titles[i]+'</h3><span class="data-badge" data-quality="'+quality+'">Data: '+quality.lower()+'</span></div>'+svg(item['value'],titles[i]+': '+item['label'],i==2)+'<div class="dial-labels">'+''.join('<span>'+e+'</span>' for e in ends[i])+'</div><p class="meter-reading" role="status">'+esc(item['label'])+'</p>'+('<p class="model-tag">Voorlopig model · niet gekalibreerd</p>' if i<2 else '')+source+stamp+'<details><summary>Uitleg en onderbouwing</summary><p class="meter-reason">'+esc(item['reason'])+'</p><p>'+explanations[i]+'</p><p>Data: actueel betreft alleen actualiteit/volledigheid van de gebruikte bron; beperkt betreft ontbrekende context of modelbeperkingen. Geen voorspelnauwkeurigheid, marktbrede dekking of persoonlijke handelsinstructie.</p></details></article>')
    return '<div data-mode-panel="'+mode+'"'+(' hidden' if mode=='position' else '')+'><section class="meter-stack" aria-label="Drie marktmeters '+mode+'">'+''.join(cards)+'</section></div>'


def render_all(feed,as_of,sentiment=None):
    return '<div class="meter-stack-title"><h2>Je drie marktmeters</h2><p>BNB geeft richting; bull- en bearroute geven samen een niveau-uitleg. Kies swing of positie. Uitleg is inklapbaar.</p><p><a href="btc-action-history.html">Niveauhistorie, scenario-evaluatie en kwaliteitscontrole →</a></p></div><div class="mode-controls" role="group" aria-label="Handelshorizon"><button type="button" data-select-mode="swing" aria-pressed="true">Swing · dag</button><button type="button" data-select-mode="position" aria-pressed="false">Positie · week</button></div>'+''.join(render(feed,as_of,sentiment,mode) for mode in MODE_NAMES)

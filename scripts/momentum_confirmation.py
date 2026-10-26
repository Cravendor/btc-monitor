"""Synchronized 4H evidence, not a wave-count certification or probability model."""
from decimal import Decimal, InvalidOperation
from html import escape
import json
from pathlib import Path
from scripts.market_scenarios import time_ms, iso
from scripts.swing_scenarios import valid_market, native_rows

MODEL = 'multi_source_momentum_v1'
PERIOD = 14400000


def decimal(value):
    if value is None or isinstance(value, bool):
        raise ValueError('missing number')
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('invalid number')
    return result


def flow(record, market, start, end):
    if (record.get('exchange'), record.get('market'), record.get('symbol')) != ('bitget', 'USDT-FUTURES', 'BTCUSDT'):
        raise ValueError('wrong market')
    if time_ms(record['started_at']) < end or time_ms(record['finished_at']) < time_ms(record['started_at']):
        raise ValueError('flow observed before interval closed')
    cvd = record['cvd_4h']
    if (cvd.get('exchange'), cvd.get('symbol'), cvd.get('method'), cvd.get('interval_convention')) != ('bitget', 'BTCUSDT', 'provider_reported_buy_minus_sell', '[start,end)'):
        raise ValueError('wrong flow scope')
    if time_ms(cvd['interval_start']) != start or time_ms(cvd['interval_end']) != end:
        raise ValueError('different window')
    if cvd.get('status') not in ('ok', 'partial'):
        raise ValueError('unverified flow')
    data = cvd['markets'][market]
    if data.get('status') != 'ok' or data.get('coverage_verified') is not True or data.get('interval_start_ms') != start or data.get('interval_end_ms') != end:
        raise ValueError('unverified market window')
    if data.get('coverage_scope') != 'bitget_public_history_only' or data.get('market') != market:
        raise ValueError('different market scope')
    buy, sell = decimal(data['validated_buy_btc']), decimal(data['validated_sell_btc'])
    delta = decimal(data['validated_delta_btc'])
    if min(buy, sell) < 0 or buy + sell <= 0 or buy - sell != delta or decimal(data['value']) != delta:
        raise ValueError('invalid flow totals')
    return delta, buy + sell


def previous_record(root, current):
    """Latest original observation available before current started; never future flow."""
    try:
        start = time_ms(current['cvd_4h']['interval_start'])
        cutoff = time_ms(current['started_at'])
    except (KeyError, TypeError, ValueError):
        return None
    found = []
    for path in Path(root).glob('????/??/??/*.json'):
        try:
            r = json.loads(path.read_text(encoding='utf-8'))
            if time_ms(r['finished_at']) > cutoff:
                continue
            if time_ms(r['cvd_4h']['interval_end']) != start:
                continue
            # Preserve independently valid legs; build() gates each market.
            valid = 0
            for market in ('spot', 'usdt_futures'):
                try:
                    flow(r, market, start-PERIOD, start)
                    valid += 1
                except (KeyError, TypeError, ValueError, InvalidOperation):
                    pass
            if not valid:
                continue
            found.append((time_ms(r['finished_at']), path.as_posix(), r))
        except (OSError, KeyError, TypeError, ValueError, InvalidOperation):
            continue
    if not found:
        return None
    latest = max(x[0] for x in found)
    tied = [x[2] for x in found if x[0] == latest]
    if any(x != tied[0] for x in tied[1:]):
        return None
    return tied[0]


def build(feed, as_of, previous=None):
    out = dict(model_version=MODEL, status='unavailable', state='unavailable',
               probability=None, scope='4H; geen bevestiging van een weekgolf', groups={},
               missing=[], contradictions=[])
    try:
        m = valid_market(feed, as_of)
        rows, _ = native_rows(m, '4h', as_of)
        if len(rows) < 24:
            raise ValueError('insufficient contiguous candles')
        last = rows[-1]; start = last['open_time_ms']; end = start+PERIOD
        if end != time_ms(as_of)//PERIOD*PERIOD:
            raise ValueError('stale closed interval')
        out.update(status='partial', interval_start=iso(start), interval_end=iso(end),
                   valid_until=iso(min(end+PERIOD, time_ms(m['started_at'])+3600000)))
        # One price-momentum group, rather than independent RSI/MACD/ROC votes.
        now = decimal(last['close'])/decimal(rows[-4]['close'])-1
        prior = decimal(rows[-2]['close'])/decimal(rows[-5]['close'])-1
        direction = 1 if now > 0 else -1 if now < 0 else 0
        structure = 1 if last['close'] > max(r['high'] for r in rows[-4:-1]) else -1 if last['close'] < min(r['low'] for r in rows[-4:-1]) else 0
        out['groups']['structure'] = dict(direction=structure, rule='slot buiten vorige drie gesloten 4H-candles')
        out['groups']['momentum'] = dict(direction=direction, roc3_pct=str(now*100), previous_roc3_pct=str(prior*100))
        out['state'] = ('tentative_bullish_switch' if now > 0 and prior <= 0 else
                        'tentative_bearish_switch' if now < 0 and prior >= 0 else
                        'bearish_weakening' if prior < now < 0 else
                        'bullish_weakening' if 0 < now < prior else
                        'bullish_momentum' if now > 0 else 'bearish_momentum' if now < 0 else 'mixed')
        for market in ('spot', 'usdt_futures'):
            try:
                delta, volume = flow(m, market, start, end)
                if market == 'usdt_futures' and volume != decimal(last['base_volume_btc']):
                    raise ValueError('futures candle mismatch')
                if previous is None or time_ms(previous['finished_at']) > time_ms(m['started_at']):
                    raise ValueError('missing point-in-time prior')
                old_delta, old_volume = flow(previous, market, start-PERIOD, start)
                ratio = volume/old_volume
                side = 1 if delta > 0 else -1 if delta < 0 else 0
                out['groups'][market] = dict(direction=side, delta_btc=str(delta), previous_delta_btc=str(old_delta),
                    volume_btc=str(volume), previous_volume_btc=str(old_volume), volume_ratio=str(ratio),
                    supports=side == direction and direction != 0 and ratio >= 1)
                if direction and side == -direction:
                    out['contradictions'].append(market)
            except (KeyError, TypeError, ValueError, InvalidOperation):
                out['missing'].append(market+'_current_or_previous_evidence')
        if structure and direction and structure != direction:
            out['contradictions'].append('structure')
        if not out['missing']:
            out['status'] = 'assessed'
            if structure == direction and direction and now*direction >= prior*direction and all(out['groups'][x]['supports'] for x in ('spot','usdt_futures')):
                out['state'] = 'bullish_supported' if direction > 0 else 'bearish_supported'
        # Positioning is context, not a vote from unmatched point observations.
        out['context'] = {k: ('snapshot_available_not_interval_vote' if m.get('metrics',{}).get(k,{}).get('status')=='ok' else 'unavailable')
                          for k in ('open_interest','funding','futures_basis','coinbase_premium_proxy')}
    except (KeyError, TypeError, ValueError, InvalidOperation, ZeroDivisionError, OverflowError):
        out.update(status='unavailable', state='unavailable', groups={}, missing=['valid_current_4h_price_source'])
    return out


LABELS = dict(unavailable='Onvoldoende actuele gegevens', mixed='Geen momentumrichting',
    tentative_bullish_switch='Voorlopige bullish momentumomslag', tentative_bearish_switch='Voorlopige bearish momentumomslag',
    bearish_weakening='Bearish momentum neemt af', bullish_weakening='Bullish momentum neemt af',
    bullish_momentum='Bullish koersmomentum', bearish_momentum='Bearish koersmomentum',
    bullish_supported='Bullish momentum met spot- en futuressteun', bearish_supported='Bearish momentum met spot- en futuressteun')


def render(result):
    parts = ['<section class="panel" id="momentum-confirmation"><h2>Momentumomslag · gezamenlijke controle</h2>']
    parts.append('<p><b>'+LABELS[result['state']]+'</b></p>')
    if result.get('interval_end'):
        parts.append('<p>Gesloten 4H-venster '+escape(result['interval_start'])+' tot '+escape(result['interval_end'])+'.</p>')
        parts.append('<p class="momentum-expiry" data-until="'+escape(result['valid_until'])+'">Beoordeling geldig tot '+escape(result['valid_until'])+'.</p>')
    parts.append('<p>4H-bewijs; geen bevestigde Elliott-weekgolf. Experimentele regels, geen gekalibreerd kanspercentage. Volume alleen geeft geen kooprichting; RSI/MACD worden niet als extra stemmen opgeteld.</p>')
    parts.append('<ul>')
    for key, group in result['groups'].items():
        name = {'structure':'Koersstructuur', 'momentum':'Koersmomentum (ROC over 3 candles)', 'spot':'Spot', 'usdt_futures':'Futures'}[key]
        direction = {1:'bullish', -1:'bearish', 0:'geen richting'}[group['direction']]
        detail = ('slot boven/onder de vorige drie candles' if key == 'structure' else
                  'vorige '+format(float(group['previous_roc3_pct']),'.2f')+'%, nu '+format(float(group['roc3_pct']),'.2f')+'%' if key == 'momentum' else
                  'delta vorige '+group['previous_delta_btc']+', nu '+group['delta_btc']+' BTC; volume '+format(float(group['volume_ratio']),'.2f')+'× het vorige venster')
        parts.append('<li><b>'+name+'</b>: '+direction+' · '+escape(detail)+'</li>')
    parts.append('</ul>')
    if result['missing']:
        parts.append('<p>ONTBREEKT: '+escape(', '.join(result['missing']))+'. Volledige bevestiging niet beschikbaar.</p>')
    if result['contradictions']:
        parts.append('<p>Tegenbewijs: '+escape(', '.join(result['contradictions']))+'.</p>')
    parts.append('<p>OI, funding, basis en premium zijn in deze versie geen richtingstem: vergelijkbare historische venstergegevens worden nog niet getoetst.</p>')
    parts.append('<p>Spot/futures: provider buy−sell, geen onafhankelijk bevestigde agressorzijde. Volumesteun: ten minste het vorige vergelijkbare 4H-volume; dit is een te toetsen modelregel.</p></section>')
    return ''.join(parts)


SCRIPT = """document.querySelectorAll('.momentum-expiry').forEach(el=>{function expire(){if(Date.now()>=Date.parse(el.dataset.until)){const panel=el.closest('section');panel.querySelector('b').textContent='HISTORISCH — geen actuele momentumbevestiging';el.textContent='Deze beoordeling is verlopen. Vernieuw voor nieuwe meetgegevens.';}}expire();setInterval(expire,60000);});"""

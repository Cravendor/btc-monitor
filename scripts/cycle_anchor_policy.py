"""Cycle-peak and running-low anchor contract; no calendar phase inference.

The collector may supply cycle_anchor_context when the previous cycle peak and phase have been identified
and a complete same-market daily source is available. Absent context is inactive.
"""
import hashlib
import json
try:
    from .market_scenarios import time_ms, iso, number
except ImportError:
    from market_scenarios import time_ms, iso, number

DAY=86400000
VERSION='cycle_peaks_running_low_v2'
IDENTITY=('bitget','USDT-FUTURES','BTCUSDT')


def select(context, as_of):
    missing=dict(status='unavailable',model_version=VERSION,
        reason='Cyclusreferentie onvoldoende onderbouwd; geen vervanging door rangeankers.')
    try:
        if not isinstance(context,dict) or context.get('schema_version')!=1:
            raise ValueError('Ongeldige cyclusconfiguratie.')
        if context.get('status')!='active' or not isinstance(context.get('cycle_id'),str) or not context['cycle_id'].strip():
            raise ValueError('Geen expliciet actieve cyclus.')
        if not isinstance(context.get('classification_basis'),str) or not context['classification_basis'].strip():
            raise ValueError('Onderbouwing voor cyclustop en fase ontbreekt.')
        if context.get('previous_cycle_id')==context['cycle_id']:
            raise ValueError('Nieuwe cyclus mag niet dezelfde identiteit hebben als de vorige.')
        now=time_ms(as_of);boundary=now//DAY*DAY
        previous_peak=time_ms(context['previous_cycle_peak_at'])
        phase=context['phase']
        if phase not in ('advance','post_peak'):
            raise ValueError('Fase moet advance of post_peak zijn; geen automatische cyclusclassificatie.')
        if previous_peak<0 or previous_peak%DAY or previous_peak>=boundary-DAY:
            raise ValueError('Vorige cyclustop moet een historische UTC-dagcandle zijn.')
        source=context['source']
        if tuple(source.get(k) for k in ('exchange','market','symbol'))!=IDENTITY:
            raise ValueError('Cyclusankers vereisen dezelfde Bitget futuresmarkt.')
        if source.get('status')!='ok' or source.get('interval')!='1d' or source.get('closed_only') is not True:
            raise ValueError('Geen geldige afgesloten daghistorie.')
        if not -60000<=now-time_ms(source['observed_at'])<3600000:
            raise ValueError('Cyclusbron is verouderd.')
        candles=source['candles']
        if not isinstance(candles,list) or len(candles)>6000:
            raise ValueError('Ongeldige omvang cyclusbron.')
        rows={}
        for c in candles:
            t=c['open_time_ms']
            if type(t) is not int or t<0 or t%DAY or t>=boundary or t in rows:
                raise ValueError('Dubbele, open of ongeldige dagcandle.')
            o,h,l,close=(number(c[k]) for k in ('open','high','low','close'))
            if l<=0 or l>min(o,close) or h<max(o,close):
                raise ValueError('Ongeldige OHLC-waarden.')
            rows[t]=(h,l)
        if any(t not in rows for t in range(previous_peak,boundary,DAY)):
            raise ValueError('Onvolledige historie vanaf de vorige cyclustop.')
        highs=[(t,v[0]) for t,v in rows.items() if previous_peak<t<boundary]
        high=max(v for t,v in highs)
        # Equal highs do not restart the drawdown; only a strictly higher record does.
        high_at=min(t for t,v in highs if v==high)
        if high<=rows[previous_peak][0]:
            raise ValueError('Nog geen hogere cyclustop dan de vorige referentietop.')
        left,right=(previous_peak+DAY,high_at) if phase=='advance' else (high_at+DAY,boundary)
        lows=[(t,v[1]) for t,v in rows.items() if left<=t<right]
        if not lows:
            raise ValueError('Nog geen afzonderlijke afgesloten low-candle in het gekozen topinterval.')
        low=min(v for t,v in lows)
        # Equal lows must not move the original anchor or its version.
        low_at=min(t for t,v in lows if v==low)
        if low>=high:raise ValueError('Geen bruikbaar ankerbereik.')
        result=dict(status='calculated',model_version=VERSION,anchor_method=VERSION,
            cycle_id=context['cycle_id'],phase=phase,classification_basis=context['classification_basis'],
            high=high,low=low,high_at=iso(high_at),low_at=iso(low_at),
            cycle_start=iso(previous_peak+DAY),cycle_through=iso(boundary),
            previous_cycle_peak_at=iso(previous_peak),previous_cycle_peak_price=rows[previous_peak][0],
            bull_window_from=iso(left),bull_window_through=iso(right),
            source_timeframe='1d',same_anchors_for_all_horizons=True,
            history_from=iso(previous_peak),history_to=iso(boundary),
            history_candles=len(rows),high_at_history_boundary=False,
            bottom_confirmed=False,cycle_extremes_verified=False,
            reference_market='bitget/BTCUSDT/USDT-FUTURES',unit='USDT',
            observed_at=source['observed_at'],calculated_at=as_of,
            reason=('Bull: laagste koers tussen vorige en nieuwste cyclustop.' if phase=='advance' else
                    'Bull: laagste koers sinds de nieuwste cyclustop; alleen een strikt lagere low verplaatst het anker.')+
                   ' Bear: hoogste gemeten koers sinds de vorige cyclustop. Fasekeuze is expliciet; geen bevestigde bodem.',
            evidence=context)
        identity=json.dumps({k:result[k] for k in ('model_version','cycle_id','phase','previous_cycle_peak_at','high','low','high_at','low_at')},sort_keys=True,separators=(',',':'),allow_nan=False)
        result['anchor_version_id']=hashlib.sha256(identity.encode()).hexdigest()[:24]
        return result
    except (ValueError,KeyError,TypeError,AttributeError,OverflowError) as e:
        return dict(missing,reason=str(e) if isinstance(e,ValueError) else missing['reason'])


def validate(anchor):
    if anchor.get('status')!='calculated':
        return True
    if select(anchor.get('evidence'),anchor.get('calculated_at'))!=anchor:
        raise ValueError('Cycle anchors disagree with original evidence')
    return True

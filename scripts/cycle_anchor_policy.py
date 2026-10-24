"""Explicit next-cycle anchor contract; no calendar/halving phase inference.

The collector may supply cycle_anchor_context when a cycle has been identified
and a complete same-market daily source is available. Absent context is inactive.
"""
from datetime import datetime, timezone
import hashlib
import json
try:
    from .market_scenarios import time_ms, iso, number
except ImportError:
    from market_scenarios import time_ms, iso, number

DAY=86400000
VERSION='explicit_cycle_bear_year_anchors_v1'
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
            raise ValueError('Onderbouwing voor cyclus/bearjaar ontbreekt.')
        if context.get('previous_cycle_id')==context['cycle_id']:
            raise ValueError('Nieuwe cyclus mag niet dezelfde identiteit hebben als de vorige.')
        now=time_ms(as_of);boundary=now//DAY*DAY
        start=time_ms(context['cycle_start'])
        year=context['bear_year']
        if type(year) is not int or not 2009<=year<=datetime.fromtimestamp(now/1000,timezone.utc).year:
            raise ValueError('Ongeldig of toekomstig bearjaar.')
        bear_start=int(datetime(year,1,1,tzinfo=timezone.utc).timestamp()*1000)
        bear_end=min(int(datetime(year+1,1,1,tzinfo=timezone.utc).timestamp()*1000),boundary)
        if start%DAY or start>=boundary or bear_start>=bear_end:
            raise ValueError('Cyclus/bearjaar heeft nog geen afgesloten dagcandles.')
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
        # Validate precisely the two required windows, not an arbitrary row count.
        for left,right in ((start,boundary),(bear_start,bear_end)):
            if any(t not in rows for t in range(left,right,DAY)):
                raise ValueError('Onvolledige dekking van cyclus of bearjaar.')
        highs=[(t,v[0]) for t,v in rows.items() if start<=t<boundary]
        lows=[(t,v[1]) for t,v in rows.items() if bear_start<=t<bear_end]
        high=max(v for t,v in highs);low=min(v for t,v in lows)
        if low>=high:raise ValueError('Geen bruikbaar ankerbereik.')
        high_at=max(t for t,v in highs if v==high);low_at=max(t for t,v in lows if v==low)
        result=dict(status='calculated',model_version=VERSION,anchor_method=VERSION,
            cycle_id=context['cycle_id'],bear_year=year,classification_basis=context['classification_basis'],
            high=high,low=low,high_at=iso(high_at),low_at=iso(low_at),
            cycle_start=iso(start),cycle_through=iso(boundary),
            bear_from=iso(bear_start),bear_through=iso(bear_end),
            source_timeframe='1d',same_anchors_for_all_horizons=True,
            history_from=iso(min(start,bear_start)),history_to=iso(boundary),
            history_candles=len(rows),high_at_history_boundary=high_at==start,
            bottom_confirmed=False,cycle_extremes_verified=False,
            reference_market='bitget/BTCUSDT/USDT-FUTURES',unit='USDT',
            observed_at=source['observed_at'],calculated_at=as_of,
            reason='Bull: laagste gemeten koers van het expliciet gekozen bearjaar. Bear: hoogste gemeten koers sinds het expliciete cyclusbegin. Identificatie van de fase is een onderbouwde keuze, geen zekerheid.',
            evidence=context)
        identity=json.dumps({k:result[k] for k in ('model_version','cycle_id','bear_year','cycle_start','high','low','high_at','low_at')},sort_keys=True,separators=(',',':'),allow_nan=False)
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

"""Observed high followed by low from available contiguous native history.

Candidates only: source coverage does not establish a cycle ATH or final bottom.
Exclude the native confirmation candle and same-candle high/low ordering.
"""
try:
    from .market_scenarios import iso
    from .native_timeframe_candles import PERIOD_MS
except ImportError:
    from market_scenarios import iso
    from native_timeframe_candles import PERIOD_MS

VERSION='available_history_high_then_low_v1'


def build(rows, timeframe):
    prior=rows[:-1]
    unavailable=dict(status='unavailable',model_version=VERSION,
        reason='Geen afzonderlijke low-candle na de waargenomen top; rangeankers blijven herkenbaar als terugval beschikbaar.')
    if len(prior)<23:
        return unavailable
    step=PERIOD_MS[timeframe]
    if any(b['open_time_ms']-a['open_time_ms'] != step for a,b in zip(prior,prior[1:])):
        return dict(unavailable,reason='Gaten in ankerhistorie; geen historisch anker afleiden.')
    high=max(c['high'] for c in prior)
    # Equal highs on a later candle restart the candidate decline.
    top=max(i for i,c in enumerate(prior) if c['high']==high)
    after=prior[top+1:]
    if not after:
        return unavailable
    low=min(c['low'] for c in after)
    bottom=max(c['open_time_ms'] for c in after if c['low']==low)
    if low>=high:
        return unavailable
    return dict(status='calculated',model_version=VERSION,anchor_method=VERSION,
        high=high,low=low,high_at=iso(prior[top]['open_time_ms']),low_at=iso(bottom),
        direction='down',scale='linear',source_timeframe=timeframe,
        history_from=iso(prior[0]['open_time_ms']),history_to=iso(prior[-1]['open_time_ms']+step),
        history_candles=len(prior),candles_after_high=len(after),
        evidence=[{k:c[k] for k in ('open_time_ms','high','low')} for c in prior],
        high_at_history_boundary=top==0,cycle_extremes_verified=False,
        bottom_confirmed=False,confirmation_candle_excluded=True,
        reason='Hoogste high in beschikbare afgesloten historie, gevolgd door de laagste low op een latere candle. Geen bewezen cyclus-ATH of definitieve bodem.')


def validate(candidate, timeframe):
    if candidate.get('status')!='calculated':
        return True
    evidence=candidate.get('evidence')
    if not isinstance(evidence,list) or len(evidence)<23:
        raise ValueError('missing anchor evidence')
    if build(evidence+[{}],timeframe)!=candidate:
        raise ValueError('anchor disagrees with recorded evidence')
    return True

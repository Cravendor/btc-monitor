"""Read existing public monitor reports as dated context, not a news score."""
import json
from pathlib import Path
try:
    from .monitor_archive import validate_record
    from .market_scenarios import time_ms
except ImportError:
    from monitor_archive import validate_record
    from market_scenarios import time_ms


def read_context(root,as_of):
    result=[]
    try:
        index=json.loads((Path(root)/'reports/index.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):
        return []
    seen=set()
    # First choose the newest declaration per type, then validate it. No silent old fallback.
    for entry in sorted(index.get('reports',[]),key=lambda x:x.get('reported_at',''),reverse=True):
        kind=entry.get('monitor')
        if kind not in ('daily','market-risk','psychology') or kind in seen: continue
        seen.add(kind)
        try:
            relative=Path(entry['path'])
            if relative.is_absolute() or '..' in relative.parts or relative.parts[:1]!=('reports',): raise ValueError('invalid report path')
            raw=json.loads((Path(root)/relative).read_text(encoding='utf-8'))
            validate_record(raw)
            if raw['monitor']!=kind or raw['reported_at']!=entry['reported_at'] or not 0<=time_ms(as_of)-time_ms(raw['reported_at'])<36*3600000:
                raise ValueError('stale or inconsistent report')
            result.append(dict(monitor=kind,reported_at=raw['reported_at'],path=relative.as_posix(),
                content_sha256=raw['content_sha256'],status='dated_report_only_not_independently_verified_news',
                url='https://github.com/Cravendor/btc-monitor/blob/main/'+relative.as_posix()))
        except (OSError,ValueError,KeyError,TypeError):
            continue
    return result


def render(context):
    from html import escape
    parts=['<section class="panel" style="margin-bottom:24px"><h2>Nieuws en psychologische context</h2><p>De wijzers gebruiken de gevalideerde koers- en sentimentgegevens. Nieuws wordt niet zonder controle tot een getal of onafhankelijke bevestiging gemaakt. Vergelijk de gedateerde monitorrapporten hieronder met de testzone; een nieuw nieuwsfeit kan het scenario veranderen.</p>']
    for x in context or []:
        parts.append('<p><a href="'+escape(x['url'],quote=True)+'">'+escape(x['monitor'])+'</a> · <time>'+escape(x['reported_at'])+'</time>. Oorspronkelijk marktverslag; nieuwsfeiten niet opnieuw onafhankelijk geverifieerd door deze pagina.</p>')
    if not context: parts.append('<p>Actuele geverifieerde nieuws-/psychologiecontext ONTBREEKT. De technische wijzers worden daardoor niet als volledige nieuwsgewogen analyse gepresenteerd.</p>')
    return ''.join(parts)+'</section>'

"""Public operational evidence, not a remote DSM process controller."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.market_scenarios import time_ms, iso

WORKFLOWS = [
    dict(id='pages', name='Dashboard publiceren', path='pages.yml', max_age_seconds=7200),
    dict(id='health', name='Meetactualiteit controleren', path='collector-health.yml', max_age_seconds=5400),
    dict(id='archive', name='4H-historie archiveren', path='btc-4h-history-archive.yml', max_age_seconds=5400),
    dict(id='daily', name='Meerjarige daghistorie bijwerken', path='cycle-history.yml', max_age_seconds=100800),
    dict(id='fallback', name='Handmatige GitHub-reserve', path='btc.yml', max_age_seconds=None),
    dict(id='reports', name='Monitorrapporten archiveren', path='archive-bias.yml', max_age_seconds=None),
]


def item(key, name, state, label, detail, evidence_at=None, expires_at=None):
    return dict(id=key, name=name, state=state, label=label, detail=detail,
                evidence_at=evidence_at, expires_at=expires_at, system='NAS / opgeslagen bewijs')


def fresh(value, now, seconds):
    stamp = time_ms(value)
    if stamp > now + 60000:
        raise ValueError('future evidence')
    return stamp, now - stamp <= seconds*1000


def build(feed, health, as_of, execution_root="data/task-executions"):
    now = time_ms(as_of)
    health = health if isinstance(health, dict) else {}
    rows = []
    # First NAS record in the newest-first feed, including a failed one. Never
    # search backwards for an older green observation when the latest is bad.
    measurements = feed.get('measurements', []) if isinstance(feed, dict) else []
    if not isinstance(measurements, list):
        measurements = []
    nas = next((m for m in measurements if isinstance(m, dict) and m.get('collection_source') == 'nas'), {})
    observed = nas.get('finished_at')
    identity = tuple(nas.get(k) for k in ('exchange', 'market', 'symbol'))
    try:
        if identity != ('bitget', 'USDT-FUTURES', 'BTCUSDT'):
            raise ValueError('wrong source')
        at, recent = fresh(observed, now, 2700)
        expiry = iso(at+2700000)
        state, label = ('good', 'Recente upload') if recent else ('attention', 'Upload verouderd')
        if nas.get('status') == 'error':
            state, label = 'error', 'Laatste meting mislukt'
        elif nas.get('status') != 'ok':
            state, label = 'attention', 'Bronnen deels beschikbaar'
        rows.append(item('nas', 'BTC NAS Collect Publish', state, label,
                         'Nieuwste NAS-meting is op GitHub opgeslagen. Normaal elk halfuur; na 45 minuten aandacht. '
                         'Dit is uploadbewijs, geen rechtstreekse DSM-procescontrole.', observed, expiry))
    except (ValueError, TypeError, OverflowError):
        at, expiry = None, None
        rows.append(item('nas', 'BTC NAS Collect Publish', 'unknown', 'Geen geldig uploadbewijs',
                         'De recente feed bevat geen bruikbare NAS-meting. Een GitHub-reservemeting vervangt dit bewijs niet.'))
    cvd = nas.get('cvd_4h', {})
    markets = cvd.get('markets', {}) if isinstance(cvd, dict) else {}
    for market, name in [('spot', 'CVD-collector · spot'), ('usdt_futures', 'CVD-collector · futures')]:
        source = markets.get(market, {}) if isinstance(markets, dict) else {}
        trade_at = source.get('latest_journal_trade_at') if isinstance(source, dict) else None
        state, label = 'unknown', 'Geen recent procesbewijs'
        detail = 'Geen directe procescontrole. De laatste journaltrade wordt beoordeeld bij de NAS-meting, niet als live heartbeat.'
        try:
            if at is None:
                raise ValueError('no valid NAS record')
            if (cvd.get('exchange'), cvd.get('symbol')) != ('bitget', 'BTCUSDT'):
                raise ValueError('wrong CVD identity')
            if tuple(source.get(k) for k in ('exchange', 'symbol', 'market')) != ('bitget', 'BTCUSDT', market):
                raise ValueError('wrong journal market')
            trade, trade_recent = fresh(trade_at, at, 300)
            if not trade_recent or now-at > 2700000:
                state, label = 'attention', 'Tradebewijs verouderd'
            else:
                state, label = 'good', 'Recente trades bij meting'
        except (ValueError, TypeError, AttributeError, OverflowError):
            pass
        rows.append(item('cvd-'+market, name, state, label, detail,
                         trade_at if state != 'unknown' else None, expiry))
    try:
        if health.get('schema_version') != 3 or health.get('status') not in ('current', 'stale'):
            raise ValueError('invalid health contract')
        checked, recent = fresh(health['checked_at'], now, 5400)
        measured, current = fresh(health['last_snapshot_at'], now, 3600)
        if measured > checked+60000:
            raise ValueError('inconsistent health')
        state, label = ('good', 'Recente meting bevestigd') if recent and current and health['status']=='current' else ('attention', 'Actualiteitsbewijs verouderd')
        rows.append(item('snapshot-health', 'Opgeslagen marktmetingen', state, label,
                         'Controleert de nieuwste opgeslagen meting uit NAS of reserve. Dit zegt niet dat alle bronnen volledig zijn '
                         'of dat alle halfuurmetingen aanwezig waren.', health['last_snapshot_at'],
                         iso(min(checked+5400000, measured+3600000))))
    except (ValueError, TypeError, KeyError, OverflowError):
        rows.append(item('snapshot-health', 'Opgeslagen marktmetingen', 'unknown', 'Geen geldig actualiteitsbewijs',
                         'De actualiteitscontrole ontbreekt of is ongeldig.'))
    from scripts.analysis_quality import assess as assess_quality
    latest = measurements[0] if measurements else {}
    quality = assess_quality(latest, as_of)
    quality_state = 'unknown' if not latest else ('good' if quality['status']=='ready_for_scoped_report' else 'attention')
    rows.append(item('analysis-quality', 'Datakwaliteit en verwerking', quality_state,
                     'Gecontroleerd voor beperkte scope' if quality_state=='good' else
                     ('Onderdelen afgekeurd' if latest else 'Geen kwaliteitsbewijs'),
                     'Prijsstructuur: '+quality['price_structure']+'; Bitget-intervaldelta: '+
                     quality['bitget_interval_delta']+'. '+
                     ' '.join(i['code']+': '+i['action'] for i in quality['issues']),
                     latest.get('finished_at') if isinstance(latest,dict) else None,
                     quality['valid_until'] if latest else None))
    report_state, report_label = 'unknown', 'Nog geen rapportcontrole'
    findings = (health.get('analysis_quality') or {}).get('report_findings')
    if isinstance(findings,list):
        try:
            checked, recent = fresh(health['checked_at'],now,5400)
            report_state = 'good' if recent and not findings else 'attention'
            report_label = ('Geen gevonden tekstconflicten' if report_state=='good' else
                            'Rapportcontrole vraagt opvolging')
        except (ValueError,TypeError,KeyError,OverflowError):
            pass
    rows.append(item('report-quality','Rapportconsistentie',report_state,report_label,
                     'Controle op herkenbare tegenstrijdigheden in oorspronkelijke rapporten; '
                     'geen volledige automatische factcheck. '+
                     (' '.join(x.get('code','') for x in findings if isinstance(x,dict)) if isinstance(findings,list) else ''),
                     health.get('checked_at') if findings is not None else None,
                     iso(checked+5400000) if report_state!='unknown' else None))
    from scripts.task_execution import read_items
    rows.extend(read_items(execution_root, as_of))
    return dict(schema_version=1, generated_at=as_of, items=rows, workflows=WORKFLOWS,
                repository='Cravendor/btc-monitor', source_scope='public_operational_evidence')


def load(path):
    try:
        value = json.loads(Path(path).read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def run(feed_path, health_path, destination, as_of=None):
    as_of = as_of or datetime.now(timezone.utc).isoformat()
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    report = build(load(feed_path), load(health_path), as_of, Path(feed_path).parent / "task-executions")
    (folder/'btc-status.json').write_text(json.dumps(report, ensure_ascii=False, allow_nan=False)+'\n')
    (folder/'btc-status.html').write_text(Path('web/status.html').read_text())
    for name in ('status.mjs', 'status.css'):
        (folder/name).write_text(Path('web', name).read_text())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feed', nargs='?', default='data/latest.json')
    parser.add_argument('health', nargs='?', default='data/collector-health.json')
    parser.add_argument('destination', nargs='?', default='_site')
    args = parser.parse_args()
    run(args.feed, args.health, args.destination)

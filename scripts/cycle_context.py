"""Read-only archive adapter; explicit reviewed configuration controls activation."""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .cycle_history import load, PATH as HISTORY_PATH, DAY
    from .cycle_anchor_policy import select
    from .market_scenarios import time_ms, iso
except ImportError:
    from cycle_history import load, PATH as HISTORY_PATH, DAY
    from cycle_anchor_policy import select
    from market_scenarios import time_ms, iso

CONFIG_PATH = 'config/cycle_anchors.json'
VERSION = 'archive_cycle_context_v1'
CONFIG_FIELDS = ('cycle_id', 'previous_cycle_id', 'previous_cycle_peak_at',
                 'phase', 'classification_basis')


def build(history_path, config_path, as_of):
    """Return a compact review plus optional original context, without any I/O writes.

    A failed active configuration deliberately retains an unavailable context.
    That prevents the scenario layer silently falling back to range anchors.
    Local validation time is distinct from historical network retrieval time.
    """
    review = dict(status='unavailable', model_version=VERSION, checked_at=as_of,
                  activation='unknown', reason='Cyclusconfiguratie of historie ontbreekt of is ongeldig.')
    # Unknown/unreadable configuration is not permission to revert an active policy.
    context = dict(schema_version=1, status='unavailable')
    try:
        config = json.loads(Path(config_path).read_text())
        if not isinstance(config, dict):
            raise ValueError('Cyclusconfiguratie moet een object zijn.')
        state = config.get('status')
        review['activation'] = state
        if state == 'active':
            # Keep this sentinel even when validation below fails.
            context = dict(schema_version=1, status='unavailable')
        if config.get('schema_version') != 1 or state not in ('disabled', 'draft', 'active'):
            raise ValueError('Ongeldige cyclusconfiguratieversie of activeringsstatus.')
        if state in ('draft', 'disabled'):
            context = None
        if state == 'disabled':
            return dict(review, status='inactive', reason='Macroankers expliciet uitgeschakeld.'), None
        for key in CONFIG_FIELDS:
            if not isinstance(config.get(key), str) or not config[key].strip():
                raise ValueError('Cyclusconfiguratie mist ' + key + '.')
        if config['cycle_id'] == config['previous_cycle_id']:
            raise ValueError('Vorige en huidige cyclus moeten verschillende identiteiten hebben.')
        if not isinstance(config.get('reference_basis'), str) or not config['reference_basis'].strip():
            raise ValueError('Onderbouwing voor de vorige cyclustop ontbreekt.')
        now = time_ms(as_of)
        boundary = now // DAY * DAY
        try:
            rows, pages = load(history_path, boundary)
        except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError):
            raise ValueError('Historisch archief ontbreekt of faalt bron- en checksumcontrole.') from None
        previous = time_ms(config['previous_cycle_peak_at'])
        required = range(previous, boundary, DAY)
        if previous < 0 or previous % DAY or previous >= boundary - DAY:
            raise ValueError('Vorige cyclustop is geen bruikbare historische UTC-dag.')
        if len(required) > 6000:
            raise ValueError('Cyclusvenster overschrijdt de ondersteunde historie.')
        missing = [t for t in required if t not in rows]
        if missing:
            review.update(missing_days=len(missing), first_missing_at=iso(missing[0]))
            raise ValueError('Onvolledige daghistorie vanaf de gekozen vorige cyclustop.')
        # Bind the reviewed prior peak to a complete explicit reference window.
        start = time_ms(config['previous_peak_window_from'])
        end = time_ms(config['previous_peak_window_through'])
        if start < 0 or start % DAY or end % DAY or not start <= previous < end <= boundary:
            raise ValueError('Ongeldig referentievenster voor vorige cyclustop.')
        if (end-start)//DAY > 6000 or any(t not in rows for t in range(start, end, DAY)):
            raise ValueError('Onvolledig referentievenster voor vorige cyclustop.')
        peak = max(rows[t]['high'] for t in range(start, end, DAY))
        first_peak = next(t for t in range(start, end, DAY) if rows[t]['high'] == peak)
        if previous != first_peak:
            raise ValueError('Gekozen vorige cyclustop wijkt af van de hoogste koers in het referentievenster.')
        fields = ('open_time_ms', 'open', 'high', 'low', 'close')
        candles = [{k: rows[t][k] for k in fields} for t in required]
        provenance = dict(
            archive_content_sha256=hashlib.sha256(json.dumps(
                [rows[t] for t in sorted(rows)], sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            config_sha256=hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            validation='local_archive_only', validated_at=as_of,
            previous_peak_window_from=iso(start), previous_peak_window_through=iso(end),
            reference_basis=config['reference_basis'],
            retrieval_pages=[p for p in pages if time_ms(p['start']) < boundary and time_ms(p['end']) > min(start, previous)])
        candidate = dict(schema_version=1, status='active', **{k: config[k] for k in CONFIG_FIELDS},
                         source=dict(status='ok', exchange='bitget', market='USDT-FUTURES', symbol='BTCUSDT',
                                     interval='1d', closed_only=True, observed_at=as_of,
                                     observation_kind='local_archive_validation', provenance=provenance, candles=candles))
        anchors = select(candidate, as_of)
        if anchors['status'] != 'calculated':
            raise ValueError(anchors['reason'])
        review.update(status='ready', reason='Kandidaatankers gecontroleerd; ' +
                      ('actieve configuratie.' if state == 'active' else 'nog niet geactiveerd.'),
                      configuration=config, provenance=provenance,
                      anchors={k: v for k, v in anchors.items() if k != 'evidence'})
        if state == 'active':
            context = candidate
    except ValueError as exc:
        review['reason'] = str(exc) if not isinstance(exc, json.JSONDecodeError) else 'Cyclusconfiguratie is onleesbaar.'
        if context is not None:
            context['reason'] = review['reason']
    except (KeyError, TypeError, AttributeError, OSError, OverflowError):
        # Generic diagnostics avoid leaking local paths or arbitrary file contents.
        if context is not None:
            context['reason'] = review['reason']
    return review, context


def attach(record, history_path=HISTORY_PATH, config_path=CONFIG_PATH):
    review, context = build(history_path, config_path, record['finished_at'])
    record['cycle_anchor_review'] = review
    if context is not None:
        record['cycle_anchor_context'] = context


def render(feed):
    from html import escape
    review = (feed.get('measurements') or [{}])[0].get('cycle_anchor_review')
    if not review:
        return ''
    esc = lambda value: escape(str(value), quote=True)
    text = '<p>' + esc(review.get('reason')) + '</p>'
    anchors = review.get('anchors', {})
    if review.get('status') == 'ready':
        text += ('<p>Beoordeeld bij meting: ' + esc(review.get('checked_at')) +
                 '. Fasekeuze: ' + esc(anchors.get('phase')) + '.</p>' +
                 '<p>Bullvertrekpunt: ' + esc(anchors.get('low')) + ' USDT · ' + esc(anchors.get('low_at')) +
                 '<br>Bearvertrekpunt: ' + esc(anchors.get('high')) + ' USDT · ' + esc(anchors.get('high_at')) +
                 '.</p><p>' + esc(anchors.get('classification_basis')) + '</p>')
    return ('<details><summary>Controle macroankers · ' + esc(review.get('activation')) +
            '</summary>' + text + '<p>Lokale controle van opgeslagen dagcandles; geen nieuwe API-meting. '
            'Een kandidaatlow bevestigt geen bodem en een gemeten high geen voltooide cyclus.</p></details>')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--history', default=HISTORY_PATH)
    p.add_argument('--config', default=CONFIG_PATH)
    p.add_argument('--as-of', required=True)
    args = p.parse_args()
    review, unused = build(args.history, args.config, args.as_of)
    print(json.dumps(review, indent=2, allow_nan=False))
    return 0 if review['status'] in ('ready', 'inactive') else 1


if __name__ == '__main__':
    raise SystemExit(main())

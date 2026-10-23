"""Observed archive coverage, never a claim about actual workflow executions."""
from datetime import timedelta
from scripts.signal_outcome_validation import parse_time

INTERVAL_SECONDS = 1800


def observations(records, end=None):
    """One stored observation per aware UTC timestamp; ignore future/malformed rows."""
    unique = {}
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get('signals'), dict):
            continue
        stamp = parse_time(row.get('updated_at'))
        if stamp is not None and (end is None or stamp <= end):
            unique.setdefault(stamp, row)
    return sorted(unique.items())


def coverage(records, end, hours=24):
    """Partition (start, end] into half-hour bins, including both boundary gaps.

    Bins wholly before the first retained observation have unknown history.
    Later empty bins are missing stored measurements, NOT proven failed jobs.
    Extra/manual runs in one bin never improve interval coverage.
    """
    if end.tzinfo is None or hours <= 0 or hours * 3600 % INTERVAL_SECONDS:
        raise ValueError('aware end and positive half-hour window required')
    rows = observations(records, end)
    start = end - timedelta(hours=hours)
    first = rows[0][0] if rows else None
    stamps = [t for t, _ in rows if start < t <= end]
    expected = int(hours * 3600 // INTERVAL_SECONDS)
    # Right-closed bins: a point at end belongs to the last bin.
    occupied = {expected - 1 - int((end - t).total_seconds() // INTERVAL_SECONDS)
                for t in stamps}
    unknown = sum(first is None or start + timedelta(seconds=(i + 1) * INTERVAL_SECONDS) < first
                  for i in range(expected))
    gaps = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
    boundaries = [start, *stamps, end]
    max_gap = max((b - a).total_seconds() for a, b in zip(boundaries, boundaries[1:]))
    missing = expected - unknown - len(occupied)
    return {
        'window_start': start.isoformat(), 'window_end': end.isoformat(),
        'first_retained_at': first.isoformat() if first else None,
        'interval_seconds': INTERVAL_SECONDS, 'expected_snapshots': expected,
        'observed_snapshots': len(stamps), 'observed_intervals': len(occupied),
        'history_unavailable_intervals': unknown, 'missing_measurement_intervals': missing,
        'coverage_percent': round(100 * len(occupied) / expected, 1),
        'max_observed_gap_seconds': round(max(gaps)) if gaps else None,
        'max_window_gap_seconds': round(max_gap),
        'status': ('history_unavailable' if unknown == expected else
                   'gaps_detected' if missing else 'partial_history' if unknown else 'complete'),
    }


def coverage_html(report):
    """Render schema-3 coverage only; older count-based reports cannot be reinterpreted."""
    from html import escape
    if not isinstance(report, dict):
        return '<p>Dekking ONTBREEKT — geen tijdvakrapport beschikbaar.</p>'
    keys = ('expected_snapshots', 'observed_intervals', 'history_unavailable_intervals',
            'missing_measurement_intervals')
    values = [report.get(k) for k in keys]
    if (any(type(v) is not int or v < 0 for v in values) or
            not values[0] or sum(values[1:]) != values[0]):
        return '<p>Dekking ONTBREEKT — nieuw tijdvakrapport vereist.</p>'
    expected, observed, unknown, missing = values
    return (f'<p>{observed}/{expected} tijdvakken met een opgeslagen meting '
            f'({100 * observed / expected:.1f}%). '
            f'Geschiedenis ontbreekt: {unknown}. Geen opgeslagen meting na archiefstart: {missing}.</p>'
            '<p>Elk tijdvak duurt 30 minuten. Extra runs tellen eenmaal. '
            'Vóór de eerste bewaarde meting is de geschiedenis onbekend; latere lege tijdvakken '
            'zijn mogelijke gemiste collectormetingen, geen bewijs van een mislukte run. '
            'Een opgeslagen foutmeting telt als aanwezigheid, niet als geldig signaal.</p>'
            '<p>Venster (UTC): ' + escape(str(report.get('window_start'))) + ' → ' +
            escape(str(report.get('window_end'))) + '</p>')

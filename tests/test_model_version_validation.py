import unittest
from datetime import datetime, timezone, timedelta
from scripts.signal_outcome_validation import evaluate, evaluate_models, model_versions
from scripts.signal_statistics import descriptive_confidence
from scripts.timeframe_history_dashboard import outcome_html, outcome_tables, chart_html, render


def row(stamp, model='v1', grade='bullish', value=100, row_model=None):
    return {'updated_at': (stamp + timedelta(minutes=1)).isoformat(),
            'model_version': row_model,
            'signals': {'5m': {'status': 'ok', 'grade': grade, 'close_price': value,
                               'candle_closed_at': stamp.isoformat(), 'model_version': model}}}


class ModelVersionTests(unittest.TestCase):
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)

    def samples(self, number, model, offset=0):
        rows = []
        for i in range(number):
            t = self.start + timedelta(hours=2 * (i + offset))
            rows += [row(t, model), row(t + timedelta(hours=1), model, 'neutral', 110)]
        return rows

    def test_versions_have_separate_denominators(self):
        rows = self.samples(2, 'v1') + self.samples(3, 'v2', 2)
        groups = evaluate_models(rows, (1,))
        self.assertEqual(groups['v1'][1]['5m']['bullish']['evaluated'], 2)
        self.assertEqual(groups['v2'][1]['5m']['bullish']['evaluated'], 3)

    def test_a_later_model_can_supply_price_without_relabelling_original(self):
        rows = [row(self.start, 'old', 'bearish'),
                row(self.start + timedelta(hours=1), 'new', 'neutral', 110)]
        stats = evaluate_models(rows, (1,))['old'][1]['5m']['bearish']
        self.assertEqual(stats['opposite_direction'], 1)
        self.assertEqual(evaluate_models(rows, (1,))['new'][1]['5m']['bearish']['total_signals'], 0)

    def test_conflicting_price_in_other_version_still_invalidates_candle(self):
        rows = self.samples(1, 'v1') + [row(self.start, 'v2', 'neutral', 101)]
        s = evaluate_models(rows, (1,))['v1'][1]['5m']['bullish']
        self.assertEqual(s['excluded'], 1)
        self.assertEqual(s['evaluated'], 0)

    def test_same_candle_opposite_labels_in_distinct_models_are_not_label_conflicts(self):
        rows = [row(self.start, 'v1'), row(self.start, 'v2', 'bearish'),
                row(self.start + timedelta(hours=1), 'v2', 'neutral', 110)]
        groups = evaluate_models(rows, (1,))
        self.assertEqual(groups['v1'][1]['5m']['bullish']['confirmed_direction'], 1)
        self.assertEqual(groups['v2'][1]['5m']['bearish']['opposite_direction'], 1)

    def test_unknown_model_never_becomes_current(self):
        rows = [row(self.start, None), row(self.start, 'known')]
        self.assertEqual(model_versions(rows), ['known'])
        self.assertEqual(evaluate_models(rows, (1,))['known'][1]['5m']['bullish']['total_signals'], 1)

    def test_record_level_version_fallback_and_signal_precedence(self):
        rows = [row(self.start, None, row_model='fallback'),
                row(self.start, 'explicit', row_model='ignored')]
        self.assertEqual(model_versions(rows), ['explicit', 'fallback'])

    def test_invalid_versions_and_future_candles_not_discovered(self):
        rows = [row(self.start, True), row(self.start, '   '), None]
        future = row(self.start, 'future')
        future['updated_at'] = (self.start - timedelta(minutes=1)).isoformat()
        self.assertEqual(model_versions(rows + [future]), [])

    def test_six_plus_six_does_not_unlock_match_percentage(self):
        rows = self.samples(6, 'v1') + self.samples(6, 'v2', 6)
        self.assertEqual(evaluate(rows, 1)['5m']['evaluated'], 12)
        for model, groups in evaluate_models(rows, (1,)).items():
            self.assertEqual(groups[1]['5m']['bullish']['evaluated'], 6)
            self.assertNotIn('<td>100.0%</td>', outcome_tables(groups))

    def test_twenty_plus_twenty_does_not_unlock_wilson_interval(self):
        rows = self.samples(20, 'v1') + self.samples(20, 'v2', 20)
        self.assertEqual(evaluate(rows, 1)['5m']['evaluated'], 40)
        for groups in evaluate_models(rows, (1,)).values():
            s = groups[1]['5m']['bullish']
            self.assertIsNone(descriptive_confidence(s['confirmed_direction'], s['evaluated'])['interval'])
        thirty = evaluate_models(self.samples(30, 'v3'), (1,))['v3'][1]['5m']['bullish']
        self.assertIsNotNone(descriptive_confidence(thirty['confirmed_direction'], thirty['evaluated'])['interval'])

    def test_model_names_are_escaped_and_empty_history_explicit(self):
        model = '<script>alert(1)</script>'
        page = outcome_html(self.samples(1, model))
        self.assertNotIn(model, page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('ONVOLDOENDE DATA', outcome_html([]))

    def test_chart_stops_at_model_boundary(self):
        rows = [row(self.start), row(self.start + timedelta(minutes=30), 'v2')]
        self.assertNotIn('<polyline', chart_html(rows))
        rows[1]['signals']['5m']['model_version'] = 'v1'
        self.assertIn('<polyline', chart_html(rows))

    def test_history_lists_mixed_model_versions_without_changing_labels(self):
        rows = self.samples(1, 'v1')
        rows[0]['signals']['1h'] = dict(rows[0]['signals']['5m'], model_version='v2')
        page = render(rows)
        self.assertIn('<th>Modelversies</th>', page)
        self.assertIn('v1, v2', page)
        self.assertIn('Modelversie: v1', page)
        self.assertIn('Modelversie: v2', page)

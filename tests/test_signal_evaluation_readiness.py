import unittest
from scripts.signal_outcome_validation import evaluate, evaluate_horizons
from scripts.timeframe_history_dashboard import outcome_html


def record(closed='2026-10-20T00:00:00Z', value=100, grade='bullish',
           observed='2026-10-20T00:05:00Z', tf='5m', model='v1'):
    return {'updated_at': observed, 'signals': {tf: {
        'status': 'ok', 'grade': grade, 'candle_closed_at': closed,
        'close_price': value, 'model_version': model}}}


class EvaluationReadinessTests(unittest.TestCase):
    def stats(self, records):
        return evaluate(records, horizon_hours=1)['5m']

    def test_missing_initial_price_is_counted_once(self):
        rows = [record(value=None)] * 4
        s = self.stats(rows)
        self.assertEqual(s['missing_initial_price'], 1)
        self.assertEqual(s['total_signals'], 1)
        self.assertEqual(s['evaluated'], 0)

    def test_invalid_initial_prices_are_not_zero(self):
        for value in (None, 0, -1, True, 'NaN', 'inf', 'bad'):
            with self.subTest(value=value):
                self.assertEqual(self.stats([record(value=value)])['missing_initial_price'], 1)

    def test_not_yet_at_horizon(self):
        s = self.stats([record()])
        self.assertEqual(s['awaiting_horizon'], 1)
        self.assertEqual(s['missing_forward_price'], 0)
        self.assertEqual(s['pending_forward_price'], 1)

    def test_archive_time_not_machine_clock(self):
        # Old archive dates stay pending even when rendered months later.
        self.assertEqual(self.stats([record()])['awaiting_horizon'], 1)

    def test_window_boundary_is_still_open(self):
        for when in ('2026-10-20T01:00:00Z', '2026-10-20T01:30:00Z'):
            with self.subTest(when=when):
                rows = [record(), {'updated_at': when, 'signals': {}}]
                self.assertEqual(self.stats(rows)['awaiting_price_window'], 1)

    def test_missing_after_full_tolerance(self):
        rows = [record(), {'updated_at': '2026-10-20T01:30:01Z', 'signals': {}}]
        self.assertEqual(self.stats(rows)['missing_forward_price'], 1)
        self.assertEqual(self.stats(rows)['awaiting_price_window'], 0)

    def test_unknown_archive_clock_explicit(self):
        for when in (None, 'invalid', '2026-10-20T00:05:00'):
            with self.subTest(when=when):
                self.assertEqual(self.stats([record(observed=when)])['unknown_observation_time'], 1)

    def test_valid_forward_price_at_tolerance_edge(self):
        rows = [record(), record('2026-10-20T01:30:00Z', 105, 'neutral',
                                 '2026-10-20T01:31:00Z')]
        self.assertEqual(self.stats(rows)['confirmed_direction'], 1)
        rows[1]['signals']['5m']['candle_closed_at'] = '2026-10-20T01:30:01Z'
        self.assertEqual(self.stats(rows)['missing_forward_price'], 1)

    def test_incompatible_horizon_is_not_waiting_for_impossible_candle(self):
        s = evaluate([record(tf='4h')], horizon_hours=1)['4h']
        self.assertEqual(s['unsupported_horizon'], 1)
        self.assertEqual(s['pending_forward_price'], 0)
        s = evaluate([record(tf='4h')], horizon_hours=4)['4h']
        self.assertEqual(s['unsupported_horizon'], 0)
        self.assertEqual(s['awaiting_horizon'], 1)

    def test_grade_split_retains_conflict_exclusions(self):
        rows = [record(grade='bullish'), record(grade='bearish'),
                record('2026-10-20T01:00:00Z', 105, 'neutral', '2026-10-20T01:05:00Z')]
        groups = evaluate_horizons(rows, (1,))[1]['5m']
        for grade in ('bullish', 'bearish'):
            self.assertEqual(groups[grade]['excluded'], 1)
            self.assertEqual(groups[grade]['evaluated'], 0)

    def test_neutral_price_from_another_model_does_not_change_original_grade(self):
        rows = [record(), record('2026-10-20T01:00:00Z', 105, 'neutral',
                                 '2026-10-20T01:05:00Z', model='v2')]
        self.assertEqual(evaluate_horizons(rows, (1,))[1]['5m']['bullish']['evaluated'], 1)

    def test_conflicting_forward_prices_are_not_resolved_by_input_order(self):
        rows = [record(), record('2026-10-20T01:00:00Z', 105, 'neutral', '2026-10-20T01:05:00Z'),
                record('2026-10-20T01:00:00Z', 95, 'neutral', '2026-10-20T01:35:00Z')]
        self.assertEqual(self.stats(rows)['missing_forward_price'], 1)
        self.assertEqual(self.stats(list(reversed(rows))), self.stats(rows))

    def test_every_unique_signal_has_exactly_one_primary_state(self):
        rows = [record(), record(value=None, model='v2'),
                record('2026-10-19T00:00:00Z', 100),
                record('2026-10-18T00:00:00Z', 100),
                record('2026-10-18T01:00:00Z', 100, 'neutral')]
        s = self.stats(rows)
        self.assertEqual(s['total_signals'], sum(s[k] for k in (
            'evaluated', 'pending_forward_price', 'missing_initial_price',
            'unsupported_horizon', 'excluded')))

    def test_no_price_from_a_candle_after_its_observation_time(self):
        rows = [record(), record('2026-10-20T01:00:00Z', 105, 'neutral',
                                 '2026-10-20T00:30:00Z')]
        self.assertEqual(self.stats(rows)['evaluated'], 0)

    def test_dashboard_explains_states_and_preserves_statistics_caveats(self):
        page = outcome_html([record(value=None)])
        for phrase in ('Startkoers ontbreekt', 'Horizon nog niet bereikt',
                       'Koersvenster nog open', 'Vervolgkoers ontbreekt',
                       'Horizon niet meetbaar', 'laatste opgeslagen observatietijd',
                       'autocorrelatie', 'ONVOLDOENDE DATA'):
            self.assertIn(phrase, page)

import unittest
from datetime import datetime, timezone, timedelta
from scripts.signal_outcome_validation import evaluate, evaluate_models, non_overlapping_keys
from scripts.signal_statistics import descriptive_confidence
from scripts.timeframe_history_dashboard import outcome_html, outcome_tables


class NonOverlapTests(unittest.TestCase):
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)

    def row(self, minutes=0, grade='bullish', value=100, model='v1', tf='5m'):
        stamp = self.start + timedelta(minutes=minutes)
        return {'updated_at': (stamp + timedelta(minutes=1)).isoformat(), 'signals': {tf: {
            'status': 'ok', 'grade': grade, 'model_version': model,
            'candle_closed_at': stamp.isoformat(), 'close_price': value}}}

    def stats(self, rows):
        return evaluate(rows, 1, sample_policy='non_overlapping')['5m']

    def test_exact_closed_boundary_skipped_and_next_point_selected(self):
        keys = [(self.start + timedelta(minutes=m), 'v1') for m in (0, 30, 90, 95)]
        chosen = non_overlapping_keys(keys, timedelta(hours=1), timedelta(minutes=30))
        self.assertEqual(chosen, {keys[0], keys[3]})

    def test_selection_is_independent_of_record_order_and_duplicates(self):
        rows = [self.row(m) for m in (0, 5, 90, 95, 180, 190)]
        self.assertEqual(self.stats(rows), self.stats(list(reversed(rows)) + rows))
        self.assertEqual(self.stats(rows)['total_signals'], 3)

    def test_grade_split_does_not_restart_selection(self):
        rows = [self.row(0, 'bullish'), self.row(5, 'bearish')]
        groups = evaluate_models(rows, (1,), sample_policy='non_overlapping')['v1'][1]['5m']
        self.assertEqual(groups['bullish']['total_signals'], 1)
        self.assertEqual(groups['bearish']['total_signals'], 0)
        self.assertEqual(groups['bearish']['overlap_skipped'], 1)

    def test_missing_start_price_still_reserves_period(self):
        rows = [self.row(0, value=None), self.row(5), self.row(65, 'neutral', 110)]
        s = self.stats(rows)
        self.assertEqual(s['missing_initial_price'], 1)
        self.assertEqual(s['overlap_skipped'], 1)
        self.assertEqual(s['evaluated'], 0)

    def test_label_conflict_still_reserves_period(self):
        rows = [self.row(0, 'bullish'), self.row(0, 'bearish'), self.row(5)]
        s = self.stats(rows)
        self.assertEqual(s['excluded'], 1)
        self.assertEqual(s['overlap_skipped'], 1)

    def test_skipped_signal_keeps_its_forward_price_available(self):
        # The second directional signal is skipped, but its price at the
        # first signal's target remains observed evidence for that first one.
        s = self.stats([self.row(0, value=100), self.row(60, value=110)])
        self.assertEqual(s['confirmed_direction'], 1)
        self.assertEqual(s['overlap_skipped'], 1)

    def test_other_models_and_timeframes_do_not_block_each_other(self):
        rows = [self.row(0, model='v1'), self.row(5, model='v2'), self.row(5, tf='15m')]
        groups = evaluate_models(rows, (1,), sample_policy='non_overlapping')
        self.assertEqual(groups['v1'][1]['5m']['bullish']['total_signals'], 1)
        self.assertEqual(groups['v2'][1]['5m']['bullish']['total_signals'], 1)
        self.assertEqual(groups['v1'][1]['15m']['bullish']['total_signals'], 1)

    def test_neutral_snapshots_supply_prices_without_reserving_periods(self):
        rows = [self.row(0, 'neutral'), self.row(5)]
        s = self.stats(rows)
        self.assertEqual(s['total_signals'], 1)
        self.assertEqual(s['overlap_skipped'], 0)

    def test_each_horizon_gets_its_own_selection(self):
        rows = [self.row(0), self.row(95)]
        groups = evaluate_models(rows, (1, 4), sample_policy='non_overlapping')['v1']
        self.assertEqual(groups[1]['5m']['bullish']['total_signals'], 2)
        self.assertEqual(groups[4]['5m']['bullish']['total_signals'], 1)

    def test_sparse_outcomes_do_not_reuse_full_sample_thresholds(self):
        rows = []
        for m in range(0, 150, 5):
            rows += [self.row(m, value=100+m), self.row(m+60, 'neutral', value=160+m)]
        all_stats = evaluate(rows, 1)['5m']
        self.assertEqual(all_stats['evaluated'], 30)
        spaced = self.stats(rows)
        self.assertEqual(spaced['evaluated'], 2)
        self.assertIsNone(descriptive_confidence(spaced['confirmed_direction'], spaced['evaluated'])['interval'])
        tables = evaluate_models(rows, (1,), sample_policy='non_overlapping')['v1']
        self.assertNotIn('<td>100.0%</td>', outcome_tables(tables))

    def test_primary_and_selection_counts_reconcile(self):
        s = self.stats([self.row(m) for m in (0, 5, 90, 95)])
        self.assertEqual(s['candidate_signals'], s['total_signals'] + s['overlap_skipped'])
        self.assertEqual(s['total_signals'], sum(s[k] for k in (
            'evaluated', 'pending_forward_price', 'missing_initial_price', 'unsupported_horizon', 'excluded')))
        full = evaluate([self.row(0), self.row(5)], 1)['5m']
        self.assertEqual(full['overlap_skipped'], 0)
        self.assertEqual(full['candidate_signals'], full['total_signals'])

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([], sample_policy='best_results')

    def test_dashboard_shows_both_views_and_residual_dependence(self):
        page = outcome_html([self.row()])
        for text in ('Alle unieke signalen', 'Zonder overlappende evaluatieperioden',
                     'Overgeslagen wegens overlap', 'NIET onafhankelijk', 'autocorrelatie'):
            self.assertIn(text, page)

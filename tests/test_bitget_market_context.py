import unittest
from scripts.bitget_market_context import _derivatives_measurement

MARKET = "bitget_USDT-FUTURES_BTCUSDT"


def metric(field, value):
    return {"status": "ok", "observed_at": "2026-10-22T12:00:00Z",
            "data": {field: value}}


class ContextBridgeTests(unittest.TestCase):
    def test_derivatives_extracted(self):
        measurement = {"finished_at": "2026-10-22T12:00:00Z",
                       "metrics": {"funding": metric("fundingRate", "0.0001"),
                                   "open_interest": metric("holdingAmount", "30000")}}
        result = _derivatives_measurement(measurement, MARKET)
        self.assertEqual(result["funding_rate"], 0.0001)
        self.assertEqual(result["open_interest"], 30000)

    def test_missing_metric_is_not_zero(self):
        measurement = {"finished_at": "2026-10-22T12:00:00Z",
                       "metrics": {"funding": metric("fundingRate", "0.0001")}}
        self.assertIsNone(_derivatives_measurement(measurement, MARKET))


if __name__ == "__main__":
    unittest.main()

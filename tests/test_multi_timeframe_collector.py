import unittest
from datetime import datetime, timezone
from scripts.multi_timeframe_collector import collect_native_timeframes
from scripts.native_timeframe_candles import PERIOD_MS


class MultiTimeframeCollectorTests(unittest.TestCase):
    def test_collects_native_intervals(self):
        now = datetime.fromtimestamp(86400000/1000 * 124, timezone.utc)
        def requester(url, transform, bitget):
            self.assertTrue(bitget)
            self.assertIn("granularity=", url)
            tf = next(t for t, g in {
                "5m":"5m", "15m":"15m", "30m":"30m", "1h":"1H",
                "4h":"4H", "1d":"1Dutc", "1w":"1Wutc"}.items() if "granularity="+g in url)
            p = PERIOD_MS[tf]
            offset = 4*86400000 if tf == "1w" else 0
            boundary = (int(now.timestamp()*1000)-offset)//p*p+offset
            if tf == "1w":
                from urllib.parse import parse_qs, urlsplit
                params = parse_qs(urlsplit(url).query)
                start = int(params["startTime"][0])
                end = int(params["endTime"][0])
                rows = [[str(t), "100", "102", "98", "101", "10", "1000"]
                        for t in range(start, end, p)]
            else:
                rows = [[str(boundary - p*(24-i)), "100", "102", "98", "101", "10", "1000"]
                        for i in range(24)]
            return {"status": "ok", "data": transform(rows)}
        result = collect_native_timeframes(now, requester)
        for tf in PERIOD_MS:
            self.assertEqual(result[tf]["signal"]["status"], "provisional")
        self.assertEqual(result["1w"]["signal"]["status"], "provisional")

    def test_failed_api_is_unavailable(self):
        def failed(url, transform, bitget):
            return {"status": "error", "data": None, "error": "offline"}
        result = collect_native_timeframes(datetime.now(timezone.utc), failed)
        self.assertTrue(all(result[tf]["signal"]["status"] == "unavailable"
                            for tf in result))


if __name__ == "__main__":
    unittest.main()

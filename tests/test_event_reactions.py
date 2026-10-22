import unittest
from scripts.event_reactions import event_reactions

EVENT = {"verification": "verified", "released_at": "2026-10-22T12:00:00Z",
         "market": "bitget_spot_btcusdt"}
PRICES = [
    {"market": EVENT["market"], "quality": "verified",
     "observed_at": "2026-10-22T11:59:00Z", "price": 80000},
    {"market": EVENT["market"], "quality": "verified",
     "observed_at": "2026-10-22T13:01:00Z", "price": 80800},
]


class EventReactionTests(unittest.TestCase):
    def test_one_hour_return(self):
        r = event_reactions(EVENT, PRICES)
        self.assertEqual(r["windows"]["1"]["return_pct"], 1.0)
        self.assertEqual(r["windows"]["4"]["status"], "unavailable")

    def test_unconfirmed_meeting_not_used(self):
        r = event_reactions({"verification": "parsed_unconfirmed"}, PRICES)
        self.assertEqual(r["status"], "unavailable")

    def test_cross_market_ignored(self):
        other = [dict(x, market="different_market") for x in PRICES]
        self.assertEqual(event_reactions(EVENT, other)["status"], "unavailable")

    def test_no_future_baseline(self):
        late = [PRICES[1]]
        self.assertEqual(event_reactions(EVENT, late)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()

import unittest
from scripts.fomc_calendar_parser import parse_meetings


class CalendarParserTests(unittest.TestCase):
    def test_year_scoped_dates(self):
        html = "<h3>2027 FOMC Meetings</h3><table><tr><td>Jan 26-27</td></tr><tr><td>Mar 16-17</td></tr></table>"
        events = parse_meetings(html)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["end_date"], "2027-01-27")
        self.assertIsNone(events[0]["release_time_utc"])

    def test_no_year_no_dates(self):
        self.assertEqual(parse_meetings("<td>Jan 26-27</td>"), [])

    def test_invalid_date_excluded(self):
        self.assertEqual(parse_meetings("<h3>2027</h3><td>Feb 30-31</td>"), [])


if __name__ == "__main__":
    unittest.main()

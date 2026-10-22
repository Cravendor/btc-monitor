"""Conservative FOMC date parser for Federal Reserve calendar page.

Only emits a meeting if the official page exposes an explicit year heading and
a date range in the same year section. Manual verification is still recommended.
"""
from html.parser import HTMLParser
import re
from datetime import date

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5,
          "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
          "oct": 10, "nov": 11, "dec": 12}
DATE = re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?\b", re.I)

class CalendarHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.year = None
        self.year_stack = []
        self.heading = None
        self.items = []
        self._capture = None
        self._buf = []
    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3", "h4"):
            self._capture = tag
            self._buf = []
        elif tag in ("td", "th") and self.year is not None:
            self._capture = tag
            self._buf = []
    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)
    def handle_endtag(self, tag):
        if tag != self._capture:
            return
        text = " ".join(self._buf).strip()
        if tag.startswith("h"):
            m = re.search(r"\b(20\d{2})\b", text)
            if m:
                self.year = int(m.group(1))
        elif self.year and text:
            self.items.append((self.year, text))
        self._capture = None
        self._buf = []

def parse_meetings(html):
    parser = CalendarHTML()
    parser.feed(html)
    result, seen = [], set()
    for year, item in parser.items:
        match = DATE.search(item)
        if not match:
            continue
        month = MONTHS[match.group(1)[:3].lower()]
        start_day = int(match.group(2))
        end_day = int(match.group(3) or start_day)
        try:
            start = date(year, month, start_day)
            end = date(year, month, end_day)
        except ValueError:
            continue
        if end < start or (end-start).days > 7:
            continue
        key = (start.isoformat(), end.isoformat())
        if key not in seen:
            seen.add(key)
            result.append({"start_date": key[0], "end_date": key[1],
                           "source": "Federal Reserve FOMC calendar",
                           "verification": "parsed_unconfirmed",
                           "release_time_utc": None})
    return sorted(result, key=lambda x: x["start_date"])

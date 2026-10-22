"""Read-only Federal Reserve FOMC calendar extractor.

Uses only the official Fed calendar page and Python standard library.
Dates are explicitly unverified until a parser matches an official year heading
and meeting date. Does not attempt to infer future dates from patterns.
"""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import json
import re

SOURCE = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())

def fetch_official_page(timeout=15):
    request = Request(SOURCE, headers={"User-Agent": "btc-monitor/1.0 (public research)"})
    with urlopen(request, timeout=timeout) as response:
        return response.read(2_000_000).decode("utf-8", errors="replace")

def extract_page_text(html):
    parser = TextParser()
    parser.feed(html)
    return "\n".join(parser.text)

def source_snapshot(html, fetched_at=None):
    """Store source text for later review, not guessed event dates."""
    stamp = fetched_at or datetime.now(timezone.utc).isoformat()
    text = extract_page_text(html)
    if "FOMC" not in text and "Federal Open Market Committee" not in text:
        raise ValueError("unexpected official calendar response")
    return {"source_url": SOURCE, "retrieved_at": stamp,
            "status": "source_observed_unparsed",
            "events": [], "raw_text_excerpt": text[:20000]}

if __name__ == "__main__":
    print(json.dumps(source_snapshot(fetch_official_page()), ensure_ascii=False, indent=2))

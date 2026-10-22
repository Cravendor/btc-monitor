"""Official-source macro event watchlist (no invented event dates).

This catalog is a source configuration, NOT a live event calendar.
Fetchers must record scheduled/released times from the source itself.
"""
SOURCES = {
    "fomc": {
        "publisher": "Federal Reserve",
        "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "category": "monetary_policy",
        "region": "US",
        "impact_channels": ["rates", "usd", "liquidity", "risk_appetite"],
    },
    "cpi": {
        "publisher": "Bureau of Labor Statistics",
        "url": "https://www.bls.gov/schedule/news_release/cpi.htm",
        "category": "inflation",
        "region": "US",
        "impact_channels": ["rates", "usd", "real_yields"],
    },
    "employment": {
        "publisher": "Bureau of Labor Statistics",
        "url": "https://www.bls.gov/schedule/news_release/empsit.htm",
        "category": "labor",
        "region": "US",
        "impact_channels": ["rates", "usd", "growth"],
    },
    "pce": {
        "publisher": "Bureau of Economic Analysis",
        "url": "https://www.bea.gov/data/personal-consumption-expenditures-price-index",
        "category": "inflation",
        "region": "US",
        "impact_channels": ["rates", "usd", "real_yields"],
    },
    "gdp": {
        "publisher": "Bureau of Economic Analysis",
        "url": "https://www.bea.gov/data/gdp/gross-domestic-product",
        "category": "growth",
        "region": "US",
        "impact_channels": ["growth", "rates", "risk_appetite"],
    },
    "ecb": {
        "publisher": "European Central Bank",
        "url": "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
        "category": "monetary_policy",
        "region": "EU",
        "impact_channels": ["rates", "eurusd", "liquidity"],
    },
}


def configured_sources():
    return [{"key": key, **value} for key, value in SOURCES.items()]


def validate_catalog():
    for key, item in SOURCES.items():
        if not key or not item["url"].startswith("https://"):
            raise ValueError("invalid source")
        if not item["impact_channels"]:
            raise ValueError("missing impact channels")
    return True

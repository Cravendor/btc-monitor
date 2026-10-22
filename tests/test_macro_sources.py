import unittest
from scripts.macro_sources import configured_sources, validate_catalog


class MacroSourcesTests(unittest.TestCase):
    def test_catalog(self):
        self.assertTrue(validate_catalog())
        sources = configured_sources()
        self.assertTrue(any(x["key"] == "fomc" for x in sources))
        self.assertTrue(any(x["key"] == "cpi" for x in sources))

    def test_no_fabricated_dates(self):
        self.assertTrue(all("scheduled_at" not in x for x in configured_sources()))


if __name__ == "__main__":
    unittest.main()

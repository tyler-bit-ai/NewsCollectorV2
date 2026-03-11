import os
import unittest

from collectors.mofa_0404_collector import Mofa0404Collector


@unittest.skipUnless(
    os.getenv("RUN_0404_SMOKE", "").lower() == "true",
    "Set RUN_0404_SMOKE=true to run live 0404 smoke test.",
)
class Mofa0404CollectorSmokeTests(unittest.TestCase):
    def test_live_fetch_returns_list_shape(self):
        collector = Mofa0404Collector(max_pages=1)
        items = collector.collect_today_keyword_posts()

        self.assertIsInstance(items, list)
        if items:
            first = items[0]
            self.assertIn("title", first)
            self.assertIn("link", first)
            self.assertIn("published_date", first)
            self.assertRegex(first["published_date"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()

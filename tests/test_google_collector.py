from datetime import datetime, timezone
import unittest

from collectors.google_collector import GoogleCollector


class GoogleCollectorMetadataTests(unittest.TestCase):
    def setUp(self):
        self.collector = GoogleCollector(
            api_key="test",
            search_engine_id="test",
            debug_mode=False,
        )

    def test_extract_published_datetime_from_metatag(self):
        item = {
            "link": "https://example.com/article",
            "snippet": "Fallback snippet",
            "pagemap": {
                "metatags": [
                    {
                        "article:published_time": "2026-03-30T09:15:00Z",
                    }
                ]
            },
        }

        published, published_raw, freshness_source = self.collector._extract_published_datetime(item)

        self.assertEqual(datetime(2026, 3, 30, 9, 15, tzinfo=timezone.utc), published)
        self.assertEqual("2026-03-30T09:15:00Z", published_raw)
        self.assertEqual("meta:article:published_time", freshness_source)

    def test_extract_published_datetime_from_snippet_prefix(self):
        item = {
            "link": "https://example.com/article",
            "snippet": "Mar 30, 2026 ... Travel eSIM demand accelerates.",
            "pagemap": {},
        }

        published, published_raw, freshness_source = self.collector._extract_published_datetime(item)

        self.assertEqual(datetime(2026, 3, 30, 0, 0, tzinfo=timezone.utc), published)
        self.assertEqual("Mar 30, 2026", published_raw)
        self.assertEqual("snippet_prefix", freshness_source)

    def test_build_article_keeps_quality_metadata(self):
        item = {
            "title": "Travel eSIM demand accelerates",
            "link": "https://news.example.com/article?id=1",
            "snippet": "Mar 30, 2026 ... Travel eSIM demand accelerates.",
            "pagemap": {},
        }

        published, published_raw, freshness_source = self.collector._extract_published_datetime(item)
        article = {
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
            "source": "Google",
            "published": published,
            "published_raw": published_raw,
            "freshness_source": freshness_source,
            "source_domain": self.collector._extract_source_domain(item.get("link")),
            "query": "travel connectivity market",
            "quality_flags": [] if published else ["missing_published_date"],
            "type": "global",
        }

        self.assertEqual("news.example.com", article["source_domain"])
        self.assertEqual("travel connectivity market", article["query"])
        self.assertEqual([], article["quality_flags"])
        self.assertIsNotNone(article["published"])

    def test_missing_date_marks_quality_flag(self):
        item = {
            "title": "Carrier roaming guide",
            "link": "https://carrier.example.com/roaming",
            "snippet": "Business roaming guide and pricing.",
            "pagemap": {},
        }

        published, published_raw, freshness_source = self.collector._extract_published_datetime(item)

        self.assertIsNone(published)
        self.assertEqual("", published_raw)
        self.assertEqual("", freshness_source)
        self.assertEqual("carrier.example.com", self.collector._extract_source_domain(item["link"]))


if __name__ == "__main__":
    unittest.main()

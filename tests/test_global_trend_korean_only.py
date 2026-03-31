import unittest
from collections import Counter
from pathlib import Path
import re

from analyzers.summarizer import Summarizer
from notifiers.email_formatter import EmailFormatter
from notifiers.web_generator import WebGenerator
from utils.helpers import (
    GLOBAL_TREND_SUMMARY_FALLBACK,
    GLOBAL_TREND_TITLE_FALLBACK,
    ensure_global_trend_korean_text,
    inspect_global_trend_translation,
)


HISTORY_DIR = Path(__file__).resolve().parents[1] / "output" / "web" / "history"
GLOBAL_TREND_HISTORY_FILES = (
    "daily_report_20260304_211123.html",
    "daily_report_20260305_095614.html",
    "daily_report_20260306_101015.html",
    "daily_report_20260312_085850.html",
    "daily_report_20260313_102357.html",
    "daily_report_20260320_091427.html",
    "daily_report_20260325_085631.html",
    "daily_report_20260331_142747.html",
)
GLOBAL_TREND_LINK_SECTION_PATTERN = re.compile(
    r"<h2>1\. Global Roaming Trend.*?<ol>(.*?)</ol>",
    re.DOTALL,
)
GLOBAL_TREND_LINK_PATTERN = re.compile(r'<a href="([^"]+)"')
GLOBAL_TREND_PLACEHOLDER_PATTERN = re.compile(r"해외 로밍 동향 기사\(한글 번역 준비중\)")


def load_global_trend_history_baseline():
    """과거 리포트에서 Global Roaming Trend 반복 패턴 기준선을 추출한다."""
    baseline = {}
    repeated_link_counts = Counter()

    for file_name in GLOBAL_TREND_HISTORY_FILES:
        path = HISTORY_DIR / file_name
        content = path.read_text(encoding="utf-8")
        section_match = GLOBAL_TREND_LINK_SECTION_PATTERN.search(content)
        links = []
        if section_match:
            links = GLOBAL_TREND_LINK_PATTERN.findall(section_match.group(1))

        baseline[file_name] = {
            "links": links,
            "placeholder_count": len(GLOBAL_TREND_PLACEHOLDER_PATTERN.findall(content)),
        }
        repeated_link_counts.update(links)

    return baseline, repeated_link_counts


class GlobalTrendKoreanOnlyTests(unittest.TestCase):
    def test_helper_replaces_english_text(self):
        title, summary = ensure_global_trend_korean_text(
            "Global roaming outlook 2026",
            "MVNO roaming market is expanding quickly.",
        )
        self.assertEqual(GLOBAL_TREND_TITLE_FALLBACK, title)
        self.assertEqual(GLOBAL_TREND_SUMMARY_FALLBACK, summary)

    def test_summarizer_postprocess_for_global_trend(self):
        summarizer = Summarizer(api_key="test", base_url="https://api.openai.com/v1", model="gpt-4o-mini")
        items = [
            {"index": 1, "title": "Roaming Market", "summary": "English summary", "link": "https://x"},
            {"index": 2, "title": "한글 제목", "summary": "한글 요약", "link": "https://y"},
        ]
        processed = summarizer._enforce_global_trend_korean_only(items)
        self.assertEqual(GLOBAL_TREND_TITLE_FALLBACK, processed[0]["title"])
        self.assertEqual(GLOBAL_TREND_SUMMARY_FALLBACK, processed[0]["summary"])
        self.assertEqual("full_fallback", processed[0]["translation_status"])
        self.assertIn("non_korean_title", processed[0]["translation_notes"])
        self.assertIn("non_korean_summary", processed[0]["translation_notes"])
        self.assertEqual("한글 제목", processed[1]["title"])
        self.assertEqual("한글 요약", processed[1]["summary"])
        self.assertEqual("translated", processed[1]["translation_status"])
        self.assertEqual([], processed[1]["translation_notes"])

    def test_inspect_global_trend_translation_tracks_partial_fallback(self):
        inspection = inspect_global_trend_translation(
            title="한글 제목",
            summary="English summary only",
        )

        self.assertEqual("한글 제목", inspection["title"])
        self.assertEqual(GLOBAL_TREND_SUMMARY_FALLBACK, inspection["summary"])
        self.assertEqual("partial_fallback", inspection["translation_status"])
        self.assertEqual(["non_korean_summary"], inspection["translation_notes"])

    def test_inspect_global_trend_translation_tracks_missing_fields(self):
        inspection = inspect_global_trend_translation(title="", summary="")

        self.assertEqual(GLOBAL_TREND_TITLE_FALLBACK, inspection["title"])
        self.assertEqual(GLOBAL_TREND_SUMMARY_FALLBACK, inspection["summary"])
        self.assertEqual("full_fallback", inspection["translation_status"])
        self.assertIn("missing_title", inspection["translation_notes"])
        self.assertIn("missing_summary", inspection["translation_notes"])

    def test_email_formatter_masks_global_trend_english(self):
        formatter = EmailFormatter()
        card_html = formatter._render_article_card(
            {"title": "Global trend report", "summary": "English summary", "link": "https://example.com"},
            category_key="global_trend",
        )
        self.assertNotIn("Global trend report", card_html)
        self.assertNotIn("English summary", card_html)
        self.assertIn("한글 번역 준비중", card_html)

    def test_web_generator_masks_global_trend_english(self):
        generator = WebGenerator()
        card_html = generator._render_article_card(
            {"title": "Global trend report", "summary": "English summary", "link": "https://example.com"},
            category_key="global_trend",
        )
        self.assertNotIn("Global trend report", card_html)
        self.assertNotIn("English summary", card_html)
        self.assertIn("한글 번역 준비중", card_html)


    def test_web_generator_external_alerts_section_does_not_use_category_key(self):
        generator = WebGenerator(default_visible_n=1)
        section_html = generator._render_external_alerts_section([
            {
                "title": "Travel advisory",
                "content_one_line": "Notice body",
                "link": "https://example.com/1",
                "board_name": "0404",
            },
            {
                "title": "Entry restriction",
                "content_one_line": "Second notice",
                "link": "https://example.com/2",
                "board_name": "0404",
            },
        ])
        self.assertIn("https://example.com/1", section_html)
        self.assertIn("https://example.com/2", section_html)

    def test_historical_reports_expose_placeholder_baseline(self):
        baseline, _ = load_global_trend_history_baseline()

        expected_placeholder_counts = {
            "daily_report_20260304_211123.html": 0,
            "daily_report_20260305_095614.html": 0,
            "daily_report_20260306_101015.html": 0,
            "daily_report_20260312_085850.html": 7,
            "daily_report_20260313_102357.html": 5,
            "daily_report_20260320_091427.html": 6,
            "daily_report_20260325_085631.html": 5,
            "daily_report_20260331_142747.html": 4,
        }

        self.assertEqual(expected_placeholder_counts, {
            file_name: values["placeholder_count"]
            for file_name, values in baseline.items()
        })

    def test_historical_reports_capture_repeated_links_baseline(self):
        _, repeated_link_counts = load_global_trend_history_baseline()

        self.assertEqual(
            8,
            repeated_link_counts["https://www.ericsson.com/en/blog/2020/9/esim-driving-global-connectivity-in-the-automotive-industry"],
        )
        self.assertEqual(
            8,
            repeated_link_counts["https://www.fortunebusinessinsights.com/industry-reports/embedded-sim-esim-technology-market-100372"],
        )
        self.assertEqual(
            7,
            repeated_link_counts["https://www.weforum.org/stories/2024/12/travel-can-shape-the-future-of-global-connectivity/"],
        )
        self.assertEqual(
            5,
            repeated_link_counts["https://www.orange.com/en/press-release/orange-travel-joins-the-selectour-network-and-accelerates-its-development-in-the-rapidly-growing-esim-market-for-travelers-worldwide-426420"],
        )

    def test_historical_reports_capture_false_positive_link_baseline(self):
        baseline, repeated_link_counts = load_global_trend_history_baseline()

        roaming_dog_link = "https://www.facebook.com/groups/hendersonville/posts/10161439450076546/"
        self.assertEqual(2, repeated_link_counts[roaming_dog_link])
        self.assertIn(roaming_dog_link, baseline["daily_report_20260320_091427.html"]["links"])
        self.assertIn(roaming_dog_link, baseline["daily_report_20260325_085631.html"]["links"])


if __name__ == "__main__":
    unittest.main()

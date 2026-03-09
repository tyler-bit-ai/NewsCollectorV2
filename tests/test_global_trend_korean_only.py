import unittest

from analyzers.summarizer import Summarizer
from notifiers.email_formatter import EmailFormatter
from notifiers.web_generator import WebGenerator
from utils.helpers import (
    GLOBAL_TREND_SUMMARY_FALLBACK,
    GLOBAL_TREND_TITLE_FALLBACK,
    ensure_global_trend_korean_text,
)


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
        self.assertEqual("한글 제목", processed[1]["title"])
        self.assertEqual("한글 요약", processed[1]["summary"])

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


if __name__ == "__main__":
    unittest.main()

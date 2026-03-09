import unittest
from unittest.mock import Mock

import requests

from collectors.mofa_0404_collector import Mofa0404Collector


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")


class Mofa0404CollectorUnitTests(unittest.TestCase):
    def setUp(self):
        self.collector = Mofa0404Collector(max_pages=1)

    def test_collect_by_date_range_sets_published_date_from_list_item(self):
        list_html = """
        <table>
          <tr>
            <td><a href="/bbs/safetyNtc/ATC0000000048238/detail" class="btn title">테스트 공지</a></td>
            <td>2026-03-04</td>
          </tr>
        </table>
        """
        detail_html = '<div class="view-body">해당 공지는 문자 안내가 포함됩니다.</div>'

        self.collector.session.get = Mock(
            side_effect=[_FakeResponse(list_html), _FakeResponse(detail_html), _FakeResponse("", status_code=200)]
        )

        items = self.collector.collect_keyword_posts_by_date_range("2026-03-01", "2026-03-04")

        self.assertEqual(1, len(items))
        self.assertEqual("2026-03-04", items[0]["published_date"])
        self.assertIn("문자", items[0]["matched_keywords"])

    def test_collect_by_date_range_excludes_out_of_range_dates(self):
        list_html = """
        <table>
          <tr>
            <td><a href="/bbs/embsyNtc/123/detail" class="btn title">범위 밖 공지</a></td>
            <td>2026-02-20</td>
          </tr>
        </table>
        """
        self.collector.session.get = Mock(side_effect=[_FakeResponse(list_html), _FakeResponse("")])

        items = self.collector.collect_keyword_posts_by_date_range("2026-03-01", "2026-03-04")
        self.assertEqual([], items)

    def test_collect_board_stops_after_consecutive_list_failures(self):
        collector = Mofa0404Collector(max_pages=10, list_failure_threshold=2)
        collector.session.get = Mock(side_effect=requests.RequestException("network error"))

        items = collector._collect_board(
            "embsyNtc",
            collector.BOARD_URLS["embsyNtc"],
            "2026-03-01",
            "2026-03-04",
        )

        self.assertEqual([], items)
        self.assertEqual(2, collector.session.get.call_count)

    def test_keyword_matching_normalizes_sms_mms_to_uppercase(self):
        matched = self.collector._matched_keywords("sms 와 mms 그리고 문자 공지")
        self.assertIn("SMS", matched)
        self.assertIn("MMS", matched)


if __name__ == "__main__":
    unittest.main()

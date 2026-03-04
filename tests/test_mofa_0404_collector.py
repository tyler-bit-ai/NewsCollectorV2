import unittest
from unittest.mock import Mock, patch

from collectors.mofa_0404_collector import Mofa0404Collector


class TestMofa0404Collector(unittest.TestCase):
    def setUp(self):
        self.collector = Mofa0404Collector(debug_mode=True, max_pages=1)

    def _response(self, text: str, status_code: int = 200):
        resp = Mock()
        resp.text = text
        resp.status_code = status_code
        resp.raise_for_status = Mock()
        return resp

    def test_collect_board_sets_published_date_from_post_date(self):
        list_html = """
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">해외 통신 점검 안내</a>
        <td>2026-03-04</td>
        """
        detail_html = '<div class="view-body">현지 통신 점검으로 데이터 연결이 제한될 수 있습니다.</div>'

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), self._response(detail_html)],
        ):
            self.collector.KEYWORDS = ["통신", "데이터"]
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["published_date"], "2026-03-04")

    def test_collect_board_skips_when_no_keyword_match(self):
        list_html = """
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">일반 공지</a>
        <td>2026-03-04</td>
        """
        detail_html = '<div class="view-body">행사 안내입니다.</div>'

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), self._response(detail_html)],
        ):
            self.collector.KEYWORDS = ["통신"]
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(results, [])

    def test_collect_keyword_posts_deduplicates_same_link_across_boards(self):
        duplicate_item = {
            "board_name": "공관안전공지",
            "title": "중복 테스트",
            "content_one_line": "중복",
            "link": "https://0404.go.kr/bbs/safetyNtc/ATC0001/detail",
            "published_date": "2026-03-04",
            "matched_keywords": ["통신"],
        }

        with patch.object(
            self.collector,
            "_collect_board",
            side_effect=[[duplicate_item], [dict(duplicate_item)]],
        ):
            results = self.collector.collect_keyword_posts_by_date_range("2026-03-04", "2026-03-04")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["link"], duplicate_item["link"])

    def test_collect_board_handles_detail_fetch_failure_gracefully(self):
        list_html = """
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">현지 공지 안내</a>
        <td>2026-03-04</td>
        """
        detail_error = RuntimeError("detail request failed")

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), detail_error],
        ):
            self.collector.KEYWORDS = ["통신"]
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()

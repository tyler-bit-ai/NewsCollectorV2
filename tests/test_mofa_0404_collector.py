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
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">해외 통신 장애 안내</a>
        <td>2026-03-04</td>
        """
        detail_html = '<div class="view-body">현지 통신 장애로 데이터 사용이 제한되고 있습니다.</div>'

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), self._response(detail_html)],
        ):
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["published_date"], "2026-03-04")
        self.assertEqual(results[0]["match_reason"], "context_disruption_sentence")

    def test_collect_board_skips_when_no_keyword_match(self):
        list_html = """
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">일반 안전 공지</a>
        <td>2026-03-04</td>
        """
        detail_html = '<div class="view-body">대사관 방문 안내입니다.</div>'

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), self._response(detail_html)],
        ):
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
            "matched_keywords": ["통신", "장애"],
            "match_reason": "context_disruption_sentence",
            "matched_excerpt": "통신 장애",
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
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">현지 통신 장애 공지</a>
        <td>2026-03-04</td>
        """
        detail_error = RuntimeError("detail request failed")

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), detail_error],
        ):
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(len(results), 1)
        self.assertEqual("", results[0]["content_one_line"])
        self.assertEqual("context_disruption_sentence", results[0]["match_reason"])

    def test_collect_board_skips_generic_communication_phrase_without_block_terms(self):
        list_html = """
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">현지 통신 수단 안내</a>
        <td>2026-03-04</td>
        """
        detail_html = '<div class="view-body">비상시 통신 수단과 연락망을 안내합니다.</div>'

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), self._response(detail_html)],
        ):
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(results, [])

    def test_collect_board_matches_sms_unavailable_notice(self):
        list_html = """
        <a href="/bbs/embsyNtc/123/detail?ntnCd=18" class="btn title">현지 SMS 발신 불가 안내</a>
        <td>2026-03-04</td>
        """
        detail_html = '<div class="view-body">통신사 점검으로 SMS/MMS 발신이 일시 불가합니다.</div>'

        with patch.object(
            self.collector.session,
            "get",
            side_effect=[self._response(list_html), self._response(detail_html)],
        ):
            results = self.collector._collect_board(
                board_key="embsyNtc",
                list_url=self.collector.BOARD_URLS["embsyNtc"],
                start_date_kst="2026-03-04",
                end_date_kst="2026-03-04",
            )

        self.assertEqual(len(results), 1)
        self.assertIn("SMS", results[0]["matched_keywords"])
        self.assertIn("MMS", results[0]["matched_keywords"])
        self.assertIn("불가", results[0]["matched_keywords"])


if __name__ == "__main__":
    unittest.main()

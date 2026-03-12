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
            <td><a href="/bbs/safetyNtc/ATC0000000048238/detail" class="btn title">안전 안내</a></td>
            <td>2026-03-04</td>
          </tr>
        </table>
        """
        detail_html = '<div class="view-body">현지 휴대전화 문자 수신이 지연되고 있습니다.</div>'

        self.collector.session.get = Mock(
            side_effect=[_FakeResponse(list_html), _FakeResponse(detail_html), _FakeResponse("", status_code=200)]
        )

        items = self.collector.collect_keyword_posts_by_date_range("2026-03-01", "2026-03-04")

        self.assertEqual(1, len(items))
        self.assertEqual("2026-03-04", items[0]["published_date"])
        self.assertEqual("context_disruption_sentence", items[0]["match_reason"])
        self.assertIn("문자", items[0]["matched_keywords"])
        self.assertIn("지연", items[0]["matched_keywords"])

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

    def test_keyword_matching_normalizes_uppercase_tokens(self):
        matched = self.collector._matched_keywords("sms 와 mms 그리고 esim 장애 공지")
        self.assertIn("SMS", matched)
        self.assertIn("MMS", matched)
        self.assertIn("ESIM", matched)

    def test_classify_post_rejects_weak_keyword_only_false_positive(self):
        result = self.collector._classify_post(
            title="바누아투 화산 가스 확산 안전 공지",
            body_text="모든 문과 창문을 닫고 외부 공기 유입을 차단하십시오.",
        )
        self.assertIsNone(result)

    def test_classify_post_rejects_security_context_false_positive(self):
        result = self.collector._classify_post(
            title="홍해 해상 안전 공지",
            body_text="후티반군이 지도부와 구성원들의 통신 보안 강화를 위해 휴대전화 번호를 변경했습니다.",
        )
        self.assertIsNone(result)

    def test_classify_post_accepts_roaming_title(self):
        result = self.collector._classify_post(
            title="현지 데이터 로밍 장애 안내",
            body_text="세부 내용은 추후 공지 예정입니다.",
        )
        self.assertIsNotNone(result)
        self.assertEqual("title_service_disruption", result["match_reason"])

    def test_classify_post_accepts_context_disruption_sentence(self):
        result = self.collector._classify_post(
            title="현지 안전 안내",
            body_text="현지 인터넷 접속이 불안정하고 문자 수신이 지연되고 있습니다.",
        )
        self.assertIsNotNone(result)
        self.assertEqual("context_disruption_sentence", result["match_reason"])
        self.assertIn("인터넷", result["matched_keywords"])
        self.assertIn("지연", result["matched_keywords"])

    def test_classify_post_rejects_missing_person_notice(self):
        result = self.collector._classify_post(
            title="연락두절 공고(정승우)",
            body_text="연락이 두절된 아래인을 아시는 분은 대사관 해외안전팀 또는 긴급전화로 연락주시기 바랍니다.",
        )
        self.assertIsNone(result)

    def test_classify_post_rejects_airport_access_restriction_notice(self):
        result = self.collector._classify_post(
            title="주의 중동지역 일부 국제공항 공항 내 출입 제한 관련 안내(항공권 미소지자 출입 제한)",
            body_text="항공권 미소지자는 공항 터미널 진입이 제한되고 있습니다.",
        )
        self.assertIsNone(result)

    def test_classify_post_rejects_advisory_leaflet_with_possible_network_issue(self):
        result = self.collector._classify_post(
            title="페루 안전여행 길잡이 (안전여행정보 리플릿)",
            body_text=(
                "정글 투어 지역은 전력 혹은 통신망이 원활하지 않아 장시간 연락이 되지 않을 가능성이 크니 "
                "안전한 체류를 위해 참고하시길 바랍니다."
            ),
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

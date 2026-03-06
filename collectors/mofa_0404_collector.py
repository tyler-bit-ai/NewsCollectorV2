"""
0404.go.kr 게시판(공관안전공지/안전공지) 수집기
"""
from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

import requests

from .base import BaseCollector

logger = logging.getLogger(__name__)


class Mofa0404Collector(BaseCollector):
    """0404 게시판에서 KST 날짜 범위 키워드 매칭 게시글을 수집한다."""

    BOARD_URLS = {
        "embsyNtc": "https://0404.go.kr/bbs/embsyNtc/list",
        "safetyNtc": "https://0404.go.kr/bbs/safetyNtc/list",
    }

    BOARD_NAMES = {
        "embsyNtc": "공관안전공지",
        "safetyNtc": "안전공지",
    }

    CHANNEL_KEYWORDS = [
        "로밍",
        "인터넷",
        "데이터",
        "국제전화",
        "통화",
        "문자",
        "sms",
        "mms",
    ]

    BLOCK_KEYWORDS = [
        "차단",
        "중단",
        "불가",
        "장애",
        "두절",
        "제한",
    ]

    LIST_ITEM_PATTERN = re.compile(
        r'<a href="(?P<link>/bbs/(?P<board>embsyNtc|safetyNtc)/[^"]*/detail[^"]*)" class="btn title">'
        r'(?P<title>[\s\S]*?)</a>[\s\S]*?<td>\s*(?P<date>\d{4}-\d{2}-\d{2})\s*</td>',
        re.IGNORECASE,
    )
    VIEW_BODY_PATTERN = re.compile(
        r'<div class="view-body"\s*[^>]*>(?P<body>[\s\S]*?)</div>',
        re.IGNORECASE,
    )
    TAG_PATTERN = re.compile(r"<[^>]+>")

    def __init__(self, debug_mode: bool = False, max_pages: int = 30):
        super().__init__(debug_mode)
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            }
        )

    def collect(self, query: str = "", limit: int = 0) -> List[Dict]:
        """BaseCollector 인터페이스 호환용."""
        return self.collect_today_keyword_posts()

    def collect_today_keyword_posts(self) -> List[Dict]:
        """두 게시판에서 KST 당일 키워드 매칭 게시글을 수집한다."""
        today_kst = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
        return self.collect_keyword_posts_by_date_range(today_kst, today_kst)

    def collect_keyword_posts_by_date_range(self, start_date_kst: str, end_date_kst: str) -> List[Dict]:
        """
        두 게시판에서 날짜 범위(KST, YYYY-MM-DD, 양끝 포함) 키워드 매칭 게시글을 수집한다.
        """
        collected: List[Dict] = []
        seen_links = set()

        for board_key, list_url in self.BOARD_URLS.items():
            board_name = self.BOARD_NAMES[board_key]
            logger.info(f"[0404] Collecting board: {board_name}")
            board_items = self._collect_board(board_key, list_url, start_date_kst, end_date_kst)

            for item in board_items:
                link = item["link"]
                if link in seen_links:
                    continue
                seen_links.add(link)
                collected.append(item)

        logger.info(f"[0404] Collected matched posts: {len(collected)}")
        return collected

    def _collect_board(self, board_key: str, list_url: str, start_date_kst: str, end_date_kst: str) -> List[Dict]:
        results: List[Dict] = []
        board_name = self.BOARD_NAMES[board_key]

        for page_index in range(1, self.max_pages + 1):
            page_url = f"{list_url}?pageIndex={page_index}"
            try:
                response = self.session.get(page_url, timeout=15)
                response.raise_for_status()
                page_html = response.text
            except Exception as e:
                logger.warning(f"[0404] Failed to load list page: {page_url} ({e})")
                continue

            list_items = list(self.LIST_ITEM_PATTERN.finditer(page_html))
            if not list_items:
                break

            target_items = []
            older_exists = False
            for match in list_items:
                date_text = match.group("date").strip()
                if start_date_kst <= date_text <= end_date_kst:
                    target_items.append(match)
                elif date_text < start_date_kst:
                    older_exists = True

            for match in target_items:
                relative_link = html.unescape(match.group("link").strip())
                link = f"https://0404.go.kr{relative_link}"
                title = self._to_one_line(match.group("title"))

                body_text = self._fetch_detail_body(link)
                combined = f"{title} {body_text}"
                matched = self._matched_keywords(combined)
                if not matched:
                    continue

                content_preview = body_text
                if len(content_preview) > 200:
                    content_preview = f"{content_preview[:200].rstrip()}..."

                results.append(
                    {
                        "board_name": board_name,
                        "title": title,
                        "content_one_line": content_preview,
                        "link": link,
                        "published_date": date_text,
                        "matched_keywords": matched,
                    }
                )
                self.collected_count += 1

            # 정렬이 최신순이라 당일 글이 없고 과거 글만 보이면 종료
            if not target_items and older_exists:
                break

        return results

    def _fetch_detail_body(self, detail_url: str) -> str:
        try:
            response = self.session.get(detail_url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"[0404] Failed to load detail page: {detail_url} ({e})")
            return ""

        match = self.VIEW_BODY_PATTERN.search(response.text)
        if not match:
            return ""

        return self._to_one_line(match.group("body"))

    def _matched_keywords(self, text: str) -> List[str]:
        text_lower = text.lower()
        matched_channels = []
        for keyword in self.CHANNEL_KEYWORDS:
            if keyword in text_lower:
                matched_channels.append(keyword.upper() if keyword in {"sms", "mms"} else keyword)

        matched_blocks = []
        for keyword in self.BLOCK_KEYWORDS:
            if keyword in text_lower:
                matched_blocks.append(keyword)

        if not matched_channels or not matched_blocks:
            return []

        return matched_channels + matched_blocks

    def _to_one_line(self, value: str) -> str:
        text = self.TAG_PATTERN.sub(" ", value)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

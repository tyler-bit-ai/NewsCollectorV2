"""
시간 필터링 (24시간 윈도우)
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TimeFilter:
    """시간 기반 필터링"""

    def __init__(self, window_hours: int = 24):
        """
        Args:
            window_hours: 시간 윈도우 (기본 24시간)
        """
        self.window_hours = window_hours
        self.cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    def is_valid(self, pub_date: datetime) -> bool:
        """
        24시간 윈도우 내에 있는지 확인

        Args:
            pub_date: 기사 발행일

        Returns:
            윈도우 내에 있으면 True
        """
        if not pub_date:
            return True  # 날짜 파싱 실패 시 포함

        is_valid = pub_date >= self.cutoff_time

        if not is_valid and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Filtered by time: {pub_date} < {self.cutoff_time}")

        return is_valid

    def filter_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        기사 리스트 시간 필터링

        Args:
            articles: 기사 리스트

        Returns:
            필터링된 기사 리스트
        """
        filtered = []
        for article in articles:
            if self.is_valid(article.get('published')):
                filtered.append(article)

        logger.info(f"Time filter: {len(filtered)}/{len(articles)} passed")
        return filtered

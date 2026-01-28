"""
Google Custom Search API 수집기
"""
import requests
from typing import List, Dict
import logging

from .base import BaseCollector
from utils.exceptions import APIError

logger = logging.getLogger(__name__)


class GoogleCollector(BaseCollector):
    """Google Custom Search API 수집기"""

    def __init__(self, api_key: str, search_engine_id: str, debug_mode: bool = False):
        super().__init__(debug_mode)
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def collect(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Google Custom Search API 수집

        Args:
            query: 검색어
            limit: 수집 개수

        Returns:
            기사 리스트
        """
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": limit
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                raise APIError(f"Google API failed: {response.status_code}")

            data = response.json()
            items = data.get('items', [])

            articles = []
            for item in items:
                article = {
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'snippet': item.get('snippet'),
                    'source': 'Google',
                    'published': None,  # Google은 날짜 제공 안 함
                    'type': 'global'
                }

                articles.append(article)
                self.collected_count += 1

            return articles

        except requests.exceptions.Timeout:
            logger.error(f"Google API timeout: {query}")
            return []
        except Exception as e:
            logger.error(f"Google API exception: {e}")
            raise

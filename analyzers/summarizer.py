"""
STEP 1: 기사 요약 (GPT-4o-mini)
"""
from typing import Dict, List
import logging

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class Summarizer(BaseAnalyzer):
    """기사 요약기"""

    def analyze(self, data: Dict) -> Dict:
        """
        기사 요약 분석

        Args:
            data: {'category_name': [articles...]}

        Returns:
            요약된 데이터
        """
        results = {}

        for category, articles in data.items():
            if not articles:
                results[category] = []
                continue

            # 카테고리별 텍스트 변환
            articles_text = self._format_articles(articles)

            # AI 요약 호출
            summaries = self._summarize_category(category, articles_text)
            results[category] = summaries

        return results

    def _format_articles(self, articles: List[Dict]) -> str:
        """기사를 텍스트로 변환"""
        formatted = []
        for i, article in enumerate(articles[:10], 1):  # 최대 10개
            formatted.append(
                f"[{i}] {article['title']}\n"
                f"링크: {article['link']}\n"
                f"요약: {article['snippet']}\n"
            )
        return "\n".join(formatted)

    def _summarize_category(self, category: str, articles_text: str) -> List[Dict]:
        """카테고리별 요약"""
        prompt = f"""
다음은 '{category}' 카테고리의 뉴스 기사 목록입니다.

{articles_text}

각 기사를 2-3문장으로 요약하고, 다음 JSON 형식으로 반환:

{{
  "summaries": [
    {{
      "index": 1,
      "title": "기사 제목",
      "summary": "요약 내용",
      "link": "기사 링크"
    }}
  ]
}}
"""

        try:
            response = self._call_ai([
                {"role": "system", "content": "당신은 뉴스 요약 전문가입니다."},
                {"role": "user", "content": prompt}
            ])
            return response.get('summaries', [])

        except Exception as e:
            logger.error(f"Summary failed for {category}: {e}")
            return []

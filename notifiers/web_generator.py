"""
웹 페이지 생성
"""
import os
from typing import Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebGenerator:
    """웹 페이지 생성기"""

    def __init__(self, template_dir: str = "notifiers/templates"):
        self.template_dir = template_dir

    def generate(self, data: Dict, output_path: str = "output/web/daily_report.html"):
        """
        HTML 웹 페이지 생성

        Args:
            data: 분석 데이터
            output_path: 출력 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        html = self._render_html(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"Web page generated: {output_path}")

    def _render_html(self, data: Dict) -> str:
        """HTML 렌더링"""
        # 기본 HTML 템플릿
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SKT 로밍팀 일일 뉴스 리포트</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #007bff;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #333;
                    margin-top: 30px;
                    border-left: 4px solid #007bff;
                    padding-left: 10px;
                }}
                .section {{
                    margin-bottom: 30px;
                }}
                .article {{
                    margin-bottom: 15px;
                    padding: 15px;
                    border-left: 3px solid #007bff;
                    background-color: #f8f9fa;
                }}
                .source {{
                    color: #666;
                    font-size: 0.9em;
                }}
                .title {{
                    font-weight: bold;
                    color: #333;
                    margin: 5px 0;
                }}
                .summary {{
                    color: #666;
                }}
                .link {{
                    color: #007bff;
                    text-decoration: none;
                }}
                .link:hover {{
                    text-decoration: underline;
                }}
                ul {{
                    margin: 10px 0;
                }}
                li {{
                    margin: 5px 0;
                }}
                .date {{
                    color: #999;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SKT 로밍팀 일일 뉴스 리포트</h1>
                <p class="date"><strong>{datetime.now().strftime('%Y년 %m월 %d일')}</strong></p>

                <div class="section">
                    <h2>📊 전략 인사이트</h2>
                    <p>{data.get('strategic_insight', '데이터가 없습니다.')}</p>
                </div>

                <div class="section">
                    <h2>🔍 주요 발견</h2>
                    <ul>
                        {self._format_findings(data.get('key_findings', []))}
                    </ul>
                </div>

                <div class="section">
                    <h2>💡 행동 권고</h2>
                    <ul>
                        {self._format_recommendations(data.get('recommendations', []))}
                    </ul>
                </div>

                {self._generate_category_sections(data)}
            </div>
        </body>
        </html>
        """
        return html

    def _format_findings(self, findings: list) -> str:
        """주요 발견 포맷팅"""
        if not findings:
            return "<li>없음</li>"
        return "\n".join(f"<li>{f}</li>" for f in findings)

    def _format_recommendations(self, recommendations: list) -> str:
        """행동 권고 포맷팅"""
        if not recommendations:
            return "<li>없음</li>"
        return "\n".join(f"<li>{r}</li>" for r in recommendations)

    def _generate_category_sections(self, data: Dict) -> str:
        """카테고리 섹션 생성"""
        sections = []

        category_names = {
            'market_culture': '0. Market & Culture (Macro)',
            'global_trend': '1. Global Roaming Trend',
            'competitors': '2. SKT & Competitors',
            'esim_products': '3. eSIM Products',
            'voc_roaming': '4. 로밍 VoC',
            'voc_esim': '5. eSIM VoC'
        }

        for key, name in category_names.items():
            articles = data.get(f'section_{key}', [])

            articles_html = ""
            for article in articles:
                # 타입 검증 추가
                if not isinstance(article, dict):
                    continue

                articles_html += f"""
                <div class="article">
                    <div class="source">{article.get('source', '')}</div>
                    <div class="title">{article.get('title', '')}</div>
                    <div class="summary">{article.get('summary', '')}</div>
                    <a href="{article.get('link', '')}" class="link" target="_blank">기사 보기</a>
                </div>
                """

            section = f"""
            <div class="section">
                <h2>{name}</h2>
                {articles_html if articles_html else '<p>데이터가 없습니다.</p>'}
            </div>
            """
            sections.append(section)

        return "\n".join(sections)

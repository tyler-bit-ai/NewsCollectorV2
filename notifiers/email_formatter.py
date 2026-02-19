"""
HTML 이메일 생성
"""
from typing import Dict
from datetime import datetime
import html as html_lib
import os

class EmailFormatter:
    """이메일 포매터"""

    def __init__(self, template_dir: str = "notifiers/templates"):
        self.template_dir = template_dir

    def format(self, data: Dict) -> str:
        """
        분석된 데이터를 HTML 이메일로 변환

        Args:
            data: 분석 데이터

        Returns:
            HTML 이메일 본문
        """
        # 템플릿 로드
        template_path = os.path.join(self.template_dir, "email_template.html")

        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            template = self._get_default_template()

        # 데이터 치환
        html = template.replace("{{DATE}}", datetime.now().strftime('%Y년 %m월 %d일'))
        html = html.replace("{{EXTERNAL_ALERTS_SECTION}}", self._format_external_alerts_section(data.get('external_alerts', [])))
        html = html.replace("{{STRATEGIC_INSIGHT}}", data.get('strategic_insight', ''))
        html = html.replace("{{KEY_FINDINGS}}", self._format_findings(data.get('key_findings', [])))
        html = html.replace("{{RECOMMENDATIONS}}", self._format_recommendations(data.get('recommendations', [])))

        # 카테고리 섹션 (동적으로 생성)
        category_sections = self._generate_category_sections(data)
        html = html.replace("{{CATEGORY_SECTIONS}}", category_sections)

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

    def _format_external_alerts_section(self, alerts: list) -> str:
        """0404 당일 키워드 공지 섹션 렌더링"""
        if not alerts:
            return """
            <div class="section">
                <h2>0404 당일 키워드 공지</h2>
                <p>당일 매칭 공지 없음</p>
            </div>
            """

        rendered = []
        for alert in alerts:
            if not isinstance(alert, dict):
                continue

            title = html_lib.escape(alert.get('title', ''))
            content = html_lib.escape(alert.get('content_one_line', ''))
            link = html_lib.escape(alert.get('link', ''))
            board_name = html_lib.escape(alert.get('board_name', ''))

            rendered.append(f"""
            <div class="article">
                <div class="source">{board_name}</div>
                <div class="title">{title}</div>
                <div class="summary">{content}</div>
                <a href="{link}" class="link">원문 보기</a>
            </div>
            """)

        body = "\n".join(rendered) if rendered else "<p>당일 매칭 공지 없음</p>"
        return f"""
        <div class="section">
            <h2>0404 당일 키워드 공지</h2>
            {body}
        </div>
        """

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

            section = f"""
            <div class="section">
                <h2>{name}</h2>
                {self._render_articles(articles)}
            </div>
            """
            sections.append(section)

        return "\n".join(sections)

    def _render_articles(self, articles: list) -> str:
        """기사 리스트 렌더링"""
        if not articles:
            return "<p>데이터가 없습니다.</p>"

        rendered = []
        for article in articles:
            # 타입 검증 추가
            if not isinstance(article, dict):
                continue

            rendered.append(f"""
            <div class="article">
                <div class="source">{article.get('source', '')}</div>
                <div class="title">{article.get('title', '')}</div>
                <div class="summary">{article.get('summary', '')}</div>
                <a href="{article.get('link', '')}" class="link">기사 보기</a>
            </div>
            """)

        return "\n".join(rendered) if rendered else "<p>데이터가 없습니다.</p>"

    def _get_default_template(self) -> str:
        """기본 HTML 템플릿"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                .section { margin-bottom: 30px; }
                .article { margin-bottom: 15px; padding: 10px; border-left: 3px solid #007bff; }
                .source { color: #666; font-size: 0.9em; }
                .title { font-weight: bold; color: #333; margin: 5px 0; }
                .summary { color: #666; }
                .link { color: #007bff; text-decoration: none; }
                .link:hover { text-decoration: underline; }
                ul { margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>SKT 로밍팀 일일 뉴스 리포트</h1>
            <p><strong>{{DATE}}</strong></p>

            {{EXTERNAL_ALERTS_SECTION}}

            <div class="section">
                <h2>📊 전략 인사이트</h2>
                <p>{{STRATEGIC_INSIGHT}}</p>
            </div>

            <div class="section">
                <h2>🔍 주요 발견</h2>
                <ul>{{KEY_FINDINGS}}</ul>
            </div>

            <div class="section">
                <h2>💡 행동 권고</h2>
                <ul>{{RECOMMENDATIONS}}</ul>
            </div>

            {{CATEGORY_SECTIONS}}
        </body>
        </html>
        """

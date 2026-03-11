"""
웹 페이지 생성
"""
from datetime import datetime
import html as html_lib
import os
from typing import Dict, List
import logging
from utils.helpers import ensure_global_trend_korean_text

logger = logging.getLogger(__name__)


class WebGenerator:
    """웹 페이지 생성기"""

    CATEGORY_NAMES = {
        "market_culture": "0. Market & Culture (Macro)",
        "global_trend": "1. Global Roaming Trend",
        "competitors": "2. SKT & Competitors",
        "esim_products": "3. eSIM Products",
        "voc_roaming": "4. 로밍 VoC",
        "voc_esim": "5. eSIM VoC",
    }

    def __init__(self, template_dir: str = "notifiers/templates", default_visible_n: int = 3, summary_max_chars: int = 180):
        self.template_dir = template_dir
        self.default_visible_n = max(1, default_visible_n)
        self.summary_max_chars = max(80, summary_max_chars)

    def generate(self, data: Dict, output_path: str = "output/web/daily_report.html"):
        """
        HTML 웹 페이지 생성

        Args:
            data: 분석 데이터
            output_path: 출력 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        rendered = self._render_html(data)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_dir = os.path.join(os.path.dirname(output_path), "history")
        os.makedirs(history_dir, exist_ok=True)
        history_path = os.path.join(history_dir, f"daily_report_{timestamp}.html")
        with open(history_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        logger.info(f"Web page generated (latest): {output_path}")
        logger.info(f"Web page archived: {history_path}")

    def _render_html(self, data: Dict) -> str:
        brief_items = self._format_today_brief(data)
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SKT 로밍팀 일일 뉴스 리포트</title>
            <style>
                :root {{
                    --bg: #f1f5f9;
                    --card: #ffffff;
                    --text: #0f172a;
                    --muted: #475569;
                    --line: #dbe3ef;
                    --accent: #0f766e;
                    --accent-soft: #ecfeff;
                }}
                * {{ box-sizing: border-box; }}
                body {{
                    font-family: "Segoe UI", "Noto Sans KR", sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: radial-gradient(circle at top right, #c7d2fe 0%, var(--bg) 55%);
                    color: var(--text);
                }}
                .container {{
                    max-width: 1180px;
                    margin: 0 auto;
                    background: var(--card);
                    border: 1px solid var(--line);
                    border-radius: 14px;
                    padding: 24px;
                }}
                h1 {{
                    margin: 0;
                    color: #0f172a;
                    font-size: 30px;
                }}
                .date {{
                    color: var(--muted);
                    font-size: 14px;
                    margin: 8px 0 18px 0;
                }}
                .brief {{
                    background: #eef2ff;
                    border: 1px solid #c7d2fe;
                    border-radius: 10px;
                    padding: 14px;
                    margin-bottom: 18px;
                }}
                .section {{
                    margin-top: 20px;
                    padding-top: 16px;
                    border-top: 1px solid var(--line);
                }}
                .section h2 {{
                    margin: 0 0 10px 0;
                    font-size: 20px;
                }}
                .count {{
                    color: var(--muted);
                    font-size: 13px;
                    font-weight: normal;
                }}
                .article {{
                    margin-bottom: 10px;
                    padding: 12px;
                    border-left: 4px solid var(--accent);
                    background: #f8fafc;
                    border-radius: 6px;
                }}
                .source {{
                    color: var(--muted);
                    font-size: 12px;
                }}
                .title {{
                    font-size: 16px;
                    font-weight: 700;
                    margin: 4px 0 6px 0;
                }}
                .summary {{
                    color: #334155;
                    margin: 0 0 6px 0;
                    font-size: 14px;
                }}
                .link {{
                    color: #0f766e;
                    text-decoration: none;
                }}
                .link:hover {{
                    text-decoration: underline;
                }}
                .more {{
                    margin-top: 8px;
                    background: #f8fafc;
                    border: 1px solid var(--line);
                    border-radius: 8px;
                    padding: 8px 10px;
                }}
                details summary {{
                    cursor: pointer;
                    font-weight: 600;
                    color: #0f766e;
                }}
                ul, ol {{
                    margin: 8px 0 0 0;
                    padding-left: 18px;
                }}
                li {{ margin: 4px 0; }}
                @media (max-width: 760px) {{
                    body {{ padding: 10px; }}
                    .container {{ padding: 14px; }}
                    h1 {{ font-size: 24px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SKT 로밍팀 일일 뉴스 리포트</h1>
                <p class="date"><strong>{datetime.now().strftime('%Y년 %m월 %d일')}</strong></p>
                <div class="brief">
                    <h2>오늘의 5줄 요약</h2>
                    <ul>{brief_items}</ul>
                </div>
                {self._render_external_alerts_section(data.get("external_alerts", []))}
                <div class="section">
                    <h2>📊 전략 인사이트</h2>
                    <p>{self._format_paragraph(data.get("strategic_insight", "데이터가 없습니다."))}</p>
                </div>
                <div class="section">
                    <h2>🔍 주요 발견</h2>
                    <ul>{self._format_findings(data.get("key_findings", []))}</ul>
                </div>
                <div class="section">
                    <h2>💡 행동 권고</h2>
                    <ul>{self._format_recommendations(data.get("recommendations", []))}</ul>
                </div>
                {self._generate_category_sections(data)}
            </div>
        </body>
        </html>
        """

    def _format_today_brief(self, data: Dict) -> str:
        lines: List[str] = []
        for finding in data.get("key_findings", [])[:3]:
            lines.append(self._truncate(str(finding), 120))
        for rec in data.get("recommendations", [])[:2]:
            lines.append(f"[권고] {self._truncate(str(rec), 120)}")
        if not lines:
            return "<li>요약 데이터가 없습니다.</li>"
        return "\n".join(f"<li>{html_lib.escape(item)}</li>" for item in lines[:5])

    def _format_paragraph(self, text: str) -> str:
        escaped = html_lib.escape(str(text or ""))
        if not escaped:
            return "데이터가 없습니다."
        return escaped.replace("\n", "<br>")

    def _format_findings(self, findings: List[str]) -> str:
        if not findings:
            return "<li>없음</li>"
        return "\n".join(f"<li>{html_lib.escape(str(item))}</li>" for item in findings)

    def _format_recommendations(self, recommendations: List[str]) -> str:
        if not recommendations:
            return "<li>없음</li>"
        return "\n".join(f"<li>{html_lib.escape(str(item))}</li>" for item in recommendations)

    def _render_external_alerts_section(self, alerts: List[Dict]) -> str:
        if not alerts:
            return """
            <div class="section">
                <h2>해외 안전 공지 <span class="count">(0건)</span></h2>
                <p>당일 매칭 공지 없음</p>
            </div>
            """

        valid_alerts = [alert for alert in alerts if isinstance(alert, dict)]
        highlights = valid_alerts[: self.default_visible_n]
        remaining = valid_alerts[self.default_visible_n :]
        cards = [self._render_external_alert_card(item) for item in highlights]
        more = self._render_external_alert_links(remaining)

        return f"""
        <div class="section">
            <h2>해외 안전 공지 <span class="count">({len(alerts)}건)</span></h2>
            {''.join(cards)}
            {more}
        </div>
        """

    def _render_external_alert_card(self, alert: Dict) -> str:
        board_name = html_lib.escape(str(alert.get("board_name", "")))
        title = html_lib.escape(str(alert.get("title", "")))
        summary = html_lib.escape(self._truncate(str(alert.get("content_one_line", "")), self.summary_max_chars))
        link = html_lib.escape(str(alert.get("link", "")))
        return f"""
        <div class="article">
            <div class="source">{board_name}</div>
            <div class="title">{title}</div>
            <div class="summary">{summary}</div>
            <a href="{link}" class="link" target="_blank">원문 보기</a>
        </div>
        """

    def _render_external_alert_links(self, remaining: List[Dict]) -> str:
        if not remaining:
            return ""

        rows = []
        for item in remaining:
            if not isinstance(item, dict):
                continue
            title = html_lib.escape(str(item.get("title", "")))
            link = html_lib.escape(str(item.get("link", "")))
            rows.append(f'<li><a href="{link}" class="link" target="_blank">{title}</a></li>')

        if not rows:
            return ""

        return f"""
        <details class="more">
            <summary>湲고? {len(rows)}嫄???蹂닿린</summary>
            <ol>{''.join(rows)}</ol>
        </details>
        """

    def _generate_category_sections(self, data: Dict) -> str:
        sections = []
        for key, name in self.CATEGORY_NAMES.items():
            raw_articles = data.get(f"section_{key}", [])
            articles = [item for item in raw_articles if isinstance(item, dict)]
            sections.append(self._render_category_section(name=name, category_key=key, articles=articles))
        return "\n".join(sections)

    def _render_category_section(self, name: str, category_key: str, articles: List[Dict]) -> str:
        if not articles:
            return f"""
            <div class="section">
                <h2>{html_lib.escape(name)} <span class="count">(0건)</span></h2>
                <p>데이터가 없습니다.</p>
            </div>
            """

        top_articles = articles[: self.default_visible_n]
        remaining = articles[self.default_visible_n :]
        top_html = [self._render_article_card(article, category_key) for article in top_articles]
        more = self._render_more_links(remaining, category_key=category_key)

        return f"""
        <div class="section">
            <h2>{html_lib.escape(name)} <span class="count">({len(articles)}건)</span></h2>
            {''.join(top_html)}
            {more}
        </div>
        """

    def _render_article_card(self, article: Dict, category_key: str) -> str:
        source = html_lib.escape(str(article.get("source", "")))
        title_raw = str(article.get("title", ""))
        summary_raw = str(article.get("summary", ""))
        if category_key == "global_trend":
            title_raw, summary_raw = ensure_global_trend_korean_text(title_raw, summary_raw)
        title = html_lib.escape(title_raw)
        summary = html_lib.escape(self._truncate(summary_raw, self.summary_max_chars))
        link = html_lib.escape(str(article.get("link", "")))
        section_hint = "VoC 하이라이트" if category_key.startswith("voc_") else "뉴스 하이라이트"
        source_line = f"{section_hint}{' | ' + source if source else ''}"
        return f"""
        <div class="article">
            <div class="source">{source_line}</div>
            <div class="title">{title}</div>
            <div class="summary">{summary}</div>
            <a href="{link}" class="link" target="_blank">원문 보기</a>
        </div>
        """

    def _render_more_links(self, remaining: List[Dict], category_key: str = "") -> str:
        if not remaining:
            return ""

        rows = []
        for item in remaining:
            if not isinstance(item, dict):
                continue
            title_raw = str(item.get("title", ""))
            if category_key == "global_trend":
                title_raw, _ = ensure_global_trend_korean_text(title_raw, "")
            title = html_lib.escape(title_raw)
            link = html_lib.escape(str(item.get("link", "")))
            rows.append(f'<li><a href="{link}" class="link" target="_blank">{title}</a></li>')

        if not rows:
            return ""

        return f"""
        <details class="more">
            <summary>기타 {len(rows)}건 더 보기</summary>
            <ol>{''.join(rows)}</ol>
        </details>
        """

    def _truncate(self, text: str, max_chars: int) -> str:
        plain = str(text or "").strip()
        if len(plain) <= max_chars:
            return plain
        return f"{plain[:max_chars].rstrip()}..."

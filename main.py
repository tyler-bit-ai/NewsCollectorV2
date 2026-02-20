"""
SKT 로밍팀 뉴스 수집 시스템 메인 실행 파일
"""
import yaml
import logging
from typing import Dict, List

from config.settings import load_settings
from config.recipient_store import get_group_recipients
from utils.logger import setup_logger
from utils.exceptions import NewsCollectorError
from utils.time_windows import get_collection_window_kst

# 수집 계층
from collectors.naver_collector import NaverCollector
from collectors.google_collector import GoogleCollector
from collectors.mofa_0404_collector import Mofa0404Collector

# 필터링 계층
from filters.time_filter import TimeFilter
from filters.keyword_filter import KeywordFilter
from filters.deduplicator import Deduplicator

# 분석 계층
from analyzers.summarizer import Summarizer
from analyzers.insight_generator import InsightGenerator

# 발송 계층
from notifiers.email_formatter import EmailFormatter
from notifiers.smtp_sender import SMTPSender
from notifiers.web_generator import WebGenerator


def load_categories(config_path: str = "config/categories.yaml") -> Dict:
    """
    카테고리 설정 로드

    Args:
        config_path: 설정 파일 경로

    Returns:
        카테고리 설정
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def collect_articles(settings) -> Dict:
    """
    기사 수집 메인 함수

    Args:
        settings: 설정 객체

    Returns:
        카테고리별 기사 딕셔너리
    """
    logger = logging.getLogger("news_collector")
    logger.info("=== Starting News Collection ===")

    # 수집기 초기화
    naver_collector = NaverCollector(
        client_id=settings.api.naver_client_id,
        client_secret=settings.api.naver_client_secret,
        debug_mode=settings.debug_mode
    )

    google_collector = GoogleCollector(
        api_key=settings.api.google_api_key,
        search_engine_id=settings.api.search_engine_id,
        debug_mode=settings.debug_mode
    )

    # 필터 초기화
    config = load_categories()
    filters_config = config['filters']

    window = get_collection_window_kst(window_hours=settings.time_window_hours)
    logger.info(
        f"Collection window ({window.label}): "
        f"KST {window.start_kst.strftime('%Y-%m-%d %H:%M')} ~ {window.end_kst.strftime('%Y-%m-%d %H:%M')}"
    )
    time_filter = TimeFilter(
        window_hours=settings.time_window_hours,
        start_time=window.start_utc,
        end_time=window.end_utc
    )
    keyword_filter = KeywordFilter(
        blacklist_domains=filters_config['blacklist_domains'],
        excluded_keywords=filters_config['excluded_keywords']
    )
    deduplicator = Deduplicator()

    # 카테고리별 수집
    categories = config['categories']
    collected_data: Dict[str, List] = {}

    for cat_key, cat_config in categories.items():
        logger.info(f"\n[{cat_config['id']}] {cat_config['name']}")

        category_articles = []
        sources = cat_config['sources']
        keywords = cat_config['keywords']

        for keyword in keywords:
            logger.info(f"  Keyword: {keyword}")

            # Naver News
            if 'naver_news' in sources:
                try:
                    articles = naver_collector.collect_from_news(keyword, limit=5)
                    category_articles.extend(articles)
                except Exception as e:
                    logger.error(f"    Naver News failed: {e}")

            # Naver Blog
            if 'naver_blog' in sources:
                try:
                    articles = naver_collector.collect_from_blog(keyword, limit=5)
                    category_articles.extend(articles)
                except Exception as e:
                    logger.error(f"    Naver Blog failed: {e}")

            # Naver Cafe
            if 'naver_cafe' in sources:
                try:
                    articles = naver_collector.collect_from_cafe(keyword, limit=5)
                    category_articles.extend(articles)
                except Exception as e:
                    logger.error(f"    Naver Cafe failed: {e}")

            # Google Search
            if 'google_search' in sources:
                try:
                    articles = google_collector.collect(keyword, limit=5)
                    category_articles.extend(articles)
                except Exception as e:
                    logger.error(f"    Google Search failed: {e}")

        # 필터링
        logger.info(f"  Filtering articles...")

        # 시간 필터링
        category_articles = time_filter.filter_articles(category_articles)

        # 키워드 필터링
        category_articles = keyword_filter.filter_articles(category_articles)

        # 중복 제거
        category_articles = deduplicator.deduplicate_within_category(category_articles)

        # 카테고리 태그 추가
        for article in category_articles:
            article['category'] = cat_key

        collected_data[cat_key] = category_articles
        logger.info(f"  Collected: {len(category_articles)} articles")

    # 카테고리 간 중복 제거
    logger.info("\n[Deduplicating across categories...")
    all_articles = []
    for articles in collected_data.values():
        all_articles.extend(articles)

    deduplicator_cross = Deduplicator()
    unique_articles = deduplicator_cross.deduplicate_cross_categories(all_articles)

    logger.info(f"Total unique articles: {len(unique_articles)}")

    return collected_data


def collect_external_alerts(settings) -> List[Dict]:
    """0404 게시판 날짜 범위(KST) 키워드 매칭 공지를 수집한다."""
    logger = logging.getLogger("news_collector")
    logger.info("\n=== Collecting 0404 External Alerts ===")

    try:
        window = get_collection_window_kst(window_hours=settings.time_window_hours)
        start_date_kst = window.start_kst.strftime("%Y-%m-%d")
        end_date_kst = window.end_kst.strftime("%Y-%m-%d")
        logger.info(
            f"[0404] Date window (KST): {start_date_kst} ~ {end_date_kst} "
            f"(time boundary {window.start_kst.strftime('%H:%M')}~{window.end_kst.strftime('%H:%M')})"
        )
        collector = Mofa0404Collector(debug_mode=settings.debug_mode)
        alerts = collector.collect_keyword_posts_by_date_range(start_date_kst, end_date_kst)
        logger.info(f"External alerts collected: {len(alerts)}")
        return alerts
    except Exception as e:
        logger.error(f"External alert collection failed: {e}")
        return []


def analyze_articles(collected_data: Dict, settings) -> Dict:
    """
    AI 분석 메인 함수

    Args:
        collected_data: 수집된 데이터
        settings: 설정 객체

    Returns:
        분석된 데이터
    """
    logger = logging.getLogger("news_collector")
    logger.info("\n=== Starting AI Analysis ===")

    # STEP 1: 기사 요약 (GPT-4o-mini)
    logger.info("STEP 1: Summarizing articles with gpt-4o-mini-2024-07-18...")
    summarizer = Summarizer(
        api_key=settings.api.openai_api_key,
        base_url=settings.api.openai_base_url,
        model=settings.api.model_basic
    )

    summary_data = summarizer.analyze(collected_data)

    # STEP 2: 전략 인사이트 (GPT-5)
    logger.info("STEP 2: Generating insights with gpt-4o-mini-2024-07-18...")
    insight_generator = InsightGenerator(
        api_key=settings.api.openai_api_key,
        base_url=settings.api.openai_base_url,
        model=settings.api.model_advanced
    )

    insight_data = insight_generator.analyze(summary_data)

    # 데이터 병합
    final_data = {**insight_data}

    # 카테고리별 섹션 데이터 추가
    for category, summaries in summary_data.items():
        final_data[f'section_{category}'] = summaries

    logger.info("AI Analysis completed")

    return final_data


def send_report(analyzed_data: Dict, settings):
    """
    리포트 발송 메인 함수

    Args:
        analyzed_data: 분석된 데이터
        settings: 설정 객체
    """
    logger = logging.getLogger("news_collector")
    logger.info("\n=== Sending Report ===")

    # 이메일 생성 및 발송
    logger.info("Generating email...")
    email_formatter = EmailFormatter()
    html_content = email_formatter.format(analyzed_data)

    logger.info("Sending email...")
    smtp_sender = SMTPSender(
        user=settings.email.gmail_user,
        password=settings.email.gmail_app_password
    )

    report_recipients = get_group_recipients("report")
    if not report_recipients:
        logger.warning("No report recipients configured. Skipping report email.")
    else:
        try:
            smtp_sender.send(html_content, report_recipients)
            logger.info(f"Report email sent successfully to {len(report_recipients)} recipients")
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            raise

    alerts = analyzed_data.get('external_alerts', [])
    send_safety_alert_notification(alerts, settings)

    # 웹 페이지 생성
    logger.info("Generating web page...")
    web_generator = WebGenerator()
    web_generator.generate(analyzed_data)

    logger.info("Report generation completed")


def send_safety_alert_notification(alerts: List[Dict], settings) -> bool:
    """
    해외 안전 공지 전용 알림 메일 발송

    Args:
        alerts: 해외 안전 공지 리스트
        settings: 설정 객체

    Returns:
        발송 성공 여부
    """
    logger = logging.getLogger("news_collector")

    if not alerts:
        logger.info("No external alerts. Skipping safety alert email.")
        return False

    recipients = get_group_recipients("safety_alert")
    if not recipients:
        logger.warning("No safety alert recipients configured. Skipping safety alert email.")
        return False

    email_formatter = EmailFormatter()
    html_content = email_formatter.format_safety_alert_digest(alerts)
    smtp_sender = SMTPSender(
        user=settings.email.gmail_user,
        password=settings.email.gmail_app_password
    )

    try:
        smtp_sender.send(
            html_content=html_content,
            recipients=recipients,
            subject_prefix="[SKT 로밍팀] 해외 안전 공지 알림"
        )
        logger.info(f"Safety alert email sent successfully to {len(recipients)} recipients")
        return True
    except Exception as e:
        logger.error(f"Safety alert email send failed: {e}")
        return False


class NewsCollector:
    """뉴스 수집기 클래스 - 웹 인터페이스를 위한 통합 인터페이스"""

    def __init__(self):
        """뉴스 수집기 초기화"""
        self.settings = load_settings()
        self.logger = setup_logger(debug_mode=self.settings.debug_mode)

    def collect_all_categories(self):
        """모든 카테고리에서 뉴스 수집"""
        self.logger.info("=== Starting News Collection ===")
        collected_data = collect_articles(self.settings)
        return collected_data

    def collect_external_alerts(self):
        self.logger.info("=== Collecting 0404 External Alerts ===")
        return collect_external_alerts(self.settings)

    def analyze_news(self, collected_data):
        """수집된 뉴스 분석"""
        self.logger.info("=== Starting AI Analysis ===")
        analyzed_data = analyze_articles(collected_data, self.settings)
        return analyzed_data

    def save_results(self, analyzed_data):
        """분석 결과 저장 (웹 페이지 생성)"""
        self.logger.info("=== Saving Results ===")
        # 웹 페이지만 생성 (이메일 발송 제외)
        from notifiers.web_generator import WebGenerator
        web_generator = WebGenerator()
        web_generator.generate(analyzed_data)
        self.logger.info("Results saved successfully")
        return True

    def run_full_pipeline(self):
        """전체 파이프라인 실행 (수집 -> 분석 -> 저장)"""
        collected_data = self.collect_all_categories()

        if not collected_data:
            self.logger.error("[ERROR] No articles collected")
            return None

        analyzed_data = self.analyze_news(collected_data)
        analyzed_data['external_alerts'] = self.collect_external_alerts()
        self.save_results(analyzed_data)

        return analyzed_data


def main():
    """메인 실행 함수"""
    # 윈도우 환경에서 한글 출력을 위한 인코딩 설정
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 먼저 기본 로거 초기화 (설정 로드 전)
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    logger = logging.getLogger("news_collector_init")

    try:
        # 설정 로드
        settings = load_settings()

        # 상세 로거 초기화 (설정 로드 후)
        logger = setup_logger(debug_mode=settings.debug_mode)
        logger.info("=== NewsCollector v2.0 Started ===")
        logger.info(f"Debug Mode: {settings.debug_mode}")

        # 1. 데이터 수집
        collected_data = collect_articles(settings)

        if not collected_data:
            logger.error("[ERROR] No articles collected")
            return

        # 2. AI 분석
        analyzed_data = analyze_articles(collected_data, settings)
        analyzed_data['external_alerts'] = collect_external_alerts(settings)

        # 3. 리포트 발송
        send_report(analyzed_data, settings)

        logger.info("\n=== NewsCollector v2.0 Completed Successfully ===")

    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        logger.error("Please check your .env file")
    except NewsCollectorError as e:
        logger.error(f"Application Error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected Error: {e}")


if __name__ == "__main__":
    main()

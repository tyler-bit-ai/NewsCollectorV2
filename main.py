"""
SKT 로밍팀 뉴스 수집 시스템 메인 실행 파일
"""
import yaml
import logging
from typing import Dict, List

from config.settings import load_settings
from utils.logger import setup_logger
from utils.exceptions import NewsCollectorError

# 수집 계층
from collectors.naver_collector import NaverCollector
from collectors.google_collector import GoogleCollector

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

    time_filter = TimeFilter(window_hours=settings.time_window_hours)
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
    logger.info("STEP 1: Summarizing articles with GPT-4o-mini...")
    summarizer = Summarizer(
        api_key=settings.api.openai_api_key,
        base_url=settings.api.openai_base_url,
        model=settings.api.model_basic
    )

    summary_data = summarizer.analyze(collected_data)

    # STEP 2: 전략 인사이트 (GPT-5)
    logger.info("STEP 2: Generating insights with GPT-5...")
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

    try:
        smtp_sender.send(html_content, settings.email.recipients)
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise

    # 웹 페이지 생성
    logger.info("Generating web page...")
    web_generator = WebGenerator()
    web_generator.generate(analyzed_data)

    logger.info("Report generation completed")


def main():
    """메인 실행 함수"""
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

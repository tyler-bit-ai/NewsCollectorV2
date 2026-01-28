"""
환경 변수 및 설정 관리
"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

# .env 파일 로드
load_dotenv()


@dataclass
class APISettings:
    """API 설정"""
    # Naver
    naver_client_id: str
    naver_client_secret: str

    # Google
    google_api_key: str
    search_engine_id: str

    # OpenAI
    openai_api_key: str
    openai_base_url: str
    model_basic: str = "gpt-4o-mini"
    model_advanced: str = "gpt-5"


@dataclass
class EmailSettings:
    """이메일 설정"""
    gmail_user: str
    gmail_app_password: str
    recipients: List[str]


@dataclass
class Settings:
    """전체 설정"""
    api: APISettings
    email: EmailSettings
    debug_mode: bool = False
    time_window_hours: int = 24
    max_articles_per_category: int = 10


def load_settings() -> Settings:
    """
    환경 변수 로드

    Returns:
        설정 객체

    Raises:
        ValueError: 필수 환경 변수 누락 시
    """
    # 필수 환경 변수 체크
    required_vars = {
        'NAVER_CLIENT_ID': os.getenv('NAVER_CLIENT_ID'),
        'NAVER_CLIENT_SECRET': os.getenv('NAVER_CLIENT_SECRET'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'SEARCH_ENGINE_ID': os.getenv('SEARCH_ENGINE_ID'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'OPENAI_BASE_URL': os.getenv('OPENAI_BASE_URL'),
        'GMAIL_USER': os.getenv('GMAIL_USER'),
        'GMAIL_APP_PASSWORD': os.getenv('GMAIL_APP_PASSWORD'),
    }

    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # 수신자 처리
    recipients_str = os.getenv('EMAIL_RECIPIENTS', '')
    recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]

    if not recipients:
        raise ValueError("EMAIL_RECIPIENTS is empty")

    return Settings(
        api=APISettings(
            naver_client_id=required_vars['NAVER_CLIENT_ID'],
            naver_client_secret=required_vars['NAVER_CLIENT_SECRET'],
            google_api_key=required_vars['GOOGLE_API_KEY'],
            search_engine_id=required_vars['SEARCH_ENGINE_ID'],
            openai_api_key=required_vars['OPENAI_API_KEY'],
            openai_base_url=required_vars['OPENAI_BASE_URL'],
            model_basic=os.getenv('OPENAI_MODEL_BASIC', 'gpt-4o-mini'),
            model_advanced=os.getenv('OPENAI_MODEL_ADVANCED', 'gpt-5')
        ),
        email=EmailSettings(
            gmail_user=required_vars['GMAIL_USER'],
            gmail_app_password=required_vars['GMAIL_APP_PASSWORD'],
            recipients=recipients
        ),
        debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
        time_window_hours=int(os.getenv('TIME_WINDOW_HOURS', '24')),
        max_articles_per_category=int(os.getenv('MAX_ARTICLES_PER_CATEGORY', '10'))
    )

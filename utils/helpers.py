"""
유틸리티 헬퍼 함수
"""
import re
from typing import Dict, Tuple


ASCII_ALPHA_PATTERN = re.compile(r"[A-Za-z]")
GLOBAL_TREND_TITLE_FALLBACK = "해외 로밍 동향 기사(한글 번역 준비중)"
GLOBAL_TREND_SUMMARY_FALLBACK = "한글 요약 준비중입니다. 원문 링크에서 확인해 주세요."


def clean_html(text: str) -> str:
    """
    HTML 태그 정리

    Args:
        text: 원본 텍스트

    Returns:
        정리된 텍스트
    """
    return (text
            .replace('<b>', '')
            .replace('</b>', '')
            .replace('&quot;', '"'))


def normalize_title(title: str) -> str:
    """
    제목 정규화 (중복 제거용)

    Args:
        title: 원본 제목

    Returns:
        정규화된 제목
    """
    return (title
            .replace(' ', '')
            .replace('<b>', '')
            .replace('</b>', '')
            .replace('&quot;', '')
            .lower())


def contains_ascii_alpha(text: str) -> bool:
    """영문 알파벳 포함 여부를 반환한다."""
    return bool(ASCII_ALPHA_PATTERN.search(str(text or "")))


def ensure_global_trend_korean_text(title: str, summary: str) -> Tuple[str, str]:
    """
    Global Roaming Trend 항목의 제목/요약에서 영문 노출을 차단한다.
    영문이 포함되면 한글 대체 문구로 치환한다.
    """
    safe_title = str(title or "").strip()
    safe_summary = str(summary or "").strip()

    if not safe_title or contains_ascii_alpha(safe_title):
        safe_title = GLOBAL_TREND_TITLE_FALLBACK
    if not safe_summary or contains_ascii_alpha(safe_summary):
        safe_summary = GLOBAL_TREND_SUMMARY_FALLBACK

    return safe_title, safe_summary

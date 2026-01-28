"""
유틸리티 헬퍼 함수
"""
from typing import Dict


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

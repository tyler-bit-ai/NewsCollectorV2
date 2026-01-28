"""
로깅 시스템 (일별 파일)
"""
import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir: str = "output/logs", debug_mode: bool = False) -> logging.Logger:
    """
    로거 설정 (일별 파일)

    Args:
        log_dir: 로그 디렉토리
        debug_mode: 디버그 모드

    Returns:
        설정된 로거
    """
    # 로그 디렉토리 생성
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 일별 로그 파일
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"news_collector_{today}.log")

    # 로거 생성
    logger = logging.getLogger("news_collector")
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # 핸들러 초기화 방지
    if logger.handlers:
        return logger

    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # 포맷
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

"""
간편 실행 스크립트
"""
import sys
import os

# 프로젝트 루트 경로를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()

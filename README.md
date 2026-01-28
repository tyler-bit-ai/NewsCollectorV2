# NewsCollector v2.0

SKT 로밍팀을 위한 뉴스 수집 및 AI 분석 시스템

## 📋 개요

6개 카테고리로 기사를 자동 수집하고, AI가 2단계 분석을 수행한 후 이메일과 웹 페이지로 발송합니다.

## ✨ 주요 기능

- **자동 뉴스 수집**: Naver News, Blog, Cafe 및 Google Search API
- **스마트 필터링**: 시간 기반(24시간), 키워드 기반 필터링
- **중복 제거**: 카테고리 내/간 중복 제거
- **AI 2단계 분석**:
  - STEP 1: GPT-4o-mini 기사 요약
  - STEP 2: GPT-5 전략 인사이트 생성
- **멀티 채널 발송**: 이메일 + 웹 페이지

## 🚀 설치

### 1. Python 설치

Python 3.9 이상 필요합니다.

```bash
python --version
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 API 키를 입력하세요.

```bash
cp .env.example .env
```

`.env` 파일 수정:

```bash
# Naver Search API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Google Custom Search API
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.platform.a15t.com/v1

# Gmail SMTP
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Recipients (comma separated)
EMAIL_RECIPIENTS=user1@sk.com,user2@sk.com
```

## 🎯 사용법

### 기본 실행

```bash
python run.py
```

또는

```bash
python main.py
```

### 디버그 모드

`.env` 파일에서 설정:

```bash
DEBUG_MODE=true
```

## 📁 프로젝트 구조

```
NewsCollector_v2.0/
├── config/                 # 설정 파일
│   ├── settings.py         # 환경 변수 로드
│   └── categories.yaml     # 카테고리/키워드 설정
├── collectors/             # 데이터 수집 계층
├── filters/                # 필터링 계층
├── analyzers/              # AI 분석 계층
├── notifiers/              # 발송 계층
├── utils/                  # 유틸리티
├── output/                 # 출력 파일
│   ├── logs/              # 로그 파일
│   ├── web/               # 웹 페이지
│   └── backups/           # 이메일 백업
├── main.py                 # 메인 실행 파일
├── run.py                  # 간편 실행 스크립트
├── requirements.txt
├── .env.example
└── README.md
```

## 📊 카테고리

| ID | 카테고리 | 설명 |
|----|---------|------|
| 0 | Market & Culture | 여행 트렌드, 한류 |
| 1 | Global Trend | 글로벌 로밍 산업 |
| 2 | Competitors | SKT/KT/LGU+ 경쟁 현황 |
| 3 | eSIM Products | eSIM 제품/회사 |
| 4 | 로밍 VoC | 로밍 고객 후기 |
| 5 | eSIM VoC | eSIM 고객 후기 |

## 🔧 설정

### 카테고리/키워드 수정

`config/categories.yaml` 파일을 수정하세요.

### 필터링 설정

`config/categories.yaml`의 `filters` 섹션에서:

- `blacklist_domains`: 제외할 도메인 패턴
- `excluded_keywords`: 제외할 키워드 (게임, 광고 등)

## 📝 로그

로그 파일은 `output/logs/` 디렉토리에 일별로 생성됩니다.

```
output/logs/
├── news_collector_20260128.log
├── news_collector_20260127.log
└── ...
```

## 🌐 웹 인터페이스

생성된 웹 리포트는 `output/web/daily_report.html`에서 확인할 수 있습니다.

브라우저에서 파일을 열어 확인하세요.

## ⚠️ 에러 핸들링

### 3단계 에러 핸들링

1. **재시도**: API 호출 실패 시 최대 3회 재시도
2. **대체 로직**: GPT-5 실패 시 GPT-4o로 대체
3. **에러 알림**: 로그 파일에 상세 기록

### 이메일 발송 실패 시

`output/backups/` 디렉토리에 HTML 파일로 백업됩니다.

## 🛠️ 개발

### 모듈 추가

각 계층에 새로운 모듈을 쉽게 추가할 수 있습니다.

- `collectors/`: 새로운 데이터 소스
- `filters/`: 새로운 필터링 로직
- `analyzers/`: 새로운 AI 분석기
- `notifiers/`: 새로운 발송 채널

## 📄 라이선스

SKT 내부 사용용

## 📞 지원

문제가 발생하면 `output/logs/`의 로그 파일을 확인하세요.

---

**버전**: 2.0
**작성일**: 2026-01-28

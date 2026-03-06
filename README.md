# NewsCollector v2.0

SKT 로밍팀을 위한 뉴스 수집 및 AI 분석 시스템

## 📋 개요

6개 카테고리의 기사/게시글을 자동 수집하고, AI 2단계 분석 후 결과를 웹/이메일로 배포합니다.  
추가로 외교부 0404(해외안전여행) 게시판의 당일 통신 이슈 공지도 별도 수집합니다.

## ✨ 주요 기능

- 자동 뉴스 수집
- Naver News / Blog / Cafe Search API
- Google Custom Search API
- 0404.go.kr 공관안전공지/안전공지 당일 통신 차단 이슈 조합 매칭 수집
- 스마트 필터링
- 시간 필터 (`TIME_WINDOW_HOURS`, 기본 24시간)
  - 월요일(KST) 실행 시: 금요일 09:00 ~ 월요일 09:00 고정 구간
- 키워드/도메인 필터 (`config/categories.yaml`)
- 중복 제거
- 카테고리 내 중복 제거: 제목 정규화 + URL
- 카테고리 간 중복 제거: URL 기준(현재는 로그/통계 용도로 수행)
- AI 2단계 분석
- STEP 1: 기사 요약 (`OPENAI_MODEL_BASIC`, 기본 `gpt-4o-mini-2024-07-18`)
  - `global_trend` 카테고리 제목/요약은 한국어로 번역 생성
- STEP 2: 전략 인사이트 생성 (`OPENAI_MODEL_ADVANCED`, 기본 `gpt-4o-mini-2024-07-18`)
- 멀티 채널 결과 생성
- 웹 리포트 HTML 생성 (`output/web/daily_report.html`)
  - 실행 시각별 이력 저장 (`output/web/history/daily_report_YYYYMMDD_HHMMSS.html`)
- 이메일 HTML 포맷 후 SMTP 발송
- 가독성 최적화 레이아웃
  - 카테고리별 핵심 `Top N` 카드 + 나머지 링크 목록으로 압축 표시
  - 요약 본문 길이 자동 절단(`EMAIL_SUMMARY_MAX_CHARS`, `WEB_SUMMARY_MAX_CHARS`)
- 해외 안전 공지 전용 알림 메일 자동 발송 (당일 공지 존재 시)
- 수신자 그룹 분리/영속화
  - 일반 리포트 수신자
  - 해외 안전 공지 수신자

## 🚀 설치

### 1. Python 설치

Python 3.9 이상 필요

```bash
python --version
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

코드에서 `python-dotenv`를 사용하므로 누락 시 아래도 추가 설치하세요.

```bash
pip install python-dotenv
```

### 3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 생성

```bash
cp .env.example .env
```

`.env` 주요 항목:

```bash
# Naver
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# Google CSE
GOOGLE_API_KEY=...
SEARCH_ENGINE_ID=...

# OpenAI
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_BASIC=gpt-4o-mini-2024-07-18
OPENAI_MODEL_ADVANCED=gpt-4o-mini-2024-07-18

# Gmail SMTP
GMAIL_USER=...
GMAIL_APP_PASSWORD=...

# 레거시 호환용(선택)
EMAIL_RECIPIENTS=user1@sk.com,user2@sk.com

# 옵션
DEBUG_MODE=false
TIME_WINDOW_HOURS=24
MAX_ARTICLES_PER_CATEGORY=10
EMAIL_TOP_N=3
EMAIL_SUMMARY_MAX_CHARS=140
WEB_DEFAULT_VISIBLE_N=3
WEB_SUMMARY_MAX_CHARS=180
```

- `EMAIL_TOP_N`: 메일에서 카테고리별 카드로 보여줄 핵심 기사 수
- `EMAIL_SUMMARY_MAX_CHARS`: 메일 summary 최대 길이
- `WEB_DEFAULT_VISIBLE_N`: 웹 리포트에서 기본 노출 카드 수
- `WEB_SUMMARY_MAX_CHARS`: 웹 리포트 summary 최대 길이

## 🎯 사용법

### CLI 전체 파이프라인 실행

```bash
python run.py
```

또는

```bash
python main.py
```

실행 순서:

1. 카테고리별 수집
2. 시간/키워드 필터링 + 중복 제거
3. AI 요약/인사이트 생성
4. 0404 공지 수집 (기본 당일, 월요일은 주말 확장)
5. 이메일 발송 + 웹 리포트 생성

### Shrimp Task Manager 규칙 초기화

- 본 저장소는 shrimp 프로젝트 규칙 파일을 루트의 `shrimp-rules.md`로 관리합니다.
- Codex/Claude Code에서 shrimp를 사용할 때 아래 요청으로 규칙을 초기화/갱신합니다.

```text
init project rules
```

- 태스크 계획/실행 전 `shrimp-rules.md`를 우선 참조합니다.

### 웹 대시보드 실행

```bash
python start_web.py
```

접속: [http://localhost:5000](http://localhost:5000)

## 📁 프로젝트 구조

```
NewsCollector_v2.0/
├── config/
│   ├── settings.py
│   ├── categories.yaml
│   ├── email_recipients.json
│   └── recipient_store.py
├── collectors/
├── filters/
├── analyzers/
├── notifiers/
├── utils/
├── web/
├── output/
│   ├── logs/
│   ├── web/
│   └── backups/
├── main.py
├── run.py
├── start_web.py
└── README.md
```

## 📊 카테고리

| ID | 카테고리 | 소스 |
|----|---------|------|
| 0 | Market & Culture (Macro) | Naver News, Blog |
| 1 | Global Roaming Trend | Google Search |
| 2 | SKT & Competitors | Naver News |
| 3 | eSIM Products | Naver News |
| 4 | 로밍 VoC | Naver Blog, Cafe |
| 5 | eSIM VoC | Naver Blog, Cafe |

## 🔧 설정

### 카테고리/키워드

`config/categories.yaml`의 `categories`를 수정

### 필터

`config/categories.yaml`의 `filters`:

- `blacklist_domains`
- `excluded_keywords`

## 🌐 웹 대시보드 상세

### 기능

- 분석 비동기 실행(백그라운드 스레드)
- 진행률 표시(0→10→50→80→100)
- 수신자 그룹별 추가/삭제
  - 일반 리포트 수신자
  - 해외 안전 공지 수신자
- 최신 리포트 열기
- 저장된 리포트 목록 조회/선택 열기
- 최신 HTML 리포트 이메일 발송(일반 리포트 수신자 대상)
- 분석 완료 후 해외 안전 공지 존재 시 전용 알림 메일 자동 발송

### 주요 API

- `POST /api/analysis/start`
- `GET /api/analysis/status/<task_id>`
- `GET /api/recipients?group=report|safety_alert`
- `POST /api/recipients?group=report|safety_alert`
- `DELETE /api/recipients/<email>?group=report|safety_alert`
- `POST /api/email/send`
- `GET /api/latest-report`
- `GET /api/reports?limit=30`
- `GET /health`

## 📧 수신자 관리 방식 (중요)

- CLI(`main.py`)와 웹 대시보드 모두 `config/email_recipients.json`을 공통 사용
- 수신자 그룹:
  - `report_recipients`: 일반 리포트 메일 수신자
  - `safety_alert_recipients`: 해외 안전 공지 전용 메일 수신자
- 수신자 변경사항은 파일에 즉시 저장되어 재시작 후에도 유지

## 🛰️ 0404 외부 공지 수집

- 대상 게시판: 공관안전공지(`embsyNtc`), 안전공지(`safetyNtc`)
- 기준 날짜:
  - 기본: KST(Asia/Seoul) 당일
  - 월요일(KST) 실행 시: 금요일 09:00 ~ 월요일 09:00 구간을 날짜 기준으로 확장 수집
- 매칭 규칙(조합):
  - 채널 키워드: 로밍/인터넷/데이터/국제전화/통화/문자/SMS/MMS
  - 차단 키워드: 차단/중단/불가/장애/두절/제한
  - 두 그룹이 함께 등장할 때만 매칭 (예: `인터넷 차단`, `SMS 발신 불가`)
- 결과는 `external_alerts`로 리포트 상단 섹션에 포함
  - `external_alerts[].published_date`: 0404 게시판의 실제 게시일(`YYYY-MM-DD`)
- 해외 안전 공지 수집 건수 > 0 이면 전용 수신자에게 별도 알림 메일 자동 발송

### 0404 수집 단위 테스트 실행

```bash
python -m unittest tests/test_mofa_0404_collector.py -v
```

- 외부 사이트 접속 없이(mock 기반) 공관안전공지 수집 로직을 검증합니다.

## ⚠️ 에러 핸들링/재시도

- AI 호출: 최대 3회 재시도(지수 백오프)
- SMTP 발송: 최대 3회 재시도
- 이메일 발송 실패 시: `output/backups/email_backup_*.html` 저장
- 수집 API 실패 시: 로깅 후 가능한 범위 내 계속 진행

## 📝 로그/출력

- 로그: `output/logs/news_collector_YYYYMMDD.log`
- 웹 리포트(최신): `output/web/daily_report.html`
- 웹 리포트(이력): `output/web/history/daily_report_YYYYMMDD_HHMMSS.html`
- 이메일 실패 백업: `output/backups/*.html`

## 📄 라이선스

SKT 내부 사용용

## 📞 지원

문제 발생 시 `output/logs/` 확인

---

**버전**: 2.0  
**최종 업데이트**: 2026-03-04

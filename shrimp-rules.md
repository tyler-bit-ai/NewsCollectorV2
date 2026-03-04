# Development Guidelines

## Project Scope
- Python 기반 뉴스 수집/분석 파이프라인은 `main.py`를 단일 오케스트레이터로 유지하라.
- 웹 대시보드 API는 `web/routes.py`, 프론트 상호작용은 `web/static/js/dashboard.js`에서만 변경하라.
- 설정 소스는 `.env` + `config/settings.py`로 단일화하고, 하드코딩 설정을 추가하지 마라.

## Architecture Rules
- 수집 로직은 `collectors/`, 필터 로직은 `filters/`, AI 분석 로직은 `analyzers/`, 발송 로직은 `notifiers/`에만 추가하라.
- 공통 예외/재시도/시간창 계산은 `utils/`를 재사용하고 동일 기능을 다른 디렉터리에 중복 구현하지 마라.
- 신규 수집기 추가 시 `collectors/base.py` 인터페이스를 따르고 `main.py` 수집 파이프라인에 명시적으로 연결하라.

## Code Style Rules
- 기존 파일 스타일을 따라 Python 타입 힌트와 명시적 함수 경계를 유지하라.
- 사용자 표시 메시지(API 응답/대시보드 토스트)는 한국어 톤을 유지하라.
- 광범위 리팩터링보다 기능 단위 최소 변경을 우선하라.

## Required Sync Rules
- `config/settings.py`에서 환경 변수를 추가/수정하면 `.env.example`과 `README.md`를 반드시 동시에 수정하라.
- `web/routes.py` API 스펙을 변경하면 `web/static/js/dashboard.js`를 반드시 동시에 수정하라.
- 수신자 그룹 구조(`report`, `safety_alert`)를 변경하면 아래 파일을 동시에 수정하라.
  - `config/recipient_store.py`
  - `web/routes.py`
  - `web/static/js/dashboard.js`
  - `web/templates/dashboard.html`
  - `README.md`
- 결과 HTML 구조를 변경하면 아래를 함께 확인/수정하라.
  - `notifiers/templates/email_template.html`
  - `notifiers/templates/web_template.html`
  - `notifiers/email_formatter.py`
  - `README.md`의 출력/발송 설명
- 0404 수집 동작(키워드/날짜범위/게시판)을 변경하면 아래를 함께 수정하라.
  - `collectors/mofa_0404_collector.py`
  - `main.py`의 `collect_external_alerts` 흐름
  - `README.md`의 0404 설명
- 실행 진입점(`run.py`, `start_web.py`, `main.py`) 동작을 바꾸면 `README.md` 실행 절을 반드시 갱신하라.

## Validation Rules
- 파이프라인 변경 시 최소 `python run.py` 기준으로 예외 없이 시작 가능한지 검증하라.
- 웹 API 변경 시 `python start_web.py` 실행 후 대시보드 핵심 동선(분석 시작/수신자 조회)을 검증하라.
- 외부 API 실패 경로를 변경했으면 `output/backups/` 백업 동작과 로그 메시지를 확인하라.

## AI Decision Rules
- 요청이 모호해도 먼저 코드/README/AGENTS 규칙을 읽고 보수적 최소 변경안을 우선 적용하라.
- 변경 범위가 사용자 사용법(`CLI`, `웹`, `환경 변수`, `출력 파일`, `수신자 정책`)에 닿으면 반드시 `README.md`를 갱신하라.
- 기존 파일에 이미 구현된 패턴이 있으면 신규 추상화보다 기존 패턴 복제를 우선하라.

## Prohibited Actions
- AGENTS 규칙을 무시한 코드/동작 변경을 금지한다.
- 관련 없는 디렉터리 대규모 포맷팅 또는 네이밍 일괄 변경을 금지한다.
- API/환경 변수/출력 형식을 조용히 깨는 비호환 변경을 금지한다.

## Do / Don't Examples
- Do: `web/routes.py`에서 엔드포인트 응답 필드 변경 시 `dashboard.js` 파싱 로직과 `README.md` API 항목을 함께 수정하라.
- Don't: `routes.py`만 수정하고 프론트 파싱 코드를 그대로 두지 마라.
- Do: 새 환경 변수 추가 시 `settings.py` 기본값, `.env.example`, `README.md`를 동시에 업데이트하라.
- Don't: 코드에만 환경 변수를 추가하고 문서 반영을 누락하지 마라.

"""
대시보드/CLI 공통 수신자 저장소
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

RECIPIENTS_FILE = Path(__file__).parent / "email_recipients.json"

GROUP_TO_KEY = {
    "report": "report_recipients",
    "safety_alert": "safety_alert_recipients",
}

DEFAULT_REPORT_RECIPIENTS = [
    "sib1979@sk.com",
    "minchaekim@sk.com",
    "hyunju11.kim@sk.com",
    "jieun.baek@sk.com",
    "yjwon@sk.com",
    "letigon@sk.com",
    "lsm0787@sk.com",
    "maclogic@sk.com",
    "jungjaehoon@sk.com",
    "hw.cho@sk.com",
    "chlskdud0623@sk.com",
    "youngmin.choi@sk.com",
    "jinyeol.han@sk.com",
    "jeongwoo.hwang@sk.com",
    "funda@sk.com",
]


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    email = _normalize_email(email)
    if "@" not in email:
        return False
    domain = email.split("@", 1)[-1]
    return "." in domain and not email.startswith("@") and not email.endswith("@")


def _dedupe_emails(emails: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for email in emails:
        normalized = _normalize_email(email)
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _default_config() -> Dict[str, List[str]]:
    base = _dedupe_emails(DEFAULT_REPORT_RECIPIENTS)
    return {
        "schema_version": 2,
        "report_recipients": base,
        "safety_alert_recipients": list(base),
    }


def _migrate_or_normalize(raw: Dict) -> Tuple[Dict, bool]:
    if not isinstance(raw, dict):
        return _default_config(), True

    changed = False
    # v2 schema
    if "report_recipients" in raw or "safety_alert_recipients" in raw:
        report = _dedupe_emails(raw.get("report_recipients", []))
        safety = _dedupe_emails(raw.get("safety_alert_recipients", report))
        normalized = {
            "schema_version": 2,
            "report_recipients": report,
            "safety_alert_recipients": safety,
        }
        if raw.get("schema_version") != 2:
            changed = True
        if raw.get("report_recipients") != report:
            changed = True
        if raw.get("safety_alert_recipients") != safety:
            changed = True
        return normalized, changed

    # legacy schema
    legacy_default = raw.get("default_recipients", [])
    legacy_custom = raw.get("custom_recipients", [])
    report = _dedupe_emails(list(legacy_default) + list(legacy_custom))
    normalized = {
        "schema_version": 2,
        "report_recipients": report,
        "safety_alert_recipients": list(report),
    }
    return normalized, True


def _save_config(data: Dict) -> None:
    RECIPIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config() -> Dict:
    if not RECIPIENTS_FILE.exists():
        data = _default_config()
        _save_config(data)
        return data

    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        data = _default_config()
        _save_config(data)
        return data

    normalized, changed = _migrate_or_normalize(raw)
    if changed:
        _save_config(normalized)
    return normalized


def get_group_recipients(group: str = "report") -> List[str]:
    key = GROUP_TO_KEY.get(group, GROUP_TO_KEY["report"])
    config = load_config()
    return list(config.get(key, []))


def add_group_recipient(email: str, group: str = "report") -> Tuple[bool, str, List[str]]:
    key = GROUP_TO_KEY.get(group)
    if not key:
        return False, "유효하지 않은 그룹입니다", []

    email = _normalize_email(email)
    if not email:
        return False, "이메일 주소를 입력해주세요", []
    if not is_valid_email(email):
        return False, "올바른 이메일 형식이 아닙니다", []

    config = load_config()
    recipients = list(config.get(key, []))
    if email in recipients:
        return False, "이미 존재하는 이메일 주소입니다", recipients

    recipients.append(email)
    config[key] = recipients
    _save_config(config)
    return True, "이메일이 추가되었습니다", recipients


def remove_group_recipient(email: str, group: str = "report") -> Tuple[bool, str, List[str]]:
    key = GROUP_TO_KEY.get(group)
    if not key:
        return False, "유효하지 않은 그룹입니다", []

    email = _normalize_email(email)
    config = load_config()
    recipients = list(config.get(key, []))

    if email not in recipients:
        return False, "존재하지 않는 이메일 주소입니다", recipients

    recipients.remove(email)
    config[key] = recipients
    _save_config(config)
    return True, "이메일이 삭제되었습니다", recipients


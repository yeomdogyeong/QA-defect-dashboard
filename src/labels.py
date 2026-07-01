"""
표시용 한글 라벨 매핑.

데이터 자체는 영문 값을 유지(앱·CSV 호환)하고, 리포트/차트에 보일 때만
이 매핑으로 한글로 바꿔 표시한다.
"""

from __future__ import annotations

STATUS_KO = {
    "New": "신규", "In Progress": "진행 중", "Resolved": "해결됨",
    "Closed": "종료", "Reopened": "재오픈",
}
SEVERITY_KO = {
    "Blocker": "블로커", "Critical": "치명적", "Major": "중요",
    "Minor": "경미", "Trivial": "사소",
}
PRIORITY_KO = {
    "Immediate": "즉시", "High": "높음", "Normal": "보통", "Low": "낮음",
}
ROOT_CAUSE_KO = {
    "Requirement": "요구사항", "Design": "설계", "Coding": "코딩",
    "Environment": "환경", "Data": "데이터", "Third-party": "외부 연동",
}
MODULE_KO = {
    "Auth-Login": "인증·로그인", "Payment": "결제", "Search": "검색",
    "Notification": "알림", "Firmware-Core": "펌웨어 코어",
    "Network-Comm": "네트워크 통신", "UI-Settings": "UI 설정",
    "Data-Sync": "데이터 동기화",
}
PHASE_KO = {
    "Unit": "단위", "Integration": "통합", "System": "시스템",
    "UAT": "UAT", "Production": "운영",
}
COLUMN_KO = {
    "id": "ID", "summary": "요약", "module": "모듈", "severity": "심각도",
    "priority": "우선순위", "status": "상태", "reporter": "보고자",
    "assignee": "담당자", "created_date": "생성일", "resolved_date": "해결일",
    "reopen_count": "재오픈 횟수", "found_phase": "발견 단계", "root_cause": "근본원인",
}


def tr(values, mapping) -> list:
    """리스트/시리즈의 각 값을 매핑으로 변환. 매핑에 없으면 원본 유지."""
    return [mapping.get(v, v) for v in values]

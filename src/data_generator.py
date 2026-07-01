"""
샘플 결함 데이터 생성기.

원본 Mantis Dashboard의 mantis_simulator.py 역할.
실제 버그트래커가 없어도 대시보드 데모가 항상 돌아가도록,
현실적인 분포를 가진 결함(defect) 데이터를 생성한다.

생성 스키마는 Mantis / Jira / Redmine CSV export를 최대공약수로 맞춘 것.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---- 컬럼 이름 상수 (metrics.py와 공유) ------------------------------------
COL_ID = "id"
COL_SUMMARY = "summary"
COL_MODULE = "module"
COL_SEVERITY = "severity"
COL_PRIORITY = "priority"
COL_STATUS = "status"
COL_REPORTER = "reporter"
COL_ASSIGNEE = "assignee"
COL_CREATED = "created_date"
COL_RESOLVED = "resolved_date"
COL_REOPEN = "reopen_count"
COL_PHASE = "found_phase"      # 결함을 발견한 테스트 단계
COL_ROOT_CAUSE = "root_cause"

SEVERITIES = ["Blocker", "Critical", "Major", "Minor", "Trivial"]
PRIORITIES = ["Immediate", "High", "Normal", "Low"]
STATUSES = ["New", "In Progress", "Resolved", "Closed", "Reopened"]
MODULES = [
    "Auth-Login", "Payment", "Search", "Notification",
    "Firmware-Core", "Network-Comm", "UI-Settings", "Data-Sync",
]
# Production = 출시 후 발견 = 유출(escape). 단계 순서가 뒤로 갈수록 유출에 가깝다.
PHASES = ["Unit", "Integration", "System", "UAT", "Production"]
ROOT_CAUSES = ["Requirement", "Design", "Coding", "Environment", "Data", "Third-party"]
REPORTERS = ["qa_kim", "qa_lee", "qa_park", "qa_choi", "qa_jung"]
ASSIGNEES = ["dev_han", "dev_seo", "dev_yoon", "dev_oh", "dev_baek", "dev_shin"]

# 심각도별 평균 해결 소요일(일). 심각할수록 빨리 처리된다고 가정.
_RESOLVE_DAYS = {
    "Blocker": 1.5, "Critical": 3.0, "Major": 6.0, "Minor": 12.0, "Trivial": 20.0,
}


def generate_defects(n: int = 500, seed: int = 42, days: int = 180) -> pd.DataFrame:
    """
    n개의 결함 레코드를 생성한다.

    Args:
        n: 생성할 결함 수
        seed: 재현성을 위한 난수 시드
        days: 최근 며칠 범위에 결함을 분포시킬지

    Returns:
        결함 DataFrame (스키마는 위 COL_* 상수 참조)
    """
    rng = np.random.default_rng(seed)
    today = pd.Timestamp.now().normalize()
    start = today - pd.Timedelta(days=days)

    # 생성 시각: 최근일수록 조금 더 많게 (선형 가중)
    offsets = rng.triangular(0, days, days, size=n)
    created = start + pd.to_timedelta(offsets, unit="D")

    severity = rng.choice(SEVERITIES, size=n, p=[0.06, 0.14, 0.35, 0.30, 0.15])
    priority = rng.choice(PRIORITIES, size=n, p=[0.10, 0.30, 0.45, 0.15])
    module = rng.choice(MODULES, size=n)
    # 모듈별 결함 편중을 만들기 위해 두 모듈에 가중치를 더 준다 → 이상탐지 데모용
    hot = rng.random(n) < 0.18
    module = np.where(hot, rng.choice(["Payment", "Network-Comm"], size=n), module)

    phase = rng.choice(PHASES, size=n, p=[0.28, 0.27, 0.22, 0.13, 0.10])
    root_cause = rng.choice(ROOT_CAUSES, size=n, p=[0.18, 0.17, 0.34, 0.13, 0.10, 0.08])
    reporter = rng.choice(REPORTERS, size=n)
    assignee = rng.choice(ASSIGNEES, size=n)

    # 상태 분포. 대부분 종료, 일부 진행/재오픈.
    status = rng.choice(STATUSES, size=n, p=[0.10, 0.12, 0.15, 0.55, 0.08])

    # 재오픈 횟수: Reopened면 최소 1, 그 외 대부분 0
    reopen = np.where(
        status == "Reopened",
        rng.integers(1, 3, size=n),
        (rng.random(n) < 0.06).astype(int),
    )

    # 해결일: Resolved/Closed만 값이 있고, 나머지는 NaT
    resolve_days = np.array([_RESOLVE_DAYS[s] for s in severity])
    noise = rng.gamma(shape=2.0, scale=0.6, size=n)  # 오른쪽 꼬리 있는 현실적 분포
    duration = np.clip(resolve_days * noise, 0.1, None)
    resolved = created + pd.to_timedelta(duration, unit="D")
    is_done = np.isin(status, ["Resolved", "Closed"])
    resolved = pd.Series(resolved).where(is_done, pd.NaT)
    # 미래로 넘어간 해결일은 잘라낸다
    resolved = resolved.where(resolved <= today, pd.NaT)

    df = pd.DataFrame({
        COL_ID: np.arange(1, n + 1),
        COL_SUMMARY: [f"[{m}] 결함 #{i}" for i, m in zip(range(1, n + 1), module)],
        COL_MODULE: module,
        COL_SEVERITY: severity,
        COL_PRIORITY: priority,
        COL_STATUS: status,
        COL_REPORTER: reporter,
        COL_ASSIGNEE: assignee,
        COL_CREATED: pd.to_datetime(created).normalize(),
        COL_RESOLVED: pd.to_datetime(resolved).dt.normalize(),
        COL_REOPEN: reopen.astype(int),
        COL_PHASE: phase,
        COL_ROOT_CAUSE: root_cause,
    })
    return df.sort_values(COL_CREATED).reset_index(drop=True)


if __name__ == "__main__":
    d = generate_defects()
    print(d.head(10).to_string())
    print(f"\n총 {len(d)}건 생성. 상태 분포:\n{d[COL_STATUS].value_counts()}")

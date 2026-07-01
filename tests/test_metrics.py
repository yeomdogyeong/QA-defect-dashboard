"""
지표 함수 단위 테스트.

핵심 지표(재오픈율/유출률/MTTR/이상탐지 등)를 손으로 만든 작은
DataFrame으로 검증한다. 기대값을 사람이 계산할 수 있을 만큼 작게 유지.

실행:  pytest -v
"""

import pandas as pd
import pytest

from src import metrics as M
from src.data_generator import (
    COL_CREATED, COL_MODULE, COL_PHASE, COL_REOPEN, COL_RESOLVED,
    COL_SEVERITY, COL_STATUS, generate_defects,
)


@pytest.fixture
def tiny() -> pd.DataFrame:
    """기대값을 손으로 계산할 수 있는 6건짜리 고정 데이터셋."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6],
        COL_MODULE: ["A", "A", "A", "B", "B", "C"],
        COL_SEVERITY: ["Major", "Minor", "Major", "Critical", "Minor", "Trivial"],
        COL_STATUS: ["Closed", "Closed", "New", "In Progress", "Reopened", "Closed"],
        COL_REOPEN: [0, 0, 0, 0, 2, 0],          # 6건 중 1건 재오픈 → 1/6
        COL_PHASE: ["Unit", "Production", "System", "Production", "UAT", "Unit"],  # 2/6 유출
        COL_CREATED: pd.to_datetime(
            ["2024-01-01", "2024-01-01", "2024-01-10",
             "2024-01-05", "2024-01-02", "2024-01-01"]),
        COL_RESOLVED: pd.to_datetime(
            ["2024-01-05", "2024-01-04", None, None, None, "2024-01-02"]),
        # 해결 소요: 4일, 3일, -, -, -, 1일 → 평균 (4+3+1)/3 = 2.6667
    })


def test_reopen_rate(tiny):
    assert M.reopen_rate(tiny) == pytest.approx(1 / 6)


def test_escape_rate(tiny):
    # Production 발견 2건 / 6건
    assert M.escape_rate(tiny) == pytest.approx(2 / 6)


def test_mttr_days(tiny):
    assert M.mttr_days(tiny) == pytest.approx((4 + 3 + 1) / 3)


def test_severity_distribution_counts(tiny):
    d = M.severity_distribution(tiny).set_index(COL_SEVERITY)["count"].to_dict()
    assert d == {"Major": 2, "Minor": 2, "Critical": 1, "Trivial": 1}


def test_density_sorted_desc(tiny):
    dens = M.defect_density_by_module(tiny)
    assert dens.iloc[0][COL_MODULE] == "A"        # A가 3건으로 최다
    assert list(dens["count"]) == sorted(dens["count"], reverse=True)


def test_aging_marks_stale(tiny):
    today = pd.Timestamp("2024-02-15")            # 1/10 New → 36일 경과
    ag = M.aging(tiny, today=today, stale_days=30)
    # open = New, In Progress, Reopened → 3건
    assert len(ag) == 3
    assert ag["is_stale"].sum() >= 1
    assert ag.iloc[0]["age_days"] >= ag.iloc[-1]["age_days"]   # 내림차순


def test_kpi_summary_keys(tiny):
    k = M.kpi_summary(tiny)
    assert set(k) == {"total", "open", "reopen_rate", "escape_rate", "mttr_days"}
    assert k["total"] == 6
    assert k["open"] == 3


def test_empty_df_is_safe():
    empty = generate_defects(n=0)
    assert M.reopen_rate(empty) == 0.0
    assert M.escape_rate(empty) == 0.0
    assert M.mttr_days(empty) == 0.0


def test_anomaly_flags_hot_module():
    # C 모듈에 결함을 몰아주면 이상으로 잡혀야 한다
    df = pd.DataFrame({
        COL_MODULE: ["A", "B", "C", "C", "C", "C", "C", "C", "C", "C"],
    })
    # 나머지 컬럼 보강
    for col, val in [(COL_SEVERITY, "Major"), (COL_STATUS, "New"),
                     (COL_PHASE, "Unit"), (COL_REOPEN, 0)]:
        df[col] = val
    df[COL_CREATED] = pd.Timestamp("2024-01-01")
    df[COL_RESOLVED] = pd.NaT
    res = M.anomaly_modules(df, z_threshold=1.0)
    hot = res[res[COL_MODULE] == "C"].iloc[0]
    assert bool(hot["is_anomaly"]) is True


def test_trend_columns(tiny):
    tr = M.defect_trend(tiny, freq="W")
    assert list(tr.columns) == ["period", "created", "resolved"]
    assert tr["created"].sum() == 6

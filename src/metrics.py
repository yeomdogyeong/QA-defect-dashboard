"""
QA 지표 계산 로직.

모든 함수는 '순수 함수'로 작성한다:
- 입력은 DataFrame, 출력은 DataFrame/dict/스칼라
- 전역 상태·파일 I/O·랜덤 없음
=> tests/test_metrics.py 에서 손쉽게 단위 테스트 가능.
"이 도구를 만든 QA가 자기 코드도 테스트로 검증한다"는 어필 포인트.
"""

from __future__ import annotations

import pandas as pd

from src.data_generator import (
    COL_CREATED, COL_MODULE, COL_PHASE, COL_PRIORITY, COL_REOPEN,
    COL_RESOLVED, COL_ROOT_CAUSE, COL_SEVERITY, COL_STATUS,
)

OPEN_STATUSES = ["New", "In Progress", "Reopened"]
ESCAPE_PHASE = "Production"  # 출시 후 발견 = 유출


def severity_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """심각도별 결함 건수. columns=[severity, count]"""
    out = df[COL_SEVERITY].value_counts().rename_axis(COL_SEVERITY).reset_index(name="count")
    return out


def status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """상태별 결함 건수."""
    return df[COL_STATUS].value_counts().rename_axis(COL_STATUS).reset_index(name="count")


def defect_density_by_module(df: pd.DataFrame) -> pd.DataFrame:
    """모듈별 결함 건수 (밀도). 많은 순 정렬."""
    return (
        df[COL_MODULE].value_counts()
        .rename_axis(COL_MODULE).reset_index(name="count")
        .sort_values("count", ascending=False).reset_index(drop=True)
    )


def root_cause_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """근본원인(RCA)별 건수."""
    return df[COL_ROOT_CAUSE].value_counts().rename_axis(COL_ROOT_CAUSE).reset_index(name="count")


def reopen_rate(df: pd.DataFrame) -> float:
    """재오픈율 = (재오픈 이력이 1회 이상인 결함) / 전체. 0~1."""
    if len(df) == 0:
        return 0.0
    return float((df[COL_REOPEN] > 0).mean())


def escape_rate(df: pd.DataFrame) -> float:
    """
    결함 유출률(Escape/Leakage) = Production 단계에서 발견된 결함 / 전체.
    낮을수록 출시 전 테스트가 결함을 잘 잡았다는 뜻. 0~1.
    """
    if len(df) == 0:
        return 0.0
    return float((df[COL_PHASE] == ESCAPE_PHASE).mean())


def mttr_days(df: pd.DataFrame) -> float:
    """
    평균 해결 소요시간(Mean Time To Resolve, 일 단위).
    resolved_date가 있는 결함만 대상. 값 없으면 0.0.
    """
    resolved = df.dropna(subset=[COL_RESOLVED])
    if len(resolved) == 0:
        return 0.0
    delta = (resolved[COL_RESOLVED] - resolved[COL_CREATED]).dt.total_seconds() / 86400.0
    return float(delta.mean())


def mttr_by_severity(df: pd.DataFrame) -> pd.DataFrame:
    """심각도별 평균 해결 소요일. columns=[severity, mttr_days]"""
    resolved = df.dropna(subset=[COL_RESOLVED]).copy()
    if len(resolved) == 0:
        return pd.DataFrame(columns=[COL_SEVERITY, "mttr_days"])
    resolved["_d"] = (resolved[COL_RESOLVED] - resolved[COL_CREATED]).dt.total_seconds() / 86400.0
    out = resolved.groupby(COL_SEVERITY)["_d"].mean().reset_index(name="mttr_days")
    return out.sort_values("mttr_days", ascending=False).reset_index(drop=True)


def defect_trend(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """
    기간별 생성/해결 결함 추세.
    columns=[period, created, resolved]. freq: 'D'/'W'/'M'.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["period", "created", "resolved"])
    created = df.set_index(COL_CREATED).resample(freq).size().rename("created")
    res = df.dropna(subset=[COL_RESOLVED])
    resolved = res.set_index(COL_RESOLVED).resample(freq).size().rename("resolved")
    out = pd.concat([created, resolved], axis=1).fillna(0).astype(int)
    return out.rename_axis("period").reset_index()


def aging(df: pd.DataFrame, today: pd.Timestamp | None = None, stale_days: int = 30) -> pd.DataFrame:
    """
    미해결(open) 결함의 경과일(age)과 방치 플래그.
    columns = 원본 + [age_days, is_stale]. age 내림차순.
    """
    today = today or pd.Timestamp.now().normalize()
    open_df = df[df[COL_STATUS].isin(OPEN_STATUSES)].copy()
    if len(open_df) == 0:
        return open_df.assign(age_days=pd.Series(dtype=int), is_stale=pd.Series(dtype=bool))
    open_df["age_days"] = (today - open_df[COL_CREATED]).dt.days
    open_df["is_stale"] = open_df["age_days"] >= stale_days
    return open_df.sort_values("age_days", ascending=False).reset_index(drop=True)


def anomaly_modules(df: pd.DataFrame, z_threshold: float = 1.5) -> pd.DataFrame:
    """
    결함이 비정상적으로 많은 모듈 자동 플래그.
    모듈별 건수의 z-score가 임계값 이상이면 is_anomaly=True.
    columns=[module, count, z_score, is_anomaly].
    """
    counts = defect_density_by_module(df)
    if len(counts) <= 1:
        counts["z_score"] = 0.0
        counts["is_anomaly"] = False
        return counts
    mean = counts["count"].mean()
    std = counts["count"].std(ddof=0)
    counts["z_score"] = 0.0 if std == 0 else (counts["count"] - mean) / std
    counts["is_anomaly"] = counts["z_score"] >= z_threshold
    return counts


def kpi_summary(df: pd.DataFrame) -> dict:
    """대시보드 상단 KPI 카드용 요약 dict."""
    open_count = int(df[COL_STATUS].isin(OPEN_STATUSES).sum())
    return {
        "total": int(len(df)),
        "open": open_count,
        "reopen_rate": reopen_rate(df),
        "escape_rate": escape_rate(df),
        "mttr_days": mttr_days(df),
    }

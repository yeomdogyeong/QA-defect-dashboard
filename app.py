"""
QA Defect Dashboard — Streamlit 앱.

실행:  streamlit run app.py

기능:
- 데이터 소스: CSV 업로드 또는 내장 샘플 생성
- 사이드바 필터: 기간 / 모듈 / 심각도 / 담당자
- 상단 KPI 카드: 총 결함 / 미해결 / 재오픈율 / 유출률 / MTTR
- 차트: 심각도·상태·RCA 분포, 모듈 밀도, 생성/해결 추세, aging, 이상 모듈
- 다운로드: Excel · PDF 리포트
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src import metrics as M
from src import report as R
from src.data_generator import (
    COL_ASSIGNEE, COL_CREATED, COL_MODULE, COL_RESOLVED, COL_SEVERITY,
    SEVERITIES, generate_defects,
)

st.set_page_config(page_title="QA Defect Dashboard", page_icon="🐞", layout="wide")

_SEV_ORDER = {s: i for i, s in enumerate(SEVERITIES)}
_DATE_COLS = [COL_CREATED, COL_RESOLVED]


@st.cache_data
def _sample() -> pd.DataFrame:
    return generate_defects()


def _load_uploaded(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    for c in _DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


# ---- 데이터 소스 -----------------------------------------------------------
st.sidebar.title("🐞 QA Defect Dashboard")
src_choice = st.sidebar.radio("데이터 소스", ["샘플 데이터", "CSV 업로드"])

if src_choice == "CSV 업로드":
    up = st.sidebar.file_uploader("결함 CSV 업로드", type=["csv"])
    if up is None:
        st.info("CSV를 업로드하거나 사이드바에서 '샘플 데이터'를 선택하세요.")
        st.stop()
    df = _load_uploaded(up)
else:
    df = _sample()

# ---- 필터 ------------------------------------------------------------------
st.sidebar.subheader("필터")
min_d, max_d = df[COL_CREATED].min(), df[COL_CREATED].max()
date_range = st.sidebar.date_input("생성 기간", (min_d, max_d), min_value=min_d, max_value=max_d)
sel_modules = st.sidebar.multiselect("모듈", sorted(df[COL_MODULE].unique()))
sel_sev = st.sidebar.multiselect("심각도", SEVERITIES)
sel_assignee = st.sidebar.multiselect("담당자", sorted(df[COL_ASSIGNEE].dropna().unique()))

mask = pd.Series(True, index=df.index)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    lo, hi = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask &= df[COL_CREATED].between(lo, hi)
if sel_modules:
    mask &= df[COL_MODULE].isin(sel_modules)
if sel_sev:
    mask &= df[COL_SEVERITY].isin(sel_sev)
if sel_assignee:
    mask &= df[COL_ASSIGNEE].isin(sel_assignee)
fdf = df[mask].copy()

st.title("QA Defect Dashboard")
st.caption(f"{len(fdf)} / {len(df)} 건 표시 중")

if len(fdf) == 0:
    st.warning("필터 조건에 맞는 결함이 없습니다.")
    st.stop()

# ---- KPI 카드 --------------------------------------------------------------
kpi = M.kpi_summary(fdf)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 결함", kpi["total"])
c2.metric("미해결 (Open)", kpi["open"])
c3.metric("재오픈율", f"{kpi['reopen_rate']:.1%}")
c4.metric("유출률 (Escape)", f"{kpi['escape_rate']:.1%}")
c5.metric("평균 해결 (일)", f"{kpi['mttr_days']:.1f}")

st.divider()

# ---- 분포 차트 -------------------------------------------------------------
a, b, c = st.columns(3)
with a:
    sev = M.severity_distribution(fdf)
    sev["_o"] = sev[COL_SEVERITY].map(_SEV_ORDER)
    sev = sev.sort_values("_o")
    st.plotly_chart(
        px.bar(sev, x=COL_SEVERITY, y="count", title="심각도 분포",
               color=COL_SEVERITY, text="count"),
        use_container_width=True)
with b:
    stt = M.status_distribution(fdf)
    st.plotly_chart(
        px.pie(stt, names="status", values="count", title="상태 분포", hole=0.4),
        use_container_width=True)
with c:
    rca = M.root_cause_distribution(fdf)
    st.plotly_chart(
        px.pie(rca, names="root_cause", values="count", title="근본원인(RCA)", hole=0.4),
        use_container_width=True)

# ---- 모듈 밀도 + 이상탐지 --------------------------------------------------
st.subheader("모듈별 결함 밀도 (이상 모듈 자동 플래그)")
anom = M.anomaly_modules(fdf)
fig = px.bar(anom, x=COL_MODULE, y="count",
             color="is_anomaly",
             color_discrete_map={True: "#d62728", False: "#1f77b4"},
             text="count", title="모듈별 결함 수")
st.plotly_chart(fig, use_container_width=True)
flagged = anom[anom["is_anomaly"]][COL_MODULE].tolist()
if flagged:
    st.error(f"⚠️ 결함 급증 모듈: {', '.join(flagged)} — 우선 점검 권장")

# ---- 추세 + MTTR -----------------------------------------------------------
d1, d2 = st.columns(2)
with d1:
    freq = st.radio("추세 단위", ["W", "M"], horizontal=True,
                    format_func=lambda x: {"W": "주간", "M": "월간"}[x])
    trend = M.defect_trend(fdf, freq=freq)
    tl = trend.melt("period", ["created", "resolved"], "종류", "건수")
    st.plotly_chart(
        px.line(tl, x="period", y="건수", color="종류", markers=True,
                title="생성 vs 해결 추세"),
        use_container_width=True)
with d2:
    mts = M.mttr_by_severity(fdf)
    if len(mts):
        mts["_o"] = mts[COL_SEVERITY].map(_SEV_ORDER)
        mts = mts.sort_values("_o")
        st.plotly_chart(
            px.bar(mts, x=COL_SEVERITY, y="mttr_days",
                   title="심각도별 평균 해결일 (MTTR)", text_auto=".1f"),
            use_container_width=True)

# ---- Aging -----------------------------------------------------------------
st.subheader("미해결 결함 Aging (30일 이상 방치 강조)")
ag = M.aging(fdf)
if len(ag):
    show = ag[["id", COL_MODULE, COL_SEVERITY, "status", "age_days", "is_stale"]]
    st.dataframe(
        show.style.apply(
            lambda r: ["background-color:#ffe0e0" if r["is_stale"] else "" for _ in r],
            axis=1),
        use_container_width=True, height=300)
    st.caption(f"방치(30일+) 결함: {int(ag['is_stale'].sum())}건")
else:
    st.success("미해결 결함이 없습니다.")

# ---- 리포트 다운로드 -------------------------------------------------------
st.divider()
st.subheader("리포트 내보내기")
e1, e2 = st.columns(2)
with e1:
    st.download_button("📊 Excel 리포트", R.to_excel(fdf),
                       file_name="qa_defect_report.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with e2:
    st.download_button("📄 PDF 리포트", R.to_pdf(fdf),
                       file_name="qa_defect_report.pdf", mime="application/pdf")

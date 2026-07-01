"""
리포트용 차트 생성기 (matplotlib).

웹 대시보드(plotly)와 비슷한 색감·레이아웃으로 그래프를 그려
PNG bytes로 반환한다. report.py가 이를 PDF/Excel에 이미지로 심는다.

- 헤드리스 환경을 위해 Agg 백엔드 사용
- 라벨은 데이터 값이 영문이라 영문 유지 (폰트 의존성 없이 어디서나 깨끗하게 렌더)
"""

from __future__ import annotations

import io
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from src import metrics as M  # noqa: E402
from src import labels as L  # noqa: E402
from src.data_generator import (  # noqa: E402
    COL_MODULE, COL_SEVERITY, SEVERITIES,
)

# --------------------------------------------------------------------------- #
#  한글 폰트 (맑은 고딕 우선, 볼드 포함). 없으면 다른 한글 폰트로 폴백.
# --------------------------------------------------------------------------- #
_FONT_PAIRS = [
    (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf"),   # Windows
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", None),                  # macOS
    ("/Library/Fonts/AppleGothic.ttf", None),
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
     "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),               # Linux
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", None),
]
_FONT_NAMES = ["Malgun Gothic", "Apple SD Gothic Neo", "AppleGothic",
               "NanumGothic", "Noto Sans CJK KR"]


def _resolve_korean_font():
    for reg, bold in _FONT_PAIRS:
        if os.path.exists(reg):
            try:
                font_manager.fontManager.addfont(reg)
                name = font_manager.FontProperties(fname=reg).get_name()
                bpath = bold if (bold and os.path.exists(bold)) else None
                if bpath:
                    try:
                        font_manager.fontManager.addfont(bpath)
                    except Exception:
                        bpath = None
                return reg, bpath, name
            except Exception:
                continue
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in _FONT_NAMES:
        if name in available:
            return None, None, name
    return None, None, None


KOREAN_FONT_PATH, KOREAN_FONT_BOLD_PATH, KOREAN_FONT_NAME = _resolve_korean_font()
if KOREAN_FONT_NAME:
    plt.rcParams["font.family"] = KOREAN_FONT_NAME
plt.rcParams["axes.unicode_minus"] = False  # 한글 폰트에서 마이너스 깨짐 방지

# 볼드를 확실히 렌더하기 위한 명시적 FontProperties (볼드 파일 우선)
_BOLD_FP = (font_manager.FontProperties(fname=KOREAN_FONT_BOLD_PATH)
            if KOREAN_FONT_BOLD_PATH else font_manager.FontProperties(weight="bold"))

# 웹(plotly)과 맞춘 색 팔레트
BLUE = "#4C6EF5"
RED = "#F03E3E"
GREEN = "#0CA678"
PURPLE = "#9C36B5"
ORANGE = "#F76707"
CYAN = "#1098AD"
INK = "#1F2A44"
MUTED = "#8794AD"

PALETTE = [BLUE, ORANGE, GREEN, PURPLE, CYAN, RED, "#F59F00", "#66A6FF"]
SEV_COLORS = {
    "Blocker": "#C92A2A", "Critical": "#F03E3E", "Major": "#F76707",
    "Minor": "#0CA678", "Trivial": "#868E96",
}
KPI_COLORS = [BLUE, "#5C7CFA", ORANGE, RED, GREEN]

plt.rcParams.update({
    "font.size": 12,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "axes.edgecolor": "#CED4DA",
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.grid": True,
    "grid.color": "#E9ECEF",
    "grid.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def _png(fig, dpi: int = 150) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    plt.close(fig)
    return buf.getvalue()


def _clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# --------------------------------------------------------------------------- #
def kpi_cards_png(kpi: dict) -> bytes:
    """웹의 KPI 카드처럼 5개 카드를 한 줄로 렌더."""
    items = [
        ("총 결함", f"{kpi['total']:,}"),
        ("미해결", f"{kpi['open']:,}"),
        ("재오픈율", f"{kpi['reopen_rate']:.1%}"),
        ("유출률", f"{kpi['escape_rate']:.1%}"),
        ("평균 해결(일)", f"{kpi['mttr_days']:.1f}"),
    ]
    fig, ax = plt.subplots(figsize=(13, 2.0))
    ax.set_xlim(0, len(items))
    ax.set_ylim(0, 1)
    ax.axis("off")
    for i, ((label, value), color) in enumerate(zip(items, KPI_COLORS)):
        pad = 0.06
        box = FancyBboxPatch(
            (i + pad, 0.08), 1 - 2 * pad, 0.84,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=0, facecolor=color, alpha=0.12,
            edgecolor=color, mutation_aspect=0.5,
        )
        ax.add_patch(box)
        cx = i + 0.5
        ax.text(cx, 0.30, label, ha="center", va="center",
                fontsize=11, color=MUTED, fontproperties=_BOLD_FP)
        ax.text(cx, 0.62, value, ha="center", va="center",
                fontsize=30, color=color, fontproperties=_BOLD_FP)
        ax.plot([i + pad + 0.02, i + pad + 0.02], [0.14, 0.86],
                color=color, linewidth=3, solid_capstyle="round")
    return _png(fig)


def severity_png(df) -> bytes:
    sev = M.severity_distribution(df).set_index(COL_SEVERITY)["count"]
    order = [s for s in SEVERITIES if s in sev.index]
    vals = [sev[s] for s in order]
    colors = [SEV_COLORS[s] for s in order]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    bars = ax.bar(L.tr(order, L.SEVERITY_KO), vals, color=colors, width=0.62)
    ax.bar_label(bars, padding=3, fontweight="bold", color=INK)
    ax.set_title("심각도 분포", loc="left")
    ax.set_ylabel("건수")
    ax.margins(y=0.15)
    _clean(ax)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    return _png(fig)


def _donut(labels, values, title, tall=False) -> bytes:
    fig, ax = plt.subplots(figsize=(6.0, 7.0) if tall else (6.4, 4.4))
    colors = PALETTE[:len(labels)]
    wedges, _, autotexts = ax.pie(
        values, colors=colors, startangle=90,
        radius=0.83 if tall else 1.0,          # 세로형 원은 기존의 2/3 크기
        wedgeprops=dict(width=0.30 if tall else 0.42, edgecolor="white", linewidth=2),
        autopct=lambda p: f"{p:.0f}%" if p >= 6 else "",
        pctdistance=0.80,
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontweight("bold")
        t.set_fontsize(11 if tall else 12)
    ax.set_title(title, loc="left", pad=12 if tall else 6)
    if tall:
        # 세로형: 범례를 원 아래로 (범례 글자 크기는 그대로 유지)
        ax.legend(wedges, labels, loc="upper center", bbox_to_anchor=(0.5, 0.14),
                  ncol=3, frameon=False, fontsize=11, columnspacing=1.2)
    else:
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.98, 0.5),
                  frameon=False, fontsize=11)
    ax.set(aspect="equal")
    return _png(fig)


def status_png(df, tall=False) -> bytes:
    s = M.status_distribution(df)
    return _donut(L.tr(s["status"], L.STATUS_KO), s["count"].tolist(), "상태 분포", tall=tall)


def rca_png(df, tall=False) -> bytes:
    r = M.root_cause_distribution(df)
    return _donut(L.tr(r["root_cause"], L.ROOT_CAUSE_KO), r["count"].tolist(),
                  "근본원인 (RCA)", tall=tall)


def module_anomaly_png(df, tall=False) -> bytes:
    a = M.anomaly_modules(df)
    colors = [RED if flag else BLUE for flag in a["is_anomaly"]]
    fig, ax = plt.subplots(figsize=(6.0, 7.0) if tall else (6.4, 4.4))
    bars = ax.bar(L.tr(a[COL_MODULE], L.MODULE_KO), a["count"], color=colors, width=0.66)
    ax.bar_label(bars, padding=3, fontweight="bold", color=INK, fontsize=10)
    ax.set_title("모듈별 결함  (빨강 = 이상 급증)", loc="left")
    ax.set_ylabel("건수")
    ax.margins(y=0.16)
    _clean(ax)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", fontsize=10)
    return _png(fig)


def trend_png(df, freq: str = "W", tall=False) -> bytes:
    t = M.defect_trend(df, freq=freq)
    fig, ax = plt.subplots(figsize=(6.0, 7.0) if tall else (6.4, 4.4))
    ax.plot(t["period"], t["created"], marker="o", markersize=5,
            color=BLUE, linewidth=2.2, label="생성")
    ax.plot(t["period"], t["resolved"], marker="o", markersize=5,
            color=GREEN, linewidth=2.2, label="해결")
    ax.fill_between(t["period"], t["created"], color=BLUE, alpha=0.06)
    ax.set_title("생성 vs 해결 추세", loc="left")
    ax.set_ylabel("건수")
    ax.legend(frameon=False, loc="upper left")
    _clean(ax)
    fig.autofmt_xdate(rotation=25)
    return _png(fig)


def mttr_png(df) -> bytes:
    m = M.mttr_by_severity(df).set_index(COL_SEVERITY)["mttr_days"]
    order = [s for s in SEVERITIES if s in m.index]
    vals = [m[s] for s in order]
    colors = [SEV_COLORS[s] for s in order]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    bars = ax.bar(L.tr(order, L.SEVERITY_KO), vals, color=colors, width=0.62)
    ax.bar_label(bars, fmt="%.1f", padding=3, fontweight="bold", color=INK)
    ax.set_title("심각도별 평균 해결일 (MTTR)", loc="left")
    ax.set_ylabel("일")
    ax.margins(y=0.16)
    _clean(ax)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    return _png(fig)


def all_charts(df, freq: str = "W", tall: bool = False) -> dict[str, bytes]:
    """리포트에 쓸 모든 차트를 한 번에 생성. tall=True면 4개 리포트 차트를 세로형으로."""
    return {
        "kpi": kpi_cards_png(M.kpi_summary(df)),
        "severity": severity_png(df),
        "status": status_png(df, tall=tall),
        "rca": rca_png(df, tall=tall),
        "module": module_anomaly_png(df, tall=tall),
        "trend": trend_png(df, freq, tall=tall),
        "mttr": mttr_png(df),
    }

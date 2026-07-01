"""리포트/차트 생성 스모크 테스트 — 유효한 파일 바이트가 나오는지 검증."""

from src.data_generator import generate_defects
from src import charts as C
from src import report as R


def test_charts_return_png_bytes():
    df = generate_defects(n=80)
    imgs = C.all_charts(df)
    assert set(imgs) == {"kpi", "severity", "status", "rca", "module", "trend", "mttr"}
    for name, png in imgs.items():
        assert png[:8] == b"\x89PNG\r\n\x1a\n", f"{name} is not a PNG"


def test_to_excel_is_valid_xlsx():
    df = generate_defects(n=80)
    data = R.to_excel(df)
    # xlsx = zip 컨테이너 → 'PK' 매직으로 시작
    assert data[:2] == b"PK"
    assert len(data) > 10_000


def test_to_pdf_is_valid_pdf():
    df = generate_defects(n=80)
    data = R.to_pdf(df)
    assert data[:5] == b"%PDF-"
    assert len(data) > 10_000

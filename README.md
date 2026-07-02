# QA Defect Dashboard 🐞

버그트래커(Jira · Redmine · Mantis) 결함 데이터를 읽어 **QA 품질 지표를 시각화**하고
**Excel · PDF 리포트를 자동 생성**하는 Streamlit 대시보드입니다.

QA 이직 포트폴리오용으로 만들어졌으며, "결함을 세는" 도구가 아니라
**품질을 읽는 지표**(재오픈율 · 유출률 · MTTR · 결함 aging · 이상 모듈 탐지)에 초점을 둡니다.

---

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저가 자동으로 열립니다. 데이터가 없어도 **사이드바 → '샘플 데이터'** 로
바로 데모가 돌아갑니다. 실제 트래커 CSV가 있으면 'CSV 업로드'로 넣으세요.

### 테스트 실행
```bash
pytest -v
```

---

## 기능

| 구분 | 내용 |
|------|------|
| 데이터 소스 | CSV 업로드 + 내장 샘플 생성기(실 트래커 불필요) |
| 필터 | 기간 · 모듈 · 심각도 · 담당자 |
| KPI 카드 | 총 결함 / 미해결 / **재오픈율** / **유출률** / **MTTR** |
| 분포 | 심각도 · 상태 · 근본원인(RCA) |
| 심화 분석 | 모듈별 결함 밀도 + **이상 모듈 자동 플래그**, 생성/해결 추세, 심각도별 MTTR, **미해결 결함 aging(30일+ 강조)** |
| 리포트 | **한글(맑은 고딕)** Excel·PDF 다운로드 — KPI 카드 + 차트 4종(원형2·추세1·막대1). PDF는 1p 차트 / 2p 모듈표 |

---

## 구조

```
qa-defect-dashboard/
├── app.py                  # Streamlit 대시보드 (UI)
├── src/
│   ├── data_generator.py   # 샘플 결함 데이터 생성 (원본의 simulator 역할)
│   ├── metrics.py          # QA 지표 = 순수 함수 (테스트 가능)
│   ├── charts.py           # matplotlib 차트 생성 (리포트용)
│   └── report.py           # Excel · PDF 리포트 생성 (차트 임베드)
├── tests/
│   ├── test_metrics.py     # 지표 로직 단위 테스트 (pytest)
│   └── test_report.py      # 리포트 생성 스모크 테스트
├── sample_defects.csv      # 예시 데이터
└── requirements.txt



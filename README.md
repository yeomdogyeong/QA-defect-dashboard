# QA Defect Dashboard 🐞

버그트래커(Jira · Redmine · Mantis) 결함 데이터를 읽어 **QA 품질 지표를 시각화**하고
**Excel · PDF 리포트를 자동 생성**하는 Streamlit 대시보드입니다.

QA 이직 포트폴리오용으로 만들어졌으며, "결함을 세는" 도구가 아니라
**품질을 읽는 지표**(재오픈율 · 유출률 · MTTR · 결함 aging · 이상 모듈 탐지)에 초점을 둡니다.

---

## 스크린샷 넣을 자리
`docs/` 폴더를 만들어 실행 화면을 캡처해 넣으세요 (README·포트폴리오 PPT용).

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
```

**설계 포인트 — 지표 계산을 UI에서 분리한 순수 함수로 작성**하고 pytest로 검증합니다.
"자기가 만든 도구조차 테스트로 검증하는 QA"라는 메타 어필이자,
관심사 분리(UI ↔ 로직) 설계 역량을 함께 보여주는 부분입니다.

---

## 지표 정의 (면접 대비 요약)

- **재오픈율(Reopen rate)** = 재오픈 이력 있는 결함 ÷ 전체. 수정 품질/검증 정확도 신호.
- **유출률(Escape rate)** = Production 단계 발견 결함 ÷ 전체. 출시 전 테스트가 결함을 얼마나 걸러냈는지.
- **MTTR** = 평균 해결 소요일. 심각도별로도 분해.
- **Aging** = 미해결 결함 경과일. 30일 이상 방치 결함 강조.
- **이상 모듈** = 모듈별 결함 수의 z-score ≥ 1.5 → 우선 점검 대상 자동 플래그.

---

> **폰트 안내**: 리포트 한글은 Windows의 맑은 고딕을 자동 인식합니다. 없으면 나눔고딕·Noto 등으로 폴백하며, 한글 폰트가 전혀 없으면 영문 라벨로 자동 전환됩니다.

## 무료 배포 (이력서에 라이브 링크 넣기)

> 리눅스 서버에는 맑은 고딕이 없으므로, 리포트 한글이 깨지지 않도록 `packages.txt`(fonts-nanum)를 함께 커밋합니다. (이미 포함됨)


1. 이 폴더를 GitHub 저장소에 push
2. [share.streamlit.io](https://share.streamlit.io) 에서 저장소 연결 → `app.py` 지정
3. 배포된 URL을 이력서·포트폴리오에 첨부

---

## 실제 트래커 연동으로 확장하려면
`src/data_generator.py` 자리에 API 커넥터를 추가하세요.
- Jira: `jira` 파이썬 라이브러리 또는 REST `/rest/api/2/search`
- Redmine: `/issues.json`
- MantisBT: REST API `/api/rest/issues`

응답을 이 프로젝트의 컬럼 스키마로 매핑하면 대시보드·리포트·테스트가 그대로 재사용됩니다.

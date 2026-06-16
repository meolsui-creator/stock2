---
name: fdr-usage
description: FinanceDataReader 조회/지표 계산 및 Windows 콘솔 한글 인코딩 주의점
metadata:
  type: reference
---

FinanceDataReader 0.9.x, matplotlib 3.11 설치됨. API 키 불필요.

- `fdr.DataReader('005930', start, end)` 반환: DatetimeIndex, 컬럼 Open/High/Low/Close/Volume/Change. 일별·지연 데이터.
- MA60 안정 계산을 위해 6개월 요청 시에도 실제로는 14개월(약 420일)을 받아 rolling 후 마지막 구간만 표시하는 것이 안전합니다. 6개월(180일)만 받으면 MA60 표본이 빠듯합니다.
- 52주 고저는 약 1년치 종가의 max/min으로 계산.

**Windows 콘솔 인코딩 함정**: Bash 도구 stdout이 한글 trend 라벨("상승"/"정배열" 등)을 깨뜨려 출력합니다(값 자체는 정상). 검증·디버깅 시 라벨을 ASCII(UP/DOWN/FLAT, GOLDEN/DEAD)로 찍으면 확실합니다. PNG 한글 파일명은 정상 저장됨(Glob로 확인).

**차트 한글 폰트**: `plt.rcParams["font.family"]=["Malgun Gothic","DejaVu Sans"]`, `axes.unicode_minus=False`.

**스플릿/데이터 단절 점검**: 6개월 등락률이 비정상적으로 클 때 일간 pct_change>25% 점프 탐지 + 월말 종가 시계열로 연속성 확인. 삼성전자는 2025-04~2026-06 구간에서 점프 없이 연속 상승(분할 아님)으로 확인됨.

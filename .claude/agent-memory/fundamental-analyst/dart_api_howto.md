---
name: dart-api-howto
description: DART OpenAPI를 requests로 직접 호출하는 패턴 (OpenDartReader 미설치 환경)
metadata:
  type: reference
---

OpenDartReader는 이 환경에 미설치. `requests`로 DART OpenAPI 직접 호출.
DART_KEY는 `C:\Users\HWPS\desktop\stock2\.env`의 `DART_KEY=...` 한 줄. python은 `python` (python3 아님, Bash에선 PowerShell 경유 권장).

주요 엔드포인트:
- 공시목록: `https://opendart.fss.or.kr/api/list.json` — params: crtfc_key, corp_code, bgn_de, end_de, pblntf_ty=A(정기공시), page_count
- 전체 재무제표: `https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json` — params: crtfc_key, corp_code, bsns_year, reprt_code, fs_div(CFS=연결/OFS=별도)
- 주요계정(간단): `https://opendart.fss.or.kr/api/fnlttSinglAcnt.json` — 당기/전기 컬럼 비교 편리

reprt_code: 11011=사업보고서(연간), 11012=반기, 11013=1분기, 11014=3분기
응답: status "000"=정상, "013"=데이터없음. list[].sj_div: IS/CIS=손익, BS=재무상태.
account_nm 키로 매핑하되 회사·연도별로 라벨이 다를 수 있음(예: 매출액 vs 영업수익 vs 수익(매출액)).
콘솔(PowerShell/Bash) 출력에서 한글이 깨져 보여도 숫자는 정확함. `sys.stdout.reconfigure(encoding='utf-8')`로 일부 완화.

**How to apply:** 연결(CFS) 우선, 없으면 별도(OFS). 연간은 thstrm_amount, 분기 누적은 thstrm_add_amount 확인.
관련: [[samsung-financials]]

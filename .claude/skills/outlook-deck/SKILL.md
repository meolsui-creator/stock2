---
name: outlook-deck
description: 한화투자증권 리서치센터 '마켓 아웃룩' 디자인 시스템으로 프레젠테이션 덱(HTML, 16:9 1920×1080)을 생성합니다. 골드만삭스 풍의 차분한 네이비/페이퍼/골드 톤, 명조 헤드라인 + Pretendard 본문. 사용자가 "마켓 아웃룩", "시장 전망 덱/PPT", "한화투자증권 스타일 발표자료", "아웃룩 슬라이드"를 요청할 때 사용합니다. (Claude Design 핸드오프 `2026 마켓 아웃룩.dc.html`의 재구현)
---

# outlook-deck

골드만삭스 풍의 **한화투자증권 리서치센터 '마켓 아웃룩'** 프레젠테이션 디자인 시스템입니다.
Claude Design(claude.ai/design)에서 넘어온 `2026 마켓 아웃룩.dc.html` 핸드오프 번들을, 독점
슬라이드 엔진(`x-dc`/`deck-stage.js`) 의존 없이 **순수 HTML/CSS 스탠드얼론 덱**으로 재구현했습니다.

## 실행 방법

```bash
# 내장 2026 마켓 아웃룩 콘텐츠로 생성 (표지 시안 A/B/C 선택)
python .claude/skills/outlook-deck/build_deck.py --cover A

# 사용자 콘텐츠(JSON)로 생성
python .claude/skills/outlook-deck/build_deck.py --spec mydeck.json --out reports/decks/mydeck.html
```

- 출력: 기본 `reports/decks/2026_마켓_아웃룩.html` (없으면 `decks` 폴더 자동 생성)
- 의존성 없음(표준 라이브러리만). 폰트(Noto Serif KR·Pretendard)는 CDN에서 로드.
- 브라우저(Edge/Chrome)에서 열면 뷰포트 폭에 맞춰 스케일됩니다.
- **PDF 내보내기**: 브라우저 인쇄 → 용지 가로/배율 100% → 슬라이드당 1페이지(@page 1920×1080).

## 디자인 시스템 (코드에 고정)

- **무드**: 골드만삭스 풍 — 차분한 네이비/그레이, 절제된 세리프, 보수적 권위감
- **컬러 토큰**:
  - `--navy-900 #0b1a2b` / `--navy-700 #1b3a57` (다크 배경)
  - `--paper #f4f1ea` / `--paper-2 #ebe6dc` (라이트 배경)
  - `--ink #15212e` · `--slate #52647a` · `--slate-2 #8b97a6` (텍스트)
  - `--gold #a98545` / `--gold-2 #c2a05c` (악센트·eyebrow)
  - `--pos #2f6a4d`(개선) · `--neg #9d3b39`(악화) · `--line #d8d2c5`(헤어라인)
- **타입**: Noto Serif KR(헤드라인·숫자) + Pretendard(본문·라벨)
- **공통 크롬**: 골드 대시 + 라틴 eyebrow(letter-spacing 0.24em) + 한글 명조 타이틀(62px) +
  우상단 페이지번호 + 1px 헤어라인 디바이더 + 하단 풋터(좌: 리서치센터 / 우: 노트)
- 얇은 헤어라인, 넉넉한 여백, 세리프 숫자, 바이링구얼 라벨

## 슬라이드 타입 (콘텐츠 계약)

`--spec` JSON은 `{ "title": "...", "slides": [ {...}, ... ] }` 구조이며, 각 슬라이드는 `type`으로 렌더됩니다.
공통 필드: `latin`(라틴 eyebrow), `title`(한글 타이틀), `pageno`("01 / 10"), `foot`(풋터 우측), `dark`(true=네이비).

| type | 용도 | 핵심 필드 |
|---|---|---|
| `cover` | 표지 | `variant` A(다크)·B(스플릿)·C(라이트 워터마크), `title`, `subtitle`, `date`, `kicker`, `outlabel`(우상단 라틴 라벨, 기본 "MARKET OUTLOOK" → 종목 리포트는 "EQUITY RESEARCH" 등) |
| `contents` | 목차 | `items:[{no,ko,en}]` (2열 컬럼 배치) |
| `houseview` | 핵심 요약 | `lead`(HTML 허용), `cards:[{no,h,p}]` |
| `metrics3` | 지표 3열 | `metrics:[{label,value,note,color?}]` (value는 HTML 허용) |
| `table` | 좌 메시지 + 우 표 | `left:[{lead?,t}]`, `table:{cols,grid,align?,rows}} ` 셀은 문자열 또는 `{t,color,bold}` |
| `scenario` | 큰 숫자 + 시나리오표 | `big:{label,value,band,note}`, `table:{cols,grid,rows}` |
| `sectors` | 업종 3그룹 | `groups:[{ko,en,accent,titlecolor?,items[],note}]` |
| `bonds` | 좌 불릿 + 우 표 | `lead`, `bullets:[{strong,rest}]`, `table` |
| `panels3` | 3패널(환율·원자재 등) | `panels:[{label,value,tag,tagcolor?,band,note}]` |
| `allocation` | 비중 막대 + 틸트 | `model`, `bars:[{name,pct,color}]`, `tilts:[{sign,color,strong,rest}]`, `tilt_note` |
| `risks` | 리스크 2열 그리드(다크) | `risks:[{no,h,p}]` |
| `checklist` | 체크리스트 + 면책(다크) | `items:[{no,h,p}]`, `disclaimer` |

## 가드레일 (프로젝트 규칙 준수)

- **모든 수치는 출처·기준일과 함께** 콘텐츠에 담고, 예시·가정값이면 풋터에 "illustrative · 실제 수치로 교체"를 표기합니다(내장 콘텐츠가 그 예시).
- **매수·매도/목표가 단정 금지** — 전망·근거 제시까지만. 시나리오/밴드 형태로 제시합니다.
- 맺음말 슬라이드에 **면책 문구**를 포함합니다(`checklist.disclaimer`).
- 이 덱은 발표용 비주얼이며, 종목 리포트 PPTX는 별도 `report-pptx` 스킬을 사용합니다.

## 원본 핸드오프 메모

- 출처: claude.ai/design 핸드오프 번들 `2026 마켓 아웃룩.dc.html` (한화투자증권 프레젠테이션 프로젝트)
- 의도(chat 기준): 개인·리테일 고객용 시장 전망 리포트, 골드만삭스 톤, 표지 3종 시안 비교, 세리프+산세리프 혼합, 핵심 지표 위주 시각화. 수치는 전부 illustrative.
- 구성(13슬라이드): 표지 → 목차 → 01 핵심요약 → 02 매크로 → 03 금리 → 04 국내경제 → 05 주식 → 06 업종 → 07 채권 → 08 환율·원자재 → 09 자산배분 → 10 리스크 → 맺음말(체크리스트+면책)

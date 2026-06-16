# -*- coding: utf-8 -*-
"""
데이터 파이프라인: 종목명 → reports/{종목명}.md 생성

- 주가/추세/차트: FinanceDataReader (키 불필요)
- 재무: OpenDartReader + .env의 DART_KEY (키 있을 때만, 없으면 '확인 불가')
- 뉴스·심리/종합: 자동 파이프라인에서는 수집하지 않으므로 안내 문구로 채움

모든 함수는 데이터가 없어도 예외를 던지지 않고 '확인 불가'로 처리합니다(가드레일).
출처·기준일을 모든 수치에 부기하고, 매수/매도 단정 표현은 쓰지 않습니다.
"""
import os
import re
from datetime import date, timedelta

import matplotlib
matplotlib.use("Agg")  # 서버 환경(헤드리스)에서 렌더
import matplotlib.pyplot as plt


def _won(n):
    try:
        return f"{int(round(n)):,}원"
    except Exception:
        return "확인 불가"


def resolve_ticker(name):
    """종목명 → (정식명, 종목코드). 실패 시 (name, None)."""
    try:
        import FinanceDataReader as fdr
        listing = fdr.StockListing("KRX")
        # 컬럼명 호환 (Name/Code 또는 한글)
        name_col = "Name" if "Name" in listing.columns else listing.columns[1]
        code_col = "Code" if "Code" in listing.columns else listing.columns[0]
        exact = listing[listing[name_col] == name]
        if len(exact) == 0:
            exact = listing[listing[name_col].astype(str).str.contains(name, na=False)]
        if len(exact) == 0:
            return name, None
        row = exact.iloc[0]
        return str(row[name_col]), str(row[code_col])
    except Exception:
        return name, None


def fetch_price(code, root, name):
    """최근 1년 주가 → 요약 dict + 차트 PNG(상대경로). 실패 시 None."""
    try:
        import FinanceDataReader as fdr
    except Exception:
        return None
    if not code:
        return None
    start = (date.today() - timedelta(days=370)).isoformat()
    try:
        df = fdr.DataReader(code, start)
    except Exception:
        return None
    if df is None or len(df) == 0:
        return None

    df = df.dropna(subset=["Close"])
    close = df["Close"]
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()

    last = float(close.iloc[-1])
    high_52 = float(close.max())
    low_52 = float(close.min())
    chg_1m = None
    if len(close) > 21:
        prev = float(close.iloc[-22])
        if prev:
            chg_1m = (last / prev - 1) * 100
    avg_vol = float(df["Volume"].tail(20).mean()) if "Volume" in df.columns else None

    # --- 차트 저장 (라벨은 영어로: 한글 폰트 깨짐 방지) ---
    charts_dir = os.path.join(root, "reports", "charts")
    os.makedirs(charts_dir, exist_ok=True)
    rel_path = f"reports/charts/{name}_price.png"
    abs_path = os.path.join(root, rel_path)
    try:
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=130)
        ax.plot(close.index, close.values, color="#1F2A44", linewidth=1.6, label="Close")
        ax.plot(ma20.index, ma20.values, color="#F37321", linewidth=1.1, label="MA20")
        ax.plot(ma60.index, ma60.values, color="#9AA4B2", linewidth=1.1, label="MA60")
        ax.set_title(f"{code} - 1Y Price & Moving Averages", fontsize=12)
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(abs_path)
        plt.close(fig)
    except Exception:
        rel_path = None

    return {
        "last": last,
        "high_52": high_52,
        "low_52": low_52,
        "chg_1m": chg_1m,
        "avg_vol": avg_vol,
        "asof": str(df.index[-1].date()),
        "chart_rel": rel_path,
    }


def fetch_financials(name, code):
    """DART 재무 3개년 표(rows). 키 없거나 실패 시 None."""
    key = os.environ.get("DART_KEY", "").strip()
    if not key or not code:
        return None
    try:
        import OpenDartReader
        dart = OpenDartReader(key)
        rows = [["항목", "최근값(백만원)", "기준"]]
        fs = dart.finstate(code, date.today().year - 1)  # 직전 사업연도
        if fs is None or len(fs) == 0:
            return None
        wanted = {"매출액": "매출액", "영업이익": "영업이익", "당기순이익": "당기순이익"}
        for label in wanted:
            try:
                hit = fs[fs["account_nm"] == label]
                if len(hit):
                    val = str(hit.iloc[0].get("thstrm_amount", "")).strip()
                    rows.append([label, val, f"{date.today().year - 1} 사업보고서"])
            except Exception:
                continue
        return rows if len(rows) >= 2 else None
    except Exception:
        return None


def generate_md(name, root):
    """전체 파이프라인 실행 → reports/{name}.md 작성. (md_path, info) 반환."""
    today = date.today().isoformat()
    official, code = resolve_ticker(name)
    price = fetch_price(code, root, name)
    fins = fetch_financials(name, code)

    src_fdr = f"(출처: FinanceDataReader / 기준일 {price['asof'] if price else today})"
    lines = []
    lines.append(f"# {official}")
    lines.append(f"작성일: {today}")
    lines.append("")

    # 종목 개요
    lines.append("## 종목 개요")
    if code:
        lines.append(f"- {official}({code}) — 한국거래소(KRX) 상장 종목입니다. {src_fdr}")
    else:
        lines.append(f"- '{name}' 종목코드를 자동으로 확정하지 못했습니다. 정식 상장명으로 다시 입력해 주십시오. (기준일 {today})")
    if price:
        lines.append(f"- 최근 종가는 {_won(price['last'])}입니다. {src_fdr}")
    lines.append("")

    # 재무 요약
    lines.append("## 재무 요약")
    if fins:
        for r in fins:
            lines.append("| " + " | ".join(r) + " |")
            if r is fins[0]:
                lines.append("|" + "---|" * len(r))
        lines.append(f"(출처: DART 전자공시 / 기준일 {today}, 연결 우선)")
    else:
        lines.append("- DART_KEY 미설정 또는 조회 실패로 재무 수치는 **확인 불가**입니다. `.env`에 `DART_KEY`를 설정하면 자동 수집됩니다. (기준일 " + today + ")")
    lines.append("")

    # 가격/추세
    lines.append("## 가격/추세")
    if price:
        if price.get("chart_rel"):
            lines.append(f"![1년 주가 추세]({price['chart_rel']})")
        lines.append(f"- 최근 1년 종가 기준 고점 {_won(price['high_52'])}, 저점 {_won(price['low_52'])}입니다. {src_fdr}")
        if price.get("chg_1m") is not None:
            lines.append(f"- 최근 약 1개월 등락률은 {price['chg_1m']:+.1f}%입니다. {src_fdr}")
        if price.get("avg_vol"):
            lines.append(f"- 최근 20거래일 평균 거래량은 약 {int(price['avg_vol']):,}주입니다. {src_fdr}")
    else:
        lines.append(f"- 주가 데이터를 가져오지 못해 **확인 불가**입니다. 종목코드 확정 여부를 확인해 주십시오. (기준일 {today})")
    lines.append("")

    # 뉴스·심리
    lines.append("## 뉴스·심리")
    lines.append(f"- 본 자동 파이프라인은 뉴스·심리를 수집하지 않습니다. 뉴스·심리 분석은 Claude Code의 `news-sentiment-analyst`로 별도 수행해 주십시오. (기준일 {today})")
    lines.append("")

    # 리스크
    lines.append("## 리스크")
    if price and price.get("avg_vol") is not None and price["avg_vol"] < 100000:
        lines.append(f"- 최근 20거래일 평균 거래량이 약 {int(price['avg_vol']):,}주로 낮은 편이어서 유동성 측면을 함께 점검할 필요가 있습니다. {src_fdr}")
    else:
        lines.append(f"- 정량 리스크(유동성·변동성) 점검은 Claude Code의 `risk-manager-analyst`로 보강하는 것을 권장합니다. (기준일 {today})")
    lines.append("")

    # 한 줄 종합
    lines.append("## 한 줄 종합")
    if price:
        lines.append(f"{official}의 최근 1년 가격은 고점 {_won(price['high_52'])}·저점 {_won(price['low_52'])} 구간에서 형성되었으며, 본 자료는 출처 있는 수치만으로 구성한 학습용 분석입니다.")
    else:
        lines.append("데이터 수집이 제한되어 출처 있는 수치만으로 구성한 학습용 분석입니다.")
    lines.append("")

    reports_dir = os.path.join(root, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    md_path = os.path.join(reports_dir, f"{name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    info = {
        "official": official,
        "code": code,
        "has_price": price is not None,
        "has_fins": fins is not None,
        "chart_rel": price.get("chart_rel") if price else None,
    }
    return md_path, info

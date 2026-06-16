# -*- coding: utf-8 -*-
"""
outlook-deck 빌더 — 한화투자증권 리서치센터 '마켓 아웃룩' 디자인 시스템
(Claude Design 핸드오프 `2026 마켓 아웃룩.dc.html`의 충실한 재구현)

특징:
  - 1920×1080(16:9) 슬라이드, 풀-스탠드얼론 HTML (proprietary x-dc/deck-stage.js 의존 제거)
  - 골드만 풍: 네이비/페이퍼/골드, Noto Serif KR(헤드라인·숫자) + Pretendard(본문)
  - 얇은 헤어라인, 넉넉한 여백, 세리프 숫자, 바이링구얼 eyebrow(라틴 gold + 한글 세리프)
  - 화면에서는 뷰포트 폭에 맞춰 스케일, 인쇄 시 슬라이드당 1페이지(PDF 내보내기)

사용법:
  python build_deck.py                      # 내장 2026 마켓 아웃룩 콘텐츠로 생성
  python build_deck.py --spec content.json  # 사용자 콘텐츠로 생성
  python build_deck.py --out reports/decks/foo.html --cover B

콘텐츠 계약(JSON)은 SKILL.md 참고. 슬라이드는 type 별로 렌더됩니다:
  cover · contents · houseview · metrics3 · table · scenario · sectors ·
  bonds · panels3 · allocation · risks · checklist
"""
import os
import sys
import json
import html
import argparse

# ── 디자인 토큰 (원본 :root 그대로) ──────────────────────────────────────────
CSS = """
:root{
  --navy-900:#0b1a2b; --navy-800:#102538; --navy-700:#1b3a57;
  --ink:#15212e; --slate:#52647a; --slate-2:#8b97a6;
  --paper:#f4f1ea; --paper-2:#ebe6dc; --line:#d8d2c5; --line-d:rgba(255,255,255,0.14);
  --gold:#a98545; --gold-2:#c2a05c; --pos:#2f6a4d; --neg:#9d3b39;
  --serif:"Noto Serif KR",Georgia,"Times New Roman",serif;
  --sans:"Pretendard","Pretendard Variable",system-ui,-apple-system,sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#0a121c;font-family:var(--sans);}
.slidewrap{display:flex;justify-content:center;overflow:hidden;}
.slide{width:1920px;height:1080px;flex:none;transform-origin:top center;overflow:hidden;position:relative;}
.slide.light{background:var(--paper);color:var(--ink);}
.slide.dark{background:var(--navy-900);color:#eef1f4;}
/* 공통 크롬 */
.hd{display:flex;justify-content:space-between;align-items:flex-end;}
.eyebrow{display:flex;align-items:center;gap:14px;margin-bottom:18px;}
.eyebrow .dash{width:34px;height:2px;background:var(--gold);display:block;}
.eyebrow .lab{font-size:24px;letter-spacing:0.24em;font-weight:600;}
.t-light .lab{color:var(--gold);} .t-dark .lab{color:var(--gold-2);}
.title{font-family:var(--serif);font-size:62px;font-weight:600;letter-spacing:-0.01em;}
.pageno{font-family:var(--serif);font-size:30px;color:var(--slate-2);}
.rule{height:1px;margin:30px 0 0;}
.rule.light{background:var(--line);} .rule.dark{background:var(--line-d);}
.body{flex:1;}
.foot{display:flex;justify-content:space-between;align-items:center;font-size:24px;color:var(--slate-2);}
.sec{display:flex;flex-direction:column;padding:84px 110px 72px;height:100%;}
@media print{
  body{background:#fff;}
  .slidewrap{height:auto!important;overflow:visible;}
  .slide{transform:none!important;break-after:page;}
  @page{size:1920px 1080px;margin:0;}
}
"""

FIT_JS = """
<script>
function fit(){var s=Math.min(1,(window.innerWidth)/1920);
document.querySelectorAll('.slidewrap').forEach(function(w){
  var sl=w.querySelector('.slide');sl.style.transform='scale('+s+')';
  w.style.height=(1080*s)+'px';});}
window.addEventListener('resize',fit);window.addEventListener('load',fit);fit();
</script>
"""

FOOT_BRAND = "한화투자증권 리서치센터"


def esc(s):
    return html.escape(str(s), quote=False)


def _wrap(inner):
    return '<div class="slidewrap"><section class="slide %s</section></div>' % inner


def header(latin, title, pageno, dark=False):
    tone = "t-dark" if dark else "t-light"
    rule = "dark" if dark else "light"
    return (
        '<div class="hd %s"><div>'
        '<div class="eyebrow"><span class="dash"></span><span class="lab">%s</span></div>'
        '<h2 class="title">%s</h2></div>'
        '<span class="pageno">%s</span></div>'
        '<div class="rule %s"></div>'
        % (tone, esc(latin), esc(title), esc(pageno), rule)
    )


def footer(right, dark=False):
    return '<div class="foot"><span>%s</span><span style="letter-spacing:0.16em;">%s</span></div>' % (
        FOOT_BRAND, esc(right))


def std_slide(s):
    """표준 크롬(헤더+룰+본문+풋터)을 가진 라이트/다크 슬라이드."""
    dark = s.get("dark", False)
    tone = "dark" if dark else "light"
    inner = '%s sec"%s%s%s' % (
        tone,
        ">" + header(s["latin"], s["title"], s["pageno"], dark),
        s["_body"],
        footer(s.get("foot", "2026 MARKET OUTLOOK"), dark),
    )
    return _wrap(inner)


# ── 슬라이드 타입별 본문 렌더러 ───────────────────────────────────────────────
def r_cover(s):
    variant = s.get("variant", "A")
    brand = '한화투자증권 <span style="color:var(--slate-2);font-weight:500;">리서치센터</span>'
    title = s.get("title", "2026<br>마켓 아웃룩")
    sub = s.get("subtitle", "거시 환경 점검과 자산배분 전략")
    foot_l = s.get("foot_left", "개인투자자를 위한 시장 전망")
    date = s.get("date", "2026. 01")
    kicker = s.get("kicker", "GLOBAL STRATEGY · 2026")
    outlabel = s.get("outlabel", "MARKET OUTLOOK")  # 표지 상단 라틴 라벨

    def fin(inner):
        return _wrap(inner.replace("MARKET OUTLOOK", outlabel))

    if variant == "B":  # 스플릿
        inner = ('light" style="display:flex;">'
            '<div style="width:60%%;background:var(--navy-900);color:#eef1f4;display:flex;flex-direction:column;justify-content:space-between;padding:92px 84px;position:relative;overflow:hidden;">'
            '<div style="display:flex;align-items:center;gap:16px;"><span style="width:28px;height:28px;border:2px solid var(--gold);transform:rotate(45deg);"></span><span style="font-size:26px;font-weight:600;">%s</span></div>'
            '<div><div class="eyebrow"><span class="dash"></span><span class="lab" style="color:var(--gold-2);">GLOBAL STRATEGY</span></div>'
            '<h1 style="font-family:var(--serif);font-size:104px;line-height:1.04;font-weight:600;letter-spacing:-0.01em;">%s</h1></div>'
            '<span style="font-size:25px;color:#aeb8c4;">%s · %s</span></div>'
            '<div style="width:40%%;background:var(--paper);color:var(--ink);display:flex;flex-direction:column;justify-content:space-between;padding:92px 70px;overflow:hidden;">'
            '<span style="font-size:24px;letter-spacing:0.28em;color:var(--gold);font-weight:600;align-self:flex-end;">MARKET OUTLOOK</span>'
            '<div style="font-family:var(--serif);font-size:300px;line-height:0.82;font-weight:600;color:var(--paper-2);letter-spacing:-0.03em;">26</div>'
            '<div style="border-top:1px solid var(--line);padding-top:26px;"><p style="font-family:var(--serif);font-size:34px;line-height:1.4;color:var(--slate);">%s</p></div></div>'
            % (brand, title.replace("<br>", "<br>"), foot_l, date, sub.replace(" ", "<br>", 1)))
        return fin(inner)
    if variant == "C":  # 라이트 워터마크
        inner = ('light sec" style="position:relative;">'
            '<div style="position:absolute;right:30px;top:50%%;transform:translateY(-50%%);font-family:var(--serif);font-size:440px;line-height:0.8;font-weight:600;color:var(--paper-2);letter-spacing:-0.04em;pointer-events:none;">26</div>'
            '<div class="hd t-light" style="align-items:center;position:relative;"><div style="display:flex;align-items:center;gap:18px;"><span style="width:30px;height:30px;border:2px solid var(--gold);transform:rotate(45deg);"></span><span style="font-size:27px;font-weight:600;">%s</span></div><span style="font-size:24px;letter-spacing:0.28em;color:var(--gold);font-weight:600;">MARKET OUTLOOK</span></div>'
            '<div style="position:relative;flex:1;display:flex;flex-direction:column;justify-content:center;"><div class="eyebrow"><span class="dash"></span><span class="lab">%s</span></div>'
            '<h1 style="font-family:var(--serif);font-size:120px;line-height:1.02;font-weight:600;letter-spacing:-0.01em;color:var(--navy-900);">%s</h1>'
            '<p style="font-family:var(--serif);font-size:42px;color:var(--slate);margin-top:32px;">%s</p></div>'
            '<div class="foot" style="border-top:1px solid var(--line);padding-top:30px;color:var(--slate);position:relative;"><span>%s</span><span style="letter-spacing:0.06em;">%s</span></div>'
            % (brand, kicker, title.replace("<br>", " "), sub, foot_l, date))
        return fin(inner)
    # variant A — 다크 풀블리드
    inner = ('dark sec" style="justify-content:space-between;overflow:hidden;">'
        '<div style="position:absolute;inset:0;background-image:repeating-linear-gradient(90deg,rgba(255,255,255,0.035) 0 1px,transparent 1px 268px);"></div>'
        '<div style="position:absolute;top:-160px;right:-160px;width:520px;height:520px;border:1px solid rgba(169,133,69,0.28);transform:rotate(45deg);"></div>'
        '<div style="display:flex;justify-content:space-between;align-items:center;position:relative;"><div style="display:flex;align-items:center;gap:18px;"><span style="width:30px;height:30px;border:2px solid var(--gold);transform:rotate(45deg);"></span><span style="font-size:27px;font-weight:600;">%s</span></div><span style="font-size:24px;letter-spacing:0.28em;color:var(--gold-2);font-weight:600;">MARKET OUTLOOK</span></div>'
        '<div style="position:relative;"><div class="eyebrow"><span class="dash" style="width:44px;"></span><span class="lab" style="color:var(--gold-2);">%s</span></div>'
        '<h1 style="font-family:var(--serif);font-size:122px;line-height:1.02;font-weight:600;letter-spacing:-0.01em;">%s</h1>'
        '<p style="font-family:var(--serif);font-size:42px;color:#c6cdd6;margin-top:34px;">%s</p></div>'
        '<div class="foot" style="border-top:1px solid var(--line-d);padding-top:30px;color:#aeb8c4;position:relative;"><span>%s</span><span style="letter-spacing:0.06em;">%s</span></div>'
        % (brand, kicker, title, sub, foot_l, date))
    return fin(inner)


def r_contents(s):
    cells = []
    for it in s["items"]:
        cells.append(
            '<div style="display:flex;align-items:baseline;gap:26px;padding:23px 0;border-bottom:1px solid var(--line-d);">'
            '<span style="font-family:var(--serif);font-size:28px;color:var(--gold-2);width:46px;">%s</span>'
            '<span style="font-size:32px;font-weight:500;">%s</span>'
            '<span style="font-size:24px;color:var(--slate-2);margin-left:auto;letter-spacing:0.14em;">%s</span></div>'
            % (esc(it["no"]), esc(it["ko"]), esc(it["en"])))
    body = ('<div class="body" style="display:grid;grid-template-columns:1fr 1fr;grid-auto-flow:column;'
            'grid-template-rows:repeat(%d,auto);column-gap:120px;align-content:center;">%s</div>'
            % ((len(cells) + 1) // 2, "".join(cells)))
    s["_body"] = body
    return std_slide(s)


def r_houseview(s):
    cards = []
    for c in s["cards"]:
        cards.append(
            '<div style="display:flex;flex-direction:column;gap:14px;border-top:2px solid var(--ink);padding-top:22px;">'
            '<span style="font-family:var(--serif);font-size:28px;color:var(--gold);">%s</span>'
            '<h3 style="font-size:31px;font-weight:700;color:var(--ink);">%s</h3>'
            '<p style="font-size:26px;line-height:1.5;color:var(--slate);">%s</p></div>'
            % (esc(c["no"]), esc(c["h"]), esc(c["p"])))
    body = ('<div class="body" style="display:flex;flex-direction:column;justify-content:center;gap:56px;">'
            '<p style="font-family:var(--serif);font-size:46px;line-height:1.4;font-weight:500;max-width:1560px;">%s</p>'
            '<div style="display:grid;grid-template-columns:repeat(%d,1fr);gap:46px;">%s</div></div>'
            % (s["lead"], len(cards), "".join(cards)))
    s["_body"] = body
    return std_slide(s)


def r_metrics3(s):
    cols = []
    for i, m in enumerate(s["metrics"]):
        bl = "border-left:1px solid var(--line);" if i else ""
        pad = ["30px 56px 30px 0", "30px 56px", "30px 0 30px 56px"][min(i, 2)]
        val_color = m.get("color", "var(--ink)")
        cols.append(
            '<div style="padding:%s;display:flex;flex-direction:column;gap:18px;%s">'
            '<span style="font-size:26px;color:var(--slate);font-weight:500;">%s</span>'
            '<span style="font-family:var(--serif);font-size:104px;line-height:1;font-weight:600;color:%s;">%s</span>'
            '<p style="font-size:26px;line-height:1.5;color:var(--slate);">%s</p></div>'
            % (pad, bl, esc(m["label"]), val_color, m["value"], esc(m["note"])))
    s["_body"] = ('<div class="body" style="display:grid;grid-template-columns:repeat(3,1fr);align-items:center;">%s</div>'
                  % "".join(cols))
    return std_slide(s)


def r_table(s):
    """좌측 메시지 + 우측 표. cols=헤더, rows=[[셀,..]]; 마지막 열은 pos 강조 옵션."""
    cols = s["table"]["cols"]
    aligns = s["table"].get("align", ["left"] + ["right"] * (len(cols) - 1))
    head = ""
    for c, a in zip(cols, aligns):
        ta = "text-align:right;" if a == "right" else ""
        head += ('<div style="font-size:25px;color:var(--slate);font-weight:600;padding:0 0 18px;'
                 'border-bottom:2px solid var(--ink);%s">%s</div>' % (ta, esc(c)))
    rowcells = ""
    for row in s["table"]["rows"]:
        for j, cell in enumerate(row):
            a = aligns[j]
            ta = "text-align:right;" if a == "right" else ""
            if j == 0:
                rowcells += ('<div style="font-size:31px;font-weight:600;padding:30px 0;border-bottom:1px solid var(--line);">%s</div>'
                             % esc(cell))
            else:
                txt = cell["t"] if isinstance(cell, dict) else cell
                col = cell.get("color", "var(--slate)") if isinstance(cell, dict) else "var(--slate)"
                fw = "font-weight:600;" if (isinstance(cell, dict) and cell.get("bold")) else ""
                rowcells += ('<div style="font-family:var(--serif);font-size:38px;padding:30px 0;border-bottom:1px solid var(--line);%s color:%s;%s">%s</div>'
                             % (ta, col, fw, esc(txt)))
    tmpl = s["table"].get("grid", "1.4fr 1fr 1fr")
    left = '<div style="display:flex;flex-direction:column;gap:30px;">'
    for p in s["left"]:
        if p.get("lead"):
            left += '<p style="font-family:var(--serif);font-size:44px;line-height:1.34;font-weight:500;color:var(--ink);">%s</p>' % esc(p["t"])
        else:
            left += '<p style="font-size:28px;line-height:1.6;color:var(--slate);">%s</p>' % esc(p["t"])
    left += "</div>"
    s["_body"] = ('<div class="body" style="display:grid;grid-template-columns:%s;gap:90px;align-items:center;">'
                  '%s<div style="display:grid;grid-template-columns:%s;">%s%s</div></div>'
                  % (s.get("split", "0.92fr 1.08fr"), left, tmpl, head, rowcells))
    return std_slide(s)


def r_scenario(s):
    big = s["big"]
    left = ('<div style="display:flex;flex-direction:column;gap:12px;">'
            '<span style="font-size:27px;color:var(--slate);font-weight:500;">%s</span>'
            '<span style="font-family:var(--serif);font-size:128px;line-height:1;font-weight:600;color:var(--ink);">%s</span>'
            '<span style="font-size:30px;color:var(--pos);font-weight:600;">%s</span>'
            '<p style="font-size:27px;line-height:1.6;color:var(--slate);margin-top:14px;">%s</p></div>'
            % (esc(big["label"]), esc(big["value"]), esc(big["band"]), esc(big["note"])))
    return r_table_like_scenario(s, left)


def r_table_like_scenario(s, left):
    cols = s["table"]["cols"]
    head = ""
    for i, c in enumerate(cols):
        ta = "" if i == 0 else "text-align:right;"
        head += '<div style="font-size:25px;color:var(--slate);font-weight:600;padding:0 0 18px;border-bottom:2px solid var(--ink);%s">%s</div>' % (ta, esc(c))
    body = ""
    for row in s["table"]["rows"]:
        name = row[0]
        ncolor = name.get("color", "var(--ink)") if isinstance(name, dict) else "var(--ink)"
        nfw = "700" if (isinstance(name, dict) and name.get("bold")) else "600"
        ntxt = name["t"] if isinstance(name, dict) else name
        body += '<div style="font-size:30px;font-weight:%s;padding:26px 0;border-bottom:1px solid var(--line);color:%s;">%s</div>' % (nfw, ncolor, esc(ntxt))
        for cell in row[1:]:
            txt = cell["t"] if isinstance(cell, dict) else cell
            col = cell.get("color", "var(--slate)") if isinstance(cell, dict) else "var(--slate)"
            fw = "font-weight:%s;" % cell["bold"] if (isinstance(cell, dict) and cell.get("bold")) else ""
            sz = cell.get("size", "32px") if isinstance(cell, dict) else "32px"
            body += '<div style="font-family:var(--serif);font-size:%s;padding:26px 0;border-bottom:1px solid var(--line);text-align:right;color:%s;%s">%s</div>' % (sz, col, fw, esc(txt))
    s["_body"] = ('<div class="body" style="display:grid;grid-template-columns:%s;gap:90px;align-items:center;">'
                  '%s<div style="display:grid;grid-template-columns:%s;">%s%s</div></div>'
                  % (s.get("split", "0.82fr 1.18fr"), left, s["table"].get("grid", "1.3fr 1fr 1fr 1fr"), head, body))
    return std_slide(s)


def r_sectors(s):
    cols = []
    for g in s["groups"]:
        items = "".join('<div style="font-size:31px;font-weight:500;padding:24px 0;border-bottom:1px solid var(--line);">%s</div>' % esc(x) for x in g["items"])
        cols.append(
            '<div style="display:flex;flex-direction:column;">'
            '<div style="display:flex;align-items:center;gap:14px;border-bottom:3px solid %s;padding-bottom:18px;margin-bottom:8px;">'
            '<span style="font-size:30px;font-weight:700;color:%s;">%s</span>'
            '<span style="font-size:24px;color:var(--slate-2);margin-left:auto;letter-spacing:0.12em;">%s</span></div>'
            '%s<p style="font-size:25px;line-height:1.5;color:var(--slate);padding-top:20px;">%s</p></div>'
            % (g["accent"], g.get("titlecolor", g["accent"]), esc(g["ko"]), esc(g["en"]), items, esc(g["note"])))
    s["_body"] = '<div class="body" style="display:grid;grid-template-columns:repeat(3,1fr);gap:54px;align-content:center;">%s</div>' % "".join(cols)
    return std_slide(s)


def r_bonds(s):
    bullets = ""
    for b in s["bullets"]:
        bullets += ('<div style="display:flex;gap:18px;align-items:flex-start;">'
                    '<span style="width:9px;height:9px;background:var(--gold);margin-top:13px;flex-shrink:0;transform:rotate(45deg);"></span>'
                    '<p style="font-size:28px;line-height:1.55;color:var(--slate);"><span style="color:var(--ink);font-weight:600;">%s</span> %s</p></div>'
                    % (esc(b["strong"]), esc(b["rest"])))
    left = ('<div style="display:flex;flex-direction:column;gap:30px;">'
            '<p style="font-family:var(--serif);font-size:44px;line-height:1.34;font-weight:500;color:var(--ink);">%s</p>'
            '<div style="display:flex;flex-direction:column;gap:22px;">%s</div></div>'
            % (esc(s["lead"]), bullets))
    cols = s["table"]["cols"]
    head = ""
    for i, c in enumerate(cols):
        ta = "" if i == 0 else "text-align:right;"
        head += '<div style="font-size:25px;color:var(--slate);font-weight:600;padding:0 0 18px;border-bottom:2px solid var(--ink);%s">%s</div>' % (ta, esc(c))
    rows = ""
    for row in s["table"]["rows"]:
        rows += '<div style="font-size:31px;font-weight:600;padding:30px 0;border-bottom:1px solid var(--line);">%s</div>' % esc(row[0])
        for cell in row[1:]:
            txt = cell["t"] if isinstance(cell, dict) else cell
            col = cell.get("color", "var(--slate)") if isinstance(cell, dict) else "var(--slate)"
            fw = "font-weight:600;" if (isinstance(cell, dict) and cell.get("bold")) else ""
            rows += '<div style="font-family:var(--serif);font-size:36px;padding:30px 0;border-bottom:1px solid var(--line);text-align:right;color:%s;%s">%s</div>' % (col, fw, esc(txt))
    s["_body"] = ('<div class="body" style="display:grid;grid-template-columns:0.92fr 1.08fr;gap:90px;align-items:center;">'
                  '%s<div style="display:grid;grid-template-columns:%s;">%s%s</div></div>'
                  % (left, s["table"].get("grid", "1.5fr 1fr 1fr"), head, rows))
    return std_slide(s)


def r_panels3(s):
    cols = []
    for i, p in enumerate(s["panels"]):
        bl = "border-left:1px solid var(--line);" if i else ""
        pad = ["46px 56px 46px 0", "46px 56px", "46px 0 46px 56px"][min(i, 2)]
        cols.append(
            '<div style="padding:%s;display:flex;flex-direction:column;justify-content:center;gap:20px;%s">'
            '<span style="font-size:27px;color:var(--slate);font-weight:600;">%s</span>'
            '<div style="display:flex;align-items:baseline;gap:18px;">'
            '<span style="font-family:var(--serif);font-size:78px;line-height:1;font-weight:600;color:var(--ink);">%s</span>'
            '<span style="font-size:30px;color:%s;font-weight:600;">%s</span></div>'
            '<span style="font-size:26px;color:var(--slate);">%s</span>'
            '<p style="font-size:25px;line-height:1.5;color:var(--slate);">%s</p></div>'
            % (pad, bl, esc(p["label"]), esc(p["value"]), p.get("tagcolor", "var(--slate)"),
               esc(p["tag"]), esc(p["band"]), esc(p["note"])))
    s["_body"] = '<div class="body" style="display:grid;grid-template-columns:repeat(3,1fr);align-items:stretch;">%s</div>' % "".join(cols)
    return std_slide(s)


def r_allocation(s):
    bars = ""
    for b in s["bars"]:
        bars += ('<div style="display:flex;flex-direction:column;gap:12px;">'
                 '<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                 '<span style="font-size:30px;font-weight:600;">%s</span>'
                 '<span style="font-family:var(--serif);font-size:38px;font-weight:600;color:var(--ink);">%d%%</span></div>'
                 '<div style="height:18px;background:var(--paper-2);"><div style="width:%d%%;height:100%%;background:%s;"></div></div></div>'
                 % (esc(b["name"]), b["pct"], b["pct"], b["color"]))
    tilts = ""
    for t in s["tilts"]:
        tilts += ('<div style="display:flex;gap:16px;align-items:flex-start;">'
                  '<span style="font-family:var(--serif);font-size:30px;color:%s;font-weight:600;flex-shrink:0;">%s</span>'
                  '<p style="font-size:28px;line-height:1.5;color:var(--ink);"><span style="font-weight:600;">%s</span> %s</p></div>'
                  % (t["color"], t["sign"], esc(t["strong"]), esc(t["rest"])))
    s["_body"] = ('<div class="body" style="display:grid;grid-template-columns:1.25fr 1fr;gap:96px;align-items:center;">'
                  '<div style="display:flex;flex-direction:column;gap:34px;"><span style="font-size:27px;color:var(--slate);font-weight:600;">%s</span>'
                  '<div style="display:flex;flex-direction:column;gap:30px;">%s</div></div>'
                  '<div style="display:flex;flex-direction:column;gap:26px;border-left:1px solid var(--line);padding-left:64px;">'
                  '<span style="font-size:25px;letter-spacing:0.18em;color:var(--gold);font-weight:600;">TILT</span>%s'
                  '<p style="font-size:25px;line-height:1.55;color:var(--slate);border-top:1px solid var(--line);padding-top:22px;margin-top:6px;">%s</p></div></div>'
                  % (esc(s["model"]), bars, tilts, esc(s["tilt_note"])))
    return std_slide(s)


def r_risks(s):
    cells = ""
    for r in s["risks"]:
        cells += ('<div style="display:flex;gap:30px;align-items:flex-start;padding:30px 0;border-bottom:1px solid var(--line-d);">'
                  '<span style="font-family:var(--serif);font-size:42px;color:var(--gold-2);flex-shrink:0;width:60px;">%s</span>'
                  '<div><h3 style="font-size:32px;font-weight:600;margin-bottom:8px;">%s</h3>'
                  '<p style="font-size:25px;line-height:1.5;color:#aeb8c4;">%s</p></div></div>'
                  % (esc(r["no"]), esc(r["h"]), esc(r["p"])))
    s["_body"] = ('<div class="body" style="display:grid;grid-template-columns:1fr 1fr;grid-auto-flow:column;'
                  'grid-template-rows:repeat(%d,auto);column-gap:110px;align-content:center;">%s</div>'
                  % ((len(s["risks"]) + 1) // 2, cells))
    s["dark"] = True
    return std_slide(s)


def r_checklist(s):
    cards = ""
    for c in s["items"]:
        cards += ('<div style="display:flex;flex-direction:column;gap:16px;border-top:2px solid var(--gold);padding-top:24px;">'
                  '<span style="font-family:var(--serif);font-size:30px;color:var(--gold-2);">%s</span>'
                  '<h3 style="font-size:32px;font-weight:700;">%s</h3>'
                  '<p style="font-size:26px;line-height:1.5;color:#aeb8c4;">%s</p></div>'
                  % (esc(c["no"]), esc(c["h"]), esc(c["p"])))
    inner = ('dark sec" style="overflow:hidden;position:relative;">'
             '<div style="position:absolute;bottom:-180px;right:-140px;width:480px;height:480px;border:1px solid rgba(169,133,69,0.22);transform:rotate(45deg);"></div>'
             '<div class="eyebrow"><span class="dash"></span><span class="lab" style="color:var(--gold-2);">%s</span></div>'
             '<h2 class="title">%s</h2><div class="rule dark"></div>'
             '<div class="body" style="display:grid;grid-template-columns:repeat(4,1fr);gap:50px;align-content:center;position:relative;">%s</div>'
             '<p style="font-size:24px;line-height:1.5;color:var(--slate-2);border-top:1px solid var(--line-d);padding-top:24px;position:relative;max-width:1640px;">%s</p>'
             % (esc(s.get("latin", "CHECKLIST")), esc(s["title"]), cards, esc(s["disclaimer"])))
    return _wrap(inner)


RENDERERS = {
    "cover": r_cover, "contents": r_contents, "houseview": r_houseview,
    "metrics3": r_metrics3, "table": r_table, "scenario": r_scenario,
    "sectors": r_sectors, "bonds": r_bonds, "panels3": r_panels3,
    "allocation": r_allocation, "risks": r_risks, "checklist": r_checklist,
}


def build(spec):
    slides = "\n".join(RENDERERS[s["type"]](s) for s in spec["slides"])
    return ("<!DOCTYPE html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>%s</title>"
            "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">"
            "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>"
            "<link href=\"https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">"
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css\">"
            "<style>%s</style></head><body>%s%s</body></html>"
            % (esc(spec.get("title", "마켓 아웃룩")), CSS, slides, FIT_JS))


# ── 내장 기본 콘텐츠: 2026 마켓 아웃룩 (원본 충실 재현) ──────────────────────
def default_spec(cover="A"):
    g, gold = "var(--pos)", "var(--gold)"
    return {
        "title": "2026 마켓 아웃룩 · 한화투자증권 리서치센터",
        "slides": [
            {"type": "cover", "variant": cover},
            {"type": "contents", "latin": "CONTENTS", "title": "목차", "pageno": "2026 OUTLOOK", "dark": True, "foot": "2026 MARKET OUTLOOK", "items": [
                {"no": "01", "ko": "핵심 요약", "en": "HOUSE VIEW"},
                {"no": "02", "ko": "글로벌 매크로 환경", "en": "MACRO"},
                {"no": "03", "ko": "금리·통화정책 전망", "en": "RATES"},
                {"no": "04", "ko": "국내 경제 전망", "en": "KOREA"},
                {"no": "05", "ko": "주식시장 전망", "en": "EQUITIES"},
                {"no": "06", "ko": "업종별 투자 전략", "en": "SECTORS"},
                {"no": "07", "ko": "채권시장 전망", "en": "BONDS"},
                {"no": "08", "ko": "환율·원자재", "en": "FX"},
                {"no": "09", "ko": "자산배분 가이드", "en": "ALLOCATION"},
                {"no": "10", "ko": "핵심 리스크 점검", "en": "RISKS"}]},
            {"type": "houseview", "latin": "HOUSE VIEW", "title": "핵심 요약", "pageno": "01 / 10",
             "lead": '완만한 성장 둔화와 금리 인하 사이클 진입. <span style="color:var(--slate);">주식과 채권의 균형을 다시 맞추는 한 해가 될 전망입니다.</span>',
             "cards": [
                {"no": "01", "h": "연착륙 기조", "p": "침체 없는 성장 둔화. 고용·소비가 완만히 식으며 물가 안정이 이어집니다."},
                {"no": "02", "h": "금리 인하 본격화", "p": "주요국 통화정책 완화 전환. 국내도 인하 행렬에 동참합니다."},
                {"no": "03", "h": "균형 자산배분", "p": "주식 비중확대와 채권 듀레이션 확대를 병행, 현금은 줄입니다."},
                {"no": "04", "h": "원화 강세 전환", "p": "금리차 축소와 수출 회복으로 원/달러는 점진적 하락이 예상됩니다."}]},
            {"type": "metrics3", "latin": "GLOBAL MACRO", "title": "글로벌 매크로 환경", "pageno": "02 / 10", "metrics": [
                {"label": "세계 경제성장률 (2026E)", "value": '+3.0<span style="font-size:54px;">%</span>', "note": "둔화하나 침체는 회피. 미국 견조, 신흥국 점진 회복."},
                {"label": "선진국 헤드라인 CPI", "value": '~2<span style="font-size:54px;">%</span>', "note": "목표 수준 근접. 디스인플레이션 흐름이 이어집니다."},
                {"label": "정책 방향", "value": "완화", "color": g, "note": "주요국 정책금리 인하 전환. 유동성 환경이 개선됩니다."}]},
            {"type": "table", "latin": "RATES & POLICY", "title": "금리·통화정책 전망", "pageno": "03 / 10", "foot": "전망치는 illustrative · 실제 수치로 교체",
             "left": [{"lead": True, "t": "정책금리는 인하 사이클로. 연말까지 완만한 추가 인하가 이어집니다."},
                      {"t": "실질금리 부담이 줄며 위험자산에 우호적인 환경이 조성됩니다. 다만 인하 속도는 데이터에 좌우되는 점진적 경로입니다."}],
             "table": {"cols": ["지역", "현재", "2026말 (E)"], "grid": "1.4fr 1fr 1fr", "rows": [
                ["미국 (Fed)", {"t": "4.50%"}, {"t": "3.50%", "color": g, "bold": True}],
                ["유로존 (ECB)", {"t": "3.00%"}, {"t": "2.25%", "color": g, "bold": True}],
                ["한국 (BOK)", {"t": "2.75%"}, {"t": "2.25%", "color": g, "bold": True}]]}},
            {"type": "table", "latin": "KOREA ECONOMY", "title": "국내 경제 전망", "pageno": "04 / 10", "foot": "전망치는 illustrative · 실제 수치로 교체",
             "split": "0.001fr 1fr", "left": [],
             "table": {"cols": ["주요 지표", "2025 (E)", "2026 (E)", "코멘트"], "grid": "2fr 1fr 1fr 1.4fr", "align": ["left", "right", "right", "left"], "rows": [
                ["실질 GDP 성장률", {"t": "1.6%"}, {"t": "1.9%", "color": g, "bold": True}, {"t": "수출·투자 중심 완만한 회복", "color": "var(--slate)"}],
                ["소비자물가 (CPI)", {"t": "2.2%"}, {"t": "2.0%", "color": "var(--ink)", "bold": True}, {"t": "목표 수준에서 안정", "color": "var(--slate)"}],
                ["수출 증가율", {"t": "2.5%"}, {"t": "4.0%", "color": g, "bold": True}, {"t": "반도체·자동차 주도", "color": "var(--slate)"}],
                ["기준금리 (연말)", {"t": "2.75%"}, {"t": "2.25%", "color": g, "bold": True}, {"t": "단계적 인하 지속", "color": "var(--slate)"}],
                ["원/달러 (연말)", {"t": "1,360"}, {"t": "1,300", "color": "var(--ink)", "bold": True}, {"t": "점진적 원화 강세", "color": "var(--slate)"}]]}},
            {"type": "scenario", "latin": "EQUITIES", "title": "주식시장 전망", "pageno": "05 / 10", "foot": "전망치는 illustrative · 실제 수치로 교체",
             "big": {"label": "KOSPI 기본 시나리오 (2026 목표)", "value": "3,100", "band": "상단 밴드 3,400 · 하단 2,650", "note": "이익 회복과 밸류에이션 정상화가 동반되며 완만한 우상향을 전망합니다."},
             "table": {"cols": ["시나리오", "EPS 증가", "적정 PER", "지수"], "grid": "1.3fr 1fr 1fr 1fr", "rows": [
                [{"t": "낙관", "color": g}, "+15%", "11.0x", {"t": "3,400", "size": "34px", "color": "var(--ink)", "bold": "600"}],
                [{"t": "기본", "bold": True}, "+10%", "10.2x", {"t": "3,100", "size": "34px", "color": gold, "bold": "700"}],
                [{"t": "비관", "color": "var(--neg)"}, "+3%", "9.0x", {"t": "2,650", "size": "34px", "color": "var(--ink)", "bold": "600"}]]}},
            {"type": "sectors", "latin": "SECTOR STRATEGY", "title": "업종별 투자 전략", "pageno": "06 / 10", "groups": [
                {"ko": "비중확대", "en": "OVERWEIGHT", "accent": "var(--pos)", "titlecolor": "var(--pos)", "items": ["반도체", "자동차·부품", "헬스케어·바이오", "인터넷·플랫폼"], "note": "실적 모멘텀과 AI·온디바이스 수요 수혜."},
                {"ko": "중립", "en": "NEUTRAL", "accent": "var(--slate-2)", "titlecolor": "var(--slate)", "items": ["은행·금융", "2차전지", "소비재·유통", "소재·화학"], "note": "개선 신호 확인 후 비중 조절 권고."},
                {"ko": "비중축소", "en": "UNDERWEIGHT", "accent": "var(--neg)", "titlecolor": "var(--neg)", "items": ["유틸리티", "통신", "건설·부동산", "필수소비재"], "note": "금리 인하기 상대 매력 둔화."}]},
            {"type": "bonds", "latin": "FIXED INCOME", "title": "채권시장 전망", "pageno": "07 / 10", "foot": "전망치는 illustrative · 실제 수치로 교체",
             "lead": "금리 인하기, 듀레이션을 늘릴 시점입니다.",
             "bullets": [{"strong": "국고채 장기물", "rest": "비중확대 — 금리 하락에 따른 자본이득 기대"},
                         {"strong": "우량 회사채(AA-급 이상)", "rest": "캐리 매력 유효"},
                         {"strong": "하이일드", "rest": "는 선별 접근 — 신용 사이클 후반 유의"}],
             "table": {"cols": ["금리 (%)", "현재", "2026말 (E)"], "grid": "1.5fr 1fr 1fr", "rows": [
                ["국고채 3년", {"t": "2.65"}, {"t": "2.30", "color": g, "bold": True}],
                ["국고채 10년", {"t": "3.05"}, {"t": "2.75", "color": g, "bold": True}],
                ["회사채 AA- 3년", {"t": "3.45"}, {"t": "3.15", "color": g, "bold": True}]]}},
            {"type": "panels3", "latin": "FX & COMMODITIES", "title": "환율·원자재", "pageno": "08 / 10", "foot": "전망치는 illustrative · 실제 수치로 교체", "panels": [
                {"label": "원/달러", "value": "1,300", "tag": "↓ 원화 강세", "tagcolor": g, "band": "예상 밴드 1,260–1,360", "note": "금리차 축소와 수출 회복으로 점진적 하락."},
                {"label": "국제유가 (WTI)", "value": "$70", "tag": "→ 박스권", "tagcolor": "var(--slate)", "band": "예상 밴드 $65–80 / 배럴", "note": "수요 둔화와 공급 조절이 균형."},
                {"label": "금 (Gold)", "value": "강세", "tag": "↑ 지속", "tagcolor": g, "band": "실질금리 하락 · 중앙은행 매수", "note": "포트폴리오 분산·헤지 수단으로 유효."}]},
            {"type": "allocation", "latin": "ASSET ALLOCATION", "title": "자산배분 가이드", "pageno": "09 / 10", "foot": "예시 배분 · 투자성향별 조정 필요",
             "model": "균형형 모델 포트폴리오 (Balanced)",
             "bars": [{"name": "주식", "pct": 45, "color": "var(--navy-900)"}, {"name": "채권", "pct": 35, "color": "var(--navy-700)"},
                      {"name": "대체·실물", "pct": 12, "color": "var(--gold)"}, {"name": "현금·단기", "pct": 8, "color": "var(--slate-2)"}],
             "tilts": [{"sign": "＋", "color": g, "strong": "주식 비중확대", "rest": "— 국내·선진국 핵심 우량주 중심"},
                       {"sign": "＋", "color": g, "strong": "채권 듀레이션 확대", "rest": "— 국고 장기물·우량 크레딧"},
                       {"sign": "－", "color": "var(--neg)", "strong": "현금 축소", "rest": "— 인하기 기회비용 확대"}],
             "tilt_note": "투자성향에 따라 안정형·성장형으로 비중을 가감하세요. 정기 리밸런싱을 권고합니다."},
            {"type": "risks", "latin": "KEY RISKS", "title": "핵심 리스크 점검", "pageno": "10 / 10", "risks": [
                {"no": "01", "h": "인플레이션 재반등", "p": "재정·임금 압력으로 인하 경로가 지연될 위험"},
                {"no": "02", "h": "지정학·교역 갈등", "p": "관세·공급망 분절에 따른 비용 상승 압력"},
                {"no": "03", "h": "신용 이벤트", "p": "부동산 PF·고금리 부채의 부실 전이 가능성"},
                {"no": "04", "h": "통화정책 오류", "p": "과도한 긴축 유지 또는 성급한 완화의 부작용"},
                {"no": "05", "h": "밸류에이션 부담", "p": "일부 자산의 쏠림과 기대 과열에 따른 변동성"},
                {"no": "＊", "h": "대응 원칙", "p": "분산과 품질 중심, 현금 버퍼로 변동성 관리"}]},
            {"type": "checklist", "latin": "CHECKLIST", "title": "개인투자자를 위한 4가지 원칙", "items": [
                {"no": "01", "h": "분산", "p": "자산·지역·통화를 나눠 한쪽 충격에 흔들리지 않게."},
                {"no": "02", "h": "듀레이션", "p": "인하기에는 채권 만기를 늘려 금리 하락을 활용."},
                {"no": "03", "h": "환·헤지", "p": "원화 강세 국면에선 해외자산 환헤지 비중을 점검."},
                {"no": "04", "h": "리밸런싱", "p": "목표 비중을 정하고 분기마다 규칙적으로 재조정."}],
             "disclaimer": "본 자료는 정보 제공을 목적으로 작성된 것으로 투자 권유를 위한 것이 아닙니다. 수치와 전망은 작성 시점의 가정에 기반한 illustrative 예시이며, 실제와 다를 수 있습니다. 투자의 최종 판단과 책임은 투자자 본인에게 있습니다. ⓒ 2026 한화투자증권 리서치센터."},
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=None, help="콘텐츠 JSON 경로 (생략 시 내장 2026 마켓 아웃룩)")
    ap.add_argument("--out", default=None, help="출력 HTML 경로")
    ap.add_argument("--cover", default="A", choices=["A", "B", "C"], help="기본 콘텐츠 표지 시안")
    ap.add_argument("--root", default=None)
    args = ap.parse_args()

    root = args.root or os.getcwd()
    if args.spec:
        with open(args.spec, encoding="utf-8") as f:
            spec = json.load(f)
        default_out = os.path.join(root, "reports", "decks", "deck.html")
    else:
        spec = default_spec(args.cover)
        default_out = os.path.join(root, "reports", "decks", "2026_마켓_아웃룩.html")

    out = args.out or default_out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(spec))
    print("[완료] %s  (슬라이드 %d장)" % (out, len(spec["slides"])))


if __name__ == "__main__":
    main()

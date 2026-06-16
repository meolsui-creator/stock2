[🇰🇷 한국어](README.md) · **🇺🇸 English**

# 📈 stock2 — Automated Stock Research Reports (Practice Project)

> Just tell it a stock name, and a team of **AI analysts collaborate** to analyze
> financials, charts, news, and risk — then export a
> **brokerage-research-style PPTX report** for you.
>
> ⚠️ **This is a learning/practice dummy project.** Do not use it for real
> investment decisions (buy/sell).

This README is written so that **even total beginners** (new to computers and
coding) can follow along, step by step. Take your time. 🙂

---

## 1. What does this do? (3-line summary)

1. You enter a **stock name** like `삼성전자` (Samsung Electronics).
2. Four AI analysts split the work: **financials / charts / news & sentiment / risk**.
3. The results are combined into a **Markdown report + presentation slides (PPTX/HTML)**.

Analysis follows a **value-investing perspective**, and every number includes its
**source and reference date**.

---

## 2. What you need first (prerequisites)

This project runs inside an AI tool called **Claude Code**. You need these 3 things:

| Item | What it is | Where to get it |
|---|---|---|
| **Claude Code** | The program that tells the AI what to do (core of this project) | <https://claude.com/claude-code> |
| **Python 3** | Used to generate the slides (PPTX/HTML) | <https://www.python.org/downloads/> — check "Add Python to PATH" ✅ |
| **DART API key** | A free key to fetch financial statements (only needed for financial analysis) | <https://opendart.fss.or.kr> — sign up → request a key (free, instant) |

> 💡 If you only want **news and chart** analysis, you don't need a DART key.
> You only need it for financial analysis.

---

## 3. Installation (just once)

### 3-1. Download this project

Open your command window (on Windows, use **PowerShell**) and type these lines one by one.

```bash
git clone https://github.com/meolsui-creator/stock2.git
cd stock2
```

> If it says `git` is not found, install it first from <https://git-scm.com>.

### 3-2. Add your DART key (only if you'll do financial analysis)

Create a new file named **`.env`** inside the project folder and write this one line.
Replace `your_issued_key` with the key you got from OpenDART.

```
DART_KEY=your_issued_key
```

> 🔒 The `.env` file is **never uploaded to GitHub** (blocked by `.gitignore`).
> Keep your key to yourself.

### 3-3. Install the slide-building library

To create PPTX reports, run this once.

```bash
python -m pip install python-pptx
```

> If you only build the HTML market-outlook deck, you don't even need this
> (it uses standard features only).

---

## 4. How to use it (the easiest way)

This project works when you simply **talk to Claude Code in plain language**.
Open Claude Code inside the folder and try typing things like the examples below
(Korean works great too).

| What you want | Say something like |
|---|---|
| Full report at once | `삼성전자 리포트 만들어줘` (Make a Samsung report) |
| Financials only | `삼성전자 재무 분석해줘` (Analyze Samsung's financials) |
| Charts only | `삼성전자 차트 봐줘` (Check Samsung's chart) |
| News & sentiment only | `삼성전자 최근 이슈 정리해줘` (Summarize recent Samsung issues) |
| Export to PPTX | `방금 리포트 PPTX로 만들어줘` (Export that report to PPTX) |

Claude will pick the right analyst, run the analysis, and save results into the
`reports/` folder.

### If you want to build slides directly (commands)

If a report Markdown (`reports/StockName.md`) already exists, you can build slides yourself.

```bash
# Stock report → PPTX (creates reports/pptx/삼성전자.pptx)
python .claude/skills/report-pptx/build_pptx.py "삼성전자"

# Market-outlook presentation deck → HTML (created under reports/decks/)
python .claude/skills/outlook-deck/build_deck.py --cover A
```

---

## 5. Where do the results go?

Everything is saved in the **`reports/` folder**.

```
reports/
├── 삼성전자.md            ← research body (Markdown)
├── pptx/삼성전자.pptx     ← presentation PPT report
├── decks/삼성전자.html    ← web slides
└── charts/삼성전자_price.png  ← stock price chart image
```

> 📂 The repo includes a **sample `삼성전자` (Samsung) output**, so open it first
> to get a feel for what the results look like.

---

## 6. Who does what? (The 4 AI analysts)

| Analyst | Role | Data source | DART key needed? |
|---|---|---|---|
| `fundamental-analyst` | ② Financials, earnings, filings | DART OpenAPI | ✅ Yes |
| `market-technical-analyst` | ③ Price, trend, volume | FinanceDataReader | ❌ No |
| `news-sentiment-analyst` | News & market sentiment | Web search | ❌ No |
| `risk-manager-analyst` | ④ Risk review | pykrx + the above results | ❌ No |

The report always has **5 parts**: ① Cover ② Financials ③ Charts ④ Risk ⑤ Overall opinion

---

## 7. When things go wrong (FAQ)

| Symptom | Fix |
|---|---|
| `python not found` | Install Python and make sure you checked **"Add to PATH"** during setup |
| `No module named 'pptx'` | Run `python -m pip install python-pptx` again |
| Financial analysis says `DART_KEY not set` | Check that `DART_KEY=...` is written correctly in `.env` |
| `git not found` | Install git from <https://git-scm.com> |

---

## 8. Folder structure (for reference)

```
stock2/
├── CLAUDE.md          ← project rules for the AI (delegation & output rules)
├── .env               ← your DART key (you create it; not uploaded to GitHub)
├── .claude/
│   ├── agents/        ← settings for the 4 AI analysts
│   └── skills/        ← slide-building skills (report-pptx, outlook-deck)
└── reports/           ← folder where analysis results are saved
```

---

## ⚠️ Disclaimer (please read)

- This project is for **learning/practice**.
- All outputs are educational analysis and **do not provide investment advice**
  such as buy/sell recommendations or price targets.
- Always make real investment decisions at your own responsibility, using
  officially verified information.

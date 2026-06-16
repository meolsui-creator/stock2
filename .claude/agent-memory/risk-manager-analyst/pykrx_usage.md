---
name: pykrx-usage
description: Which pykrx endpoints return data vs. fail empty in this environment, and how to compute market cap / trading value as a fallback
metadata:
  type: reference
---

pykrx is installed and importable. On startup it prints a harmless KRX login warning (KRX_ID/KRX_PW not set) — no API key is needed for the working endpoints.

Endpoint reliability observed (dates around 2026-06):
- `stock.get_market_ohlcv(start, end, ticker)` — WORKS. Returns columns 시가/고가/저가/종가/거래량/등락률 (Korean headers; index by date). Note: gives 거래량 (volume), NOT 거래대금 (trading value).
- `get_market_cap` / `get_market_cap_by_ticker`, `get_market_trading_value_by_date`, `get_market_fundamental` — FAILED, returning empty JSON ("Expecting value: line 1 column 1"). These hit KRX server endpoints that appear gated/unavailable in this env.

Fallback when cap/value endpoints fail:
- Approx 거래대금 = 거래량 × 종가 (per day); average over 20d for a liquidity baseline.
- Market cap = shares outstanding × 종가. Samsung Electronics (005930) common shares ≈ 5,969,782,550. Always label such market cap as computed/approximate with the price source and date, since it depends on the price series used (e.g. FinanceDataReader vs pykrx may differ on split-adjustment).

**Why:** Avoids re-discovering dead endpoints each run and keeps every number sourced.
**How to apply:** Default to get_market_ohlcv for liquidity; compute value/cap manually and disclose the method + source + 기준일.

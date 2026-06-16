---
name: liquidity-thresholds
description: Heuristic thresholds for judging KR-equity liquidity and size in risk analysis
metadata:
  type: reference
---

Working heuristics for liquidity/size commentary on KR equities (use as judgment aids, not hard rules):
- Large-cap / 대형주: market cap in the tens-to-hundreds of trillions KRW. Samsung Electronics (005930) is the KOSPI bellwether — top-of-market by cap and trading value, so 체결/슬리피지 (fill/slippage) risk from size is effectively negligible; the liquidity angle for such names is better framed as concentration/index-flow risk (passive & foreign flows can amplify volatility) rather than thin-book risk.
- For 대형주, daily trading value in the multiple-trillions KRW means individual orders rarely move the book. The more useful liquidity signal is a *trend*: falling volume on rising price (거래 동반 약화) = weakening conviction, not an execution problem.
- Mid/small-cap thin-liquidity flags worth raising: daily 거래대금 below ~1-수십억원, wide spreads, or volume spikes concentrated in few sessions.

**Why:** Keeps the liquidity section meaningful instead of boilerplate; for mega-caps the real risk is volatility/concentration, not fills.
**How to apply:** Match the framing to the cap tier — slippage talk for small caps, flow/volatility/momentum-divergence talk for mega caps.

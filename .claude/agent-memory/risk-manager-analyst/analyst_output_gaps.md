---
name: analyst-output-gaps
description: Recurring cross-check issues found when consolidating the 3 analyst outputs into the risk section
metadata:
  type: project
---

Recurring cross-check patterns when consolidating news/financial/chart outputs:
- Conflicting numbers across outputs should be reframed as a *risk signal*, not silently dropped. Example (Samsung 1Q2026): the financial analyst flagged record quarterly figures (매출 133.9조·영업이익 57.2조) as "unverifiable/unrealistic," but the news analyst cross-confirmed them as actual record results (HBM/AI memory cycle). Correct handling = treat as earnings *volatility / cycle-dependence* risk, not data-reliability risk. The orchestrator may supply a 정합성 메모 resolving such conflicts — honor it.
- Semiconductor/memory names: the dominant fundamental risk is almost always the memory cycle (HBM/DRAM ASP swings) plus competitive positioning vs SK하이닉스 in HBM. Recurring theme.
- Chart outputs often surface a momentum-divergence flag (price at band-high while volume fades) — pairs well as a technical risk alongside the cycle risk.
- Market-cap/시총 figures frequently differ between sources (news vs pykrx-computed vs FDR price base). Always reconcile the price base and label the source.

**Why:** Lets future risk sections resolve cross-output conflicts consistently instead of re-deriving the call.
**How to apply:** When two outputs disagree on a number, decide whether it is a reliability risk or a real-business risk before writing; lean on any orchestrator 정합성 메모.

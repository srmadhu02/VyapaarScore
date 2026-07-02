# UPI Cash-Flow Digital Footprint Scorer — Day 1 Deliverables

## What's in this folder
- `generate_data.py` — generates 6 months of synthetic UPI transactions for 4 merchant personas
- `score_engine.py` — the scoring engine (pure Python, framework-free — port straight into your Node/Python backend)
- `stable_kirana.csv`, `growing_shop.csv`, `seasonal_vendor.csv`, `risky_declining.csv` — the generated datasets

## The 4 Personas (your demo cast)
1. **Stable Kirana Store** — established, consistent daily sales, loyal repeat customers, near-zero failed transactions → should score highest
2. **Growing New Shop** — newer business, smaller history, but a clear upward revenue trend → should score high but slightly behind #1
3. **Seasonal Vendor** — real, legitimate business but "lumpy" cash flow (festival/wedding season spikes, dead months between) → mid score, tests whether your model unfairly punishes seasonality
4. **Risky Declining Shop** — declining revenue, thin/one-off customer base, high transaction failure rate, weak cash buffer → lowest score

## The Scoring Formula
```
Score (0-100) = 100 × [
    0.25 × Consistency
  + 0.15 × Growth
  + 0.20 × Liquidity Buffer
  + 0.15 × Payer Diversity
  + 0.15 × Reliability
  + 0.10 × Longevity
]
```
Each factor is normalized to 0–1 before weighting. Grades: A ≥80, B ≥65, C ≥45, D <45.

| Factor | What it measures | Why it matters for lending |
|---|---|---|
| Consistency | Coefficient of variation of daily inflow + % active days | Steady income = predictable repayment capacity |
| Growth | Avg month-over-month inflow growth (full calendar months only) | Business trajectory, not just current snapshot |
| Liquidity Buffer | Net retained cash ÷ avg daily outflow = "survival days" | Classic working-capital health signal |
| Payer Diversity | Unique payers + % repeat customers | Thin/one-off customer base = concentration risk |
| Reliability | Inverse of failed/bounced transaction rate | Proxy for operational/technical reliability |
| Longevity | Span of available transaction history | More history = more confidence in the score |

## Current Results (sanity check)
| Merchant | Score | Grade |
|---|---|---|
| Stable Kirana Store | 92.1 | A |
| Growing New Shop | 82.7 | A |
| Seasonal Vendor | 69.2 | B |
| Risky Declining Shop | 51.4 | C |

## Notes for tuning during the hackathon
- Weights live in `WEIGHTS` dict at the top of `score_engine.py` — must sum to 1.0
- Normalization bounds (the `low, high` args to `normalize()`) are the biggest lever for spreading scores apart — tune these first if scores cluster
- The `factor_details` dict in each result gives raw human-readable numbers (e.g. "buffer_days: 29.6") — use these directly for your "why this score" explainability UI on Day 3

## Next (Day 2)
Port `score_merchant()` into your backend (Supabase Edge Function or a simple Node/Python API route), and wire it to accept either:
(a) an uploaded CSV, or
(b) a merchant_id that pulls from your mock transactions table

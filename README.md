# VyapaarScore

**Explainable UPI cash-flow credit scoring for India's micro-merchants — with built-in fraud detection and a lender-ready recommendation engine.**

Built for IDBI Bank's Innovate 2026 hackathon.

## The Problem

~99% of India's micro-merchants — kirana stores, street vendors, small service providers — are **credit invisible**. No CIBIL history, no formal financials, despite processing regular digital payments via UPI. Banks and NBFCs can't assess their creditworthiness, so these merchants get excluded from formal working-capital loans and pushed toward informal lenders with high interest rates.

## The Solution

VyapaarScore turns a merchant's UPI transaction history into an **explainable trust score** — no bureau data, no collateral, just cash-flow behavior. Every score comes with a transparent factor-by-factor breakdown, actionable improvement tips, an anomaly/fraud check, a peer benchmark, and a rule-based lending recommendation — the full decision layer a bank actually needs, not just a number.

## What's built

| Layer | What it does |
|---|---|
| **Scoring Engine** (`score_engine.py`) | Computes a 0–100 explainable score from 6 weighted cash-flow factors |
| **Tips Engine** (`tips_engine.py`) | Rule-based, deterministic "improve your score" recommendations |
| **What-If Simulator** (`simulator.py`) | Re-scores real transaction data under hypothetical scenarios (more repeat customers, fewer failed transactions, etc.) — live, interactive sliders on the frontend |
| **Trust & Integrity Check** (`anomaly_detector.py`) | Flags wash-trading / scripted-transaction patterns consistent with score gaming — independent of the score itself |
| **Peer Benchmarking** (`benchmarking.py`) | Percentile comparison against a modeled category distribution (e.g. "top 27% of Kirana & Grocery Stores") |
| **Lender Recommendation Engine** (`lender_report.py`) | Translates score + integrity + benchmark into a concrete credit decision, with integrity overrides that can force manual review regardless of the numeric score |
| **FastAPI backend** (`main.py`) | Serves all of the above via `/score`, `/score_demo`, `/simulate`, `/categories` |
| **React dashboard** (`frontend/`) | Merchant View, Lender View (print/PDF-ready), and a simulated Account Aggregator consent flow |

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

Weights live in `WEIGHTS` in `score_engine.py`.

## Demo Personas

Five synthetic 6-month UPI transaction datasets, each telling a different story:

| Merchant | CSV | Score | Grade | Notes |
|---|---|---|---|---|
| Stable Kirana Store | `stable_kirana.csv` | 92.1 | A | Established, consistent, loyal customer base |
| Growing New Shop | `growing_shop.csv` | 82.7 | A | Newer business, clear upward trend |
| Seasonal Vendor | `seasonal_vendor.csv` | 69.3 | B | Legitimate but "lumpy" cash flow (festival spikes) |
| Risky Declining Shop | `risky_declining.csv` | 51.4 | C | Declining revenue, thin buffer, high failure rate |
| Gaming Attempt Shop | `gaming_attempt.csv` | 72.5 | B* | *Score looks fine — but Trust & Integrity Check flags it HIGH RISK (3 signals) and the Lender Recommendation overrides it to "Manual Review Required, ₹0" |

The last row is the key demo moment: **a naive score-only model would approve this merchant. VyapaarScore doesn't.**

## Running locally

**Backend:**
```bash
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Full API docs at `http://127.0.0.1:8000/docs`.

## Honest disclosures (say these out loud in the pitch)

- **Peer benchmarking** uses modeled category distributions, not real aggregate merchant data — no hackathon team has access to that. In production this would be replaced by real distributions from actually-scored merchants.
- **Account Aggregator flow** is a simulated consent journey demonstrating the mechanism and RBI-compliant framing, not a real bank integration.
- **Lender recommendations** are rule-based and fully explainable by design — not a black-box classifier — so every decision traces to a stated reason.

## Roadmap (post-hackathon)

- Real UPI data via the RBI Account Aggregator framework (currently simulated)
- Real peer benchmark data as the merchant base grows
- Additional anomaly signals (device/location metadata, cross-merchant graph analysis)
- Configurable weight tuning per lender risk appetite
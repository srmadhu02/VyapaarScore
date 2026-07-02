"""
UPI Cash-Flow Digital Footprint Scorer
Day 1: Core Scoring Engine

Computes an explainable 0-100 Trust Score from raw UPI transaction data,
using ONLY cash-flow behavior (no bureau data, no collateral).

This same logic is what you'll port into your backend (Node/Python) on
Day 2. Keeping it framework-free (pure Python) so it's easy to reuse
anywhere in Antigravity.
"""

import csv
from datetime import datetime, timedelta
from collections import defaultdict
import statistics as stats

# ---------------------------------------------------------------------
# WEIGHTS - tune these during the hackathon; they must sum to 1.0
# ---------------------------------------------------------------------
WEIGHTS = {
    "consistency": 0.25,     # regularity of inflow (low volatility = trustworthy)
    "growth": 0.15,          # month-over-month inflow trend
    "liquidity_buffer": 0.20, # how many days the merchant could survive on savings
    "payer_diversity": 0.15, # unique repeat customers vs one-off
    "reliability": 0.15,     # inverse of failed/bounced transaction rate
    "longevity": 0.10,       # length of active transaction history
}

SCORE_SCALE = 100


def load_transactions(filepath):
    rows = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["amount"] = float(r["amount"])
            r["timestamp"] = datetime.fromisoformat(r["timestamp"])
            rows.append(r)
    return rows


def daily_inflows(transactions):
    """Aggregate successful credit amounts per calendar day."""
    daily = defaultdict(float)
    for t in transactions:
        if t["type"] == "credit" and t["status"] == "success":
            day = t["timestamp"].date()
            daily[day] += t["amount"]
    return daily


def monthly_inflows(transactions):
    monthly = defaultdict(float)
    for t in transactions:
        if t["type"] == "credit" and t["status"] == "success":
            key = (t["timestamp"].year, t["timestamp"].month)
            monthly[key] += t["amount"]
    return dict(sorted(monthly.items()))


def normalize(value, low, high):
    """Clamp + scale a raw metric into 0-1."""
    if high == low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))


def compute_consistency(daily, window_days):
    """Lower coefficient-of-variation (std/mean) of daily inflow = more consistent."""
    values = list(daily.values())
    if len(values) < 2 or stats.mean(values) == 0:
        return 0.0, {"note": "insufficient data"}
    mean_v = stats.mean(values)
    std_v = stats.pstdev(values)
    cv = std_v / mean_v
    # lower CV is better; typical range 0.3 (very steady) to 2.5 (very erratic)
    score = 1 - normalize(cv, 0.3, 2.5)
    active_days_ratio = len(values) / max(window_days, 1)
    combined = 0.7 * score + 0.3 * normalize(active_days_ratio, 0.05, 0.9)
    return round(combined, 4), {
        "coefficient_of_variation": round(cv, 3),
        "active_days_ratio": round(active_days_ratio, 3),
    }


def compute_growth(transactions, monthly):
    """Month-over-month growth rate, averaged across FULL calendar months
    only (drops any partial first/last month, which otherwise causes
    misleading spikes e.g. a single day counted as 'month 1')."""
    dates = [t["timestamp"] for t in transactions]
    if not dates:
        return 0.5, {"note": "no data"}
    min_d, max_d = min(dates), max(dates)
    keys = list(monthly.keys())
    # drop the first month if data doesn't start on the 1st, and the last
    # month if data doesn't extend to that month's final day
    if keys and min_d.day != 1:
        keys = keys[1:]
    if keys and (max_d.year, max_d.month) == keys[-1] if keys else False:
        # only drop last month if it's clearly incomplete (< 25 days of data)
        last_month_days = sum(1 for d in dates if (d.year, d.month) == keys[-1])
        if last_month_days < 25:
            keys = keys[:-1]

    if len(keys) < 2:
        return 0.5, {"note": "insufficient full months"}
    growth_rates = []
    for i in range(1, len(keys)):
        prev, curr = monthly[keys[i-1]], monthly[keys[i]]
        if prev > 0:
            growth_rates.append((curr - prev) / prev)
    if not growth_rates:
        return 0.5, {"note": "no valid growth rate"}
    avg_growth = stats.mean(growth_rates)
    # normalize: -30% decline -> 0, +30% avg monthly growth -> 1
    score = normalize(avg_growth, -0.3, 0.3)
    return round(score, 4), {"avg_month_over_month_growth_pct": round(avg_growth * 100, 2)}


def compute_liquidity_buffer(transactions, daily):
    """Buffer days = (total net cash retained) / (avg daily outflow),
    i.e., how long the merchant could sustain operations with zero new inflow."""
    total_credit = sum(t["amount"] for t in transactions if t["type"] == "credit" and t["status"] == "success")
    total_debit = sum(t["amount"] for t in transactions if t["type"] == "debit" and t["status"] == "success")
    net_retained = max(0, total_credit - total_debit)

    debit_days = defaultdict(float)
    for t in transactions:
        if t["type"] == "debit" and t["status"] == "success":
            debit_days[t["timestamp"].date()] += t["amount"]
    avg_daily_outflow = (sum(debit_days.values()) / len(debit_days)) if debit_days else 1.0
    avg_daily_outflow = max(avg_daily_outflow, 1.0)

    buffer_days = net_retained / avg_daily_outflow
    score = normalize(buffer_days, 5, 400)  # 5 days = weak, 400+ days = strong
    return round(score, 4), {
        "estimated_buffer_days": round(buffer_days, 1),
        "net_retained_amount": round(net_retained, 2),
    }


def compute_payer_diversity(transactions):
    payer_counts = defaultdict(int)
    for t in transactions:
        if t["type"] == "credit" and t["status"] == "success":
            payer_counts[t["payer_vpa"]] += 1
    unique_payers = len(payer_counts)
    repeat_payers = sum(1 for c in payer_counts.values() if c >= 3)
    repeat_ratio = (repeat_payers / unique_payers) if unique_payers else 0

    diversity_score = normalize(unique_payers, 10, 250)
    loyalty_score = normalize(repeat_ratio, 0.05, 0.6)
    combined = 0.5 * diversity_score + 0.5 * loyalty_score
    return round(combined, 4), {
        "unique_payers": unique_payers,
        "repeat_customer_ratio": round(repeat_ratio, 3),
    }


def compute_reliability(transactions):
    total = len(transactions)
    failed = sum(1 for t in transactions if t["status"] == "failed")
    failure_rate = (failed / total) if total else 0
    score = 1 - normalize(failure_rate, 0.0, 0.10)  # 10%+ failure = worst case
    return round(score, 4), {"failure_rate_pct": round(failure_rate * 100, 2)}


def compute_longevity(transactions):
    if not transactions:
        return 0.0, {"note": "no data"}
    dates = [t["timestamp"] for t in transactions]
    span_days = (max(dates) - min(dates)).days
    score = normalize(span_days, 30, 180)
    return round(score, 4), {"history_span_days": span_days}


def score_transactions(transactions):
    """Core scoring logic — works on any in-memory list of transaction dicts.
    Used directly by score_merchant() (full history) and by compute_score_trend()
    (progressively larger slices of history, to show how the score evolves)."""
    if not transactions:
        return {
            "score": 0.0, "grade": "D",
            "factors_normalized_0_1": {}, "factor_details": {},
            "total_transactions": 0,
        }

    daily = daily_inflows(transactions)
    monthly = monthly_inflows(transactions)
    dates = [t["timestamp"] for t in transactions]
    window_days = max((max(dates) - min(dates)).days, 1)

    factors = {}
    details = {}

    factors["consistency"], details["consistency"] = compute_consistency(daily, window_days)
    factors["growth"], details["growth"] = compute_growth(transactions, monthly)
    factors["liquidity_buffer"], details["liquidity_buffer"] = compute_liquidity_buffer(transactions, daily)
    factors["payer_diversity"], details["payer_diversity"] = compute_payer_diversity(transactions)
    factors["reliability"], details["reliability"] = compute_reliability(transactions)
    factors["longevity"], details["longevity"] = compute_longevity(transactions)

    weighted_sum = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    final_score = round(weighted_sum * SCORE_SCALE, 1)

    if final_score >= 80:
        grade = "A"
    elif final_score >= 65:
        grade = "B"
    elif final_score >= 45:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": final_score,
        "grade": grade,
        "factors_normalized_0_1": factors,
        "factor_details": details,
        "total_transactions": len(transactions),
    }


def score_merchant(filepath):
    transactions = load_transactions(filepath)
    return score_transactions(transactions)


def compute_score_trend(filepath, min_history_days=60, step_days=30):
    """
    Computes the merchant's score AS OF each checkpoint in their history,
    using only transactions up to that point (an expanding window).

    This produces a genuine trajectory — e.g. a merchant who's growing will
    show a real upward trend, because their consistency/growth/buffer
    factors genuinely improve over time as more good history accumulates.

    min_history_days: skip checkpoints before this much history exists
                       (score on <60 days of data is too noisy to show)
    step_days: gap between checkpoints, e.g. every 30 days ~ "monthly"

    Returns: [{"date": "2026-03-02", "score": 61.4, "grade": "C"}, ...]
    """
    all_transactions = load_transactions(filepath)
    if not all_transactions:
        return []

    all_transactions.sort(key=lambda t: t["timestamp"])
    start_date = all_transactions[0]["timestamp"]
    end_date = all_transactions[-1]["timestamp"]

    trend = []
    checkpoint = start_date + timedelta(days=min_history_days)
    while checkpoint <= end_date:
        slice_txns = [t for t in all_transactions if t["timestamp"] <= checkpoint]
        result = score_transactions(slice_txns)
        trend.append({
            "date": checkpoint.date().isoformat(),
            "score": result["score"],
            "grade": result["grade"],
        })
        checkpoint += timedelta(days=step_days)

    # Always include the final, full-history checkpoint if not already covered
    if not trend or trend[-1]["date"] != end_date.date().isoformat():
        result = score_transactions(all_transactions)
        trend.append({
            "date": end_date.date().isoformat(),
            "score": result["score"],
            "grade": result["grade"],
        })

    return trend


if __name__ == "__main__":
    files = {
        "Stable Kirana Store": "/home/claude/wealthscore/stable_kirana.csv",
        "Growing New Shop": "/home/claude/wealthscore/growing_shop.csv",
        "Seasonal Vendor": "/home/claude/wealthscore/seasonal_vendor.csv",
        "Risky Declining Shop": "/home/claude/wealthscore/risky_declining.csv",
    }

    print("=" * 70)
    print("UPI CASH-FLOW DIGITAL FOOTPRINT SCORE - DEMO RESULTS")
    print("=" * 70)
    for name, path in files.items():
        result = score_merchant(path)
        print(f"\n{name}")
        print(f"  Score: {result['score']} / 100   Grade: {result['grade']}   (txns: {result['total_transactions']})")
        print("  Factor breakdown (0-1 scale):")
        for k, v in result["factors_normalized_0_1"].items():
            print(f"    - {k:18s}: {v}")
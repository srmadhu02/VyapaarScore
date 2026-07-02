"""
VyapaarScore — Rule-Based "Improve Your Score" Tips Engine

Takes the output of score_merchant() (from score_engine.py) and generates
2-3 targeted, plain-language tips explaining exactly which factor is
holding the score back and what real-world action would improve it.

Deliberately rule-based (not LLM-generated):
  - Free — no API cost
  - Deterministic — same input always gives same tips, reproducible in a demo
  - Explainable — each tip traces directly to a specific metric, which is
    the whole point of the "explainable AI" pitch for VyapaarScore
"""

# Each rule: (factor_key, condition_fn, tip_text_fn, priority)
# Lower priority number = shown first (most impactful / easiest to act on)

def _consistency_tip(details):
    cv = details.get("coefficient_of_variation", 0)
    active_pct = round(details.get("active_days_ratio", 0) * 100)
    return (
        f"Your daily sales vary a lot (volatility score: {cv}). Try to keep the "
        f"shop active more consistently — you're currently recording transactions "
        f"on only {active_pct}% of days. Even small, steady daily sales score "
        f"better than occasional large ones."
    )


def _growth_tip(details):
    growth_pct = details.get("avg_month_over_month_growth_pct", 0)
    return (
        f"Your monthly revenue trend is currently {growth_pct}% on average. "
        f"Consider running small promotions during slow months, or expanding "
        f"your product range, to build a steadier upward trend over the next "
        f"few months."
    )


def _liquidity_tip(details):
    buffer_days = details.get("estimated_buffer_days", 0)
    return (
        f"Your cash buffer is currently about {buffer_days} days — meaning "
        f"that's how long you could sustain the business with zero new sales. "
        f"Try to retain a larger cash cushion by reducing large one-off "
        f"outflows where possible, or spreading big supplier payments across "
        f"the month instead of one lump sum."
    )


def _diversity_tip(details):
    unique_payers = details.get("unique_payers", 0)
    repeat_pct = round(details.get("repeat_customer_ratio", 0) * 100)
    return (
        f"You have {unique_payers} unique customers, with {repeat_pct}% being "
        f"repeat buyers. Encourage repeat visits with a simple loyalty "
        f"incentive (e.g. a small discount on the 5th visit) — a broader, "
        f"more loyal customer base lowers your risk profile for lenders."
    )


def _reliability_tip(details):
    failure_pct = details.get("failure_rate_pct", 0)
    return (
        f"About {failure_pct}% of your UPI transactions are failing or "
        f"bouncing. Check your UPI app/QR code setup and internet connectivity "
        f"during peak hours — reducing failed transactions directly improves "
        f"your reliability score."
    )


def _longevity_tip(details):
    span_days = details.get("history_span_days", 0)
    return (
        f"You currently have {span_days} days of transaction history. "
        f"There's nothing to fix here except time — keep using UPI "
        f"consistently for your sales, and this factor will improve on its "
        f"own as your track record grows."
    )


RULES = {
    "consistency": {
        "threshold": 0.6,
        "tip_fn": _consistency_tip,
        "label": "Steady sales",
        "priority": 1,
    },
    "liquidity_buffer": {
        "threshold": 0.5,
        "tip_fn": _liquidity_tip,
        "label": "Cash buffer",
        "priority": 2,
    },
    "reliability": {
        "threshold": 0.7,
        "tip_fn": _reliability_tip,
        "label": "Transaction reliability",
        "priority": 3,
    },
    "payer_diversity": {
        "threshold": 0.5,
        "tip_fn": _diversity_tip,
        "label": "Customer base",
        "priority": 4,
    },
    "growth": {
        "threshold": 0.4,
        "tip_fn": _growth_tip,
        "label": "Revenue trend",
        "priority": 5,
    },
    "longevity": {
        "threshold": 0.4,
        "tip_fn": _longevity_tip,
        "label": "Transaction history",
        "priority": 6,
    },
}

MAX_TIPS = 3


def generate_tips(factors_normalized, factor_details):
    """
    factors_normalized: dict like {"consistency": 0.95, "growth": 0.54, ...}
                         (the factors_normalized_0_1 field from score_merchant())
    factor_details:      dict like {"consistency": {...}, "growth": {...}, ...}
                         (the factor_details field from score_merchant())

    Returns a list of up to MAX_TIPS dicts, sorted by priority:
    [{"factor": "liquidity_buffer", "label": "Cash buffer", "score": 0.21,
      "tip": "Your cash buffer is currently..."}]
    """
    candidates = []
    for factor_key, rule in RULES.items():
        score = factors_normalized.get(factor_key)
        if score is None:
            continue
        if score < rule["threshold"]:
            details = factor_details.get(factor_key, {})
            candidates.append({
                "factor": factor_key,
                "label": rule["label"],
                "score": score,
                "tip": rule["tip_fn"](details),
                "priority": rule["priority"],
            })

    # Weakest factors first (lowest score = most urgent), then by priority
    candidates.sort(key=lambda c: (c["score"], c["priority"]))
    return candidates[:MAX_TIPS]


def generate_strength(factors_normalized, factor_details):
    """
    Returns one positive callout for the merchant's strongest factor —
    balances the tips with something encouraging, good UX for a demo.
    """
    best_factor = max(factors_normalized, key=factors_normalized.get)
    best_score = factors_normalized[best_factor]
    label = RULES.get(best_factor, {}).get("label", best_factor.replace("_", " ").title())
    return {
        "factor": best_factor,
        "label": label,
        "score": best_score,
        "message": f"Your strongest factor is {label.lower()} — keep this up, it's actively boosting your score.",
    }


if __name__ == "__main__":
    from score_engine import score_merchant

    files = {
        "Stable Kirana Store": "/home/claude/wealthscore/stable_kirana.csv",
        "Growing New Shop": "/home/claude/wealthscore/growing_shop.csv",
        "Seasonal Vendor": "/home/claude/wealthscore/seasonal_vendor.csv",
        "Risky Declining Shop": "/home/claude/wealthscore/risky_declining.csv",
    }

    for name, path in files.items():
        result = score_merchant(path)
        tips = generate_tips(result["factors_normalized_0_1"], result["factor_details"])
        strength = generate_strength(result["factors_normalized_0_1"], result["factor_details"])

        print("=" * 70)
        print(f"{name}  —  Score: {result['score']}  Grade: {result['grade']}")
        print("=" * 70)
        print(f"\n✓ STRENGTH: {strength['message']}\n")
        if tips:
            print("IMPROVEMENT TIPS:")
            for i, t in enumerate(tips, 1):
                print(f"\n{i}. [{t['label']}] (score: {t['score']})")
                print(f"   {t['tip']}")
        else:
            print("No major weak points detected — all factors above threshold.")
        print()
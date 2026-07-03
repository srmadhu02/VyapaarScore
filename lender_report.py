"""
VyapaarScore — Lender Recommendation Engine

Translates the score + integrity check + benchmark into a concrete,
rule-based lending recommendation — the layer that makes this useful
to an actual bank/NBFC loan officer, not just interesting to look at.

Deliberately rule-based (not a black box "approve/deny"):
  - Every recommendation traces to explicit, statable rules
  - Integrity flags can override an otherwise-good score (a high score
    with high anomaly risk should NOT be silently approved)
  - This mirrors how real underwriting actually works: a score is one
    input to a decision, not the decision itself
"""

# grade -> (max_recommended_amount_inr, tier_label)
GRADE_LOAN_TIERS = {
    "A": (200000, "Preferred tier"),
    "B": (100000, "Standard tier"),
    "C": (50000, "Conditional tier"),
    "D": (0, "Not recommended without further review"),
}


def get_lender_recommendation(score, grade, integrity_result, benchmark_result=None):
    """
    score: float (0-100)
    grade: "A" | "B" | "C" | "D"
    integrity_result: output of anomaly_detector.check_integrity()
    benchmark_result: output of benchmarking.get_benchmark() (optional)

    Returns: {
        "decision": "recommend" | "recommend_with_conditions" | "manual_review_required" | "not_recommended",
        "max_recommended_amount": int (INR),
        "tier_label": str,
        "reasoning": [str, ...],   # bullet-point justification, for the report
        "conditions": [str, ...],  # only if decision requires conditions
    }
    """
    base_amount, tier_label = GRADE_LOAN_TIERS.get(grade, (0, "Not recommended without further review"))
    reasoning = [f"Score {score}/100 (Grade {grade}) places this merchant in the '{tier_label}' bracket."]
    conditions = []

    risk_level = integrity_result.get("risk_level", "low") if integrity_result else "low"
    flags = integrity_result.get("flags", []) if integrity_result else []

    # Integrity check can override an otherwise-good score — this is the
    # key design point: a high score with high anomaly risk should NOT
    # be silently approved.
    if risk_level == "high":
        decision = "manual_review_required"
        reasoning.append(
            f"Trust & Integrity Check flagged {len(flags)} high-priority anomaly signal(s) "
            f"in the transaction pattern. Automated approval is withheld pending manual review, "
            f"regardless of the numeric score."
        )
        max_amount = 0
    elif risk_level == "medium":
        decision = "recommend_with_conditions"
        conditions.append("Manually spot-check the flagged transaction patterns before disbursal.")
        reasoning.append(
            f"Trust & Integrity Check flagged {len(flags)} medium-priority signal(s) — "
            f"recommend proceeding with additional verification rather than full automated approval."
        )
        max_amount = round(base_amount * 0.6)
    else:
        max_amount = base_amount
        if grade == "D":
            decision = "not_recommended"
            reasoning.append("Score falls below the minimum threshold for automated recommendation.")
        elif grade == "C":
            decision = "recommend_with_conditions"
            conditions.append("Consider a shorter repayment tenure and/or a smaller initial ticket size.")
            reasoning.append("Grade C profiles are approved with conditions rather than full automatic approval.")
        else:
            decision = "recommend"
            reasoning.append("No integrity concerns detected — transaction patterns appear organic and consistent.")

    if benchmark_result:
        reasoning.append(
            f"Benchmarked at the {benchmark_result['percentile']}th percentile among "
            f"{benchmark_result['category_label']} peers (peer median: {benchmark_result['peer_median']})."
        )

    return {
        "decision": decision,
        "max_recommended_amount": max_amount,
        "tier_label": tier_label,
        "reasoning": reasoning,
        "conditions": conditions,
    }


DECISION_LABELS = {
    "recommend": ("Recommended for Credit", "success"),
    "recommend_with_conditions": ("Recommended with Conditions", "warning"),
    "manual_review_required": ("Manual Review Required", "danger"),
    "not_recommended": ("Not Recommended at This Time", "danger"),
}


if __name__ == "__main__":
    from score_engine import load_transactions, score_transactions
    from anomaly_detector import check_integrity
    from benchmarking import get_benchmark

    cases = [
        ("Stable Kirana Store", "stable_kirana.csv", "kirana_grocery"),
        ("Growing New Shop", "growing_shop.csv", "apparel_retail"),
        ("Seasonal Vendor", "seasonal_vendor.csv", "seasonal_festive"),
        ("Risky Declining Shop", "risky_declining.csv", "food_beverage"),
        ("Gaming Attempt Shop", "gaming_attempt.csv", "general_service"),
    ]

    for name, path, category in cases:
        txns = load_transactions(path)
        score_result = score_transactions(txns)
        integrity_result = check_integrity(txns)
        benchmark_result = get_benchmark(score_result["score"], category)

        rec = get_lender_recommendation(
            score_result["score"], score_result["grade"], integrity_result, benchmark_result
        )
        label, tone = DECISION_LABELS[rec["decision"]]

        print(f"{name}  —  Score {score_result['score']} ({score_result['grade']})")
        print(f"  DECISION: {label}  |  Max amount: Rs.{rec['max_recommended_amount']:,}")
        for r in rec["reasoning"]:
            print(f"   - {r}")
        if rec["conditions"]:
            for c in rec["conditions"]:
                print(f"   ! Condition: {c}")
        print()
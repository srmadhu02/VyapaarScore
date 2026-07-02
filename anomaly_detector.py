"""
VyapaarScore — Trust & Integrity Check (Anomaly Detector)

Answers the question every underwriter (and every skeptical hackathon
judge) will ask: "couldn't a merchant just fake transactions to inflate
this score?"

This module scans the SAME transaction data used for scoring and flags
patterns consistent with wash-trading / scripted transactions / a
last-minute attempt to game the score before applying for credit.

Deliberate design choice: this does NOT silently subtract points from
the score. It returns a separate risk_level + explicit flags, meant to
be shown alongside the score for human review. Silently penalizing
based on suspicion alone would be neither fair nor explainable — and
"we flag transparently, we don't black-box penalize" is a stronger,
more honest pitch than quietly gaming the number down.
"""

from collections import defaultdict
from statistics import mean, pstdev
from datetime import timedelta


def _round_number_ratio(credit_txns):
    """% of transactions with a suspiciously 'round' amount (exact multiples
    of 100). Real customer payments are rarely perfectly round; a spike here
    suggests scripted/fake transactions rather than organic sales."""
    if not credit_txns:
        return 0.0, 0
    round_count = sum(1 for t in credit_txns if t["amount"] % 100 == 0)
    ratio = round_count / len(credit_txns)
    return ratio, round_count


def _max_burst_velocity(transactions, window_minutes=10):
    """Largest number of transactions occurring within any rolling
    window_minutes window. Real walk-in customers arrive spread out over
    a day; a tight cluster suggests scripted/automated transactions."""
    timestamps = sorted(t["timestamp"] for t in transactions)
    if len(timestamps) < 2:
        return 0
    max_count = 1
    window = timedelta(minutes=window_minutes)
    left = 0
    for right in range(len(timestamps)):
        while timestamps[right] - timestamps[left] > window:
            left += 1
        max_count = max(max_count, right - left + 1)
    return max_count


def _recent_payer_concentration(credit_txns, recent_days=14):
    """% of transactions in the most recent window coming from just the
    single most frequent payer. A sudden concentration right before
    'application time' is a classic wash-trading signature."""
    if not credit_txns:
        return 0.0, None
    last_date = max(t["timestamp"] for t in credit_txns)
    cutoff = last_date - timedelta(days=recent_days)
    recent = [t for t in credit_txns if t["timestamp"] >= cutoff]
    if not recent:
        return 0.0, None

    payer_counts = defaultdict(int)
    for t in recent:
        payer_counts[t["payer_vpa"]] += 1
    top_payer, top_count = max(payer_counts.items(), key=lambda kv: kv[1])
    concentration = top_count / len(recent)
    return concentration, top_payer


def _duplicate_amount_ratio(credit_txns):
    """% of transactions that share the EXACT same (payer, amount) pair as
    another transaction. A high ratio suggests a scripted loop rather than
    organic, varied customer purchases."""
    if not credit_txns:
        return 0.0
    pair_counts = defaultdict(int)
    for t in credit_txns:
        pair_counts[(t["payer_vpa"], t["amount"])] += 1
    duplicated = sum(c for c in pair_counts.values() if c >= 3)  # same pair 3+ times
    return duplicated / len(credit_txns)


def _recent_spike_zscore(credit_txns, recent_days=14):
    """How many standard deviations the recent daily inflow average is
    above the historical (older) daily average. A large positive spike
    right before the data ends is consistent with an attempt to inflate
    the score right before applying for credit."""
    if not credit_txns:
        return 0.0

    daily = defaultdict(float)
    for t in credit_txns:
        daily[t["timestamp"].date()] += t["amount"]

    last_date = max(t["timestamp"] for t in credit_txns).date()
    cutoff = last_date - timedelta(days=recent_days)

    older_values = [v for d, v in daily.items() if d < cutoff]
    recent_values = [v for d, v in daily.items() if d >= cutoff]

    if len(older_values) < 5 or not recent_values:
        return 0.0  # not enough history to judge a spike

    hist_mean = mean(older_values)
    hist_std = pstdev(older_values) if len(older_values) > 1 else 1.0
    hist_std = max(hist_std, 1.0)
    recent_mean = mean(recent_values)

    z = (recent_mean - hist_mean) / hist_std
    return round(z, 2)


def check_integrity(transactions):
    """
    Runs all integrity checks and returns a combined risk assessment.

    Returns: {
        "risk_level": "low" | "medium" | "high",
        "anomaly_score": 0.0-1.0,
        "flags": [ {"signal": ..., "severity": ..., "message": ...}, ... ],
        "clean": bool  (True if zero flags triggered)
    }
    """
    credit_txns = [t for t in transactions if t["type"] == "credit" and t["status"] == "success"]

    flags = []
    points = 0.0  # accumulated risk points -> converted to anomaly_score

    round_ratio, round_count = _round_number_ratio(credit_txns)
    if round_ratio > 0.35:
        severity = "high" if round_ratio > 0.55 else "medium"
        points += 0.3 if severity == "high" else 0.15
        flags.append({
            "signal": "round_number_amounts",
            "severity": severity,
            "message": f"{round(round_ratio*100)}% of transactions are exact round amounts "
                       f"({round_count} transactions) — unusually high for organic customer payments."
        })

    burst = _max_burst_velocity(transactions)
    if burst >= 6:
        severity = "high" if burst >= 10 else "medium"
        points += 0.25 if severity == "high" else 0.12
        flags.append({
            "signal": "transaction_burst",
            "severity": severity,
            "message": f"{burst} transactions occurred within a single 10-minute window — "
                       f"a pattern more consistent with scripted activity than walk-in customers."
        })

    concentration, top_payer = _recent_payer_concentration(credit_txns)
    if concentration > 0.5:
        severity = "high" if concentration > 0.7 else "medium"
        points += 0.25 if severity == "high" else 0.12
        flags.append({
            "signal": "recent_payer_concentration",
            "severity": severity,
            "message": f"{round(concentration*100)}% of the last 14 days' transactions came from a "
                       f"single payer — a sudden concentration right before scoring is a wash-trading signature."
        })

    dup_ratio = _duplicate_amount_ratio(credit_txns)
    if dup_ratio > 0.15:
        severity = "high" if dup_ratio > 0.3 else "medium"
        points += 0.2 if severity == "high" else 0.1
        flags.append({
            "signal": "repeated_amount_pattern",
            "severity": severity,
            "message": f"{round(dup_ratio*100)}% of transactions repeat the exact same amount from "
                       f"the same payer 3+ times — suggests scripted, non-organic activity."
        })

    spike_z = _recent_spike_zscore(credit_txns)
    if spike_z > 2.5:
        severity = "high" if spike_z > 4 else "medium"
        points += 0.25 if severity == "high" else 0.12
        flags.append({
            "signal": "sudden_inflow_spike",
            "severity": severity,
            "message": f"Recent daily inflow is {spike_z} standard deviations above the historical "
                       f"average — an unexplained spike right before the most recent data point."
        })

    anomaly_score = round(min(points, 1.0), 3)
    if anomaly_score >= 0.5:
        risk_level = "high"
    elif anomaly_score >= 0.2:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "anomaly_score": anomaly_score,
        "flags": flags,
        "clean": len(flags) == 0,
    }


if __name__ == "__main__":
    from score_engine import load_transactions

    files = {
        "Stable Kirana Store": "stable_kirana.csv",
        "Growing New Shop": "growing_shop.csv",
        "Seasonal Vendor": "seasonal_vendor.csv",
        "Risky Declining Shop": "risky_declining.csv",
    }

    for name, path in files.items():
        txns = load_transactions(path)
        result = check_integrity(txns)
        print(f"{name}: risk={result['risk_level']}  score={result['anomaly_score']}  "
              f"flags={len(result['flags'])}")
        for f in result["flags"]:
            print(f"   [{f['severity']}] {f['message']}")
        print()
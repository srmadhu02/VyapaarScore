"""
VyapaarScore — Peer Benchmarking

Turns a raw score into a relative, intuitive statement: "You're in the
top 30% of Kirana & Grocery merchants" instead of just "your score is 78."

IMPORTANT / HONEST FRAMING:
This uses MODELED category distributions, not real aggregate merchant
data (no hackathon team has access to that). Each category's distribution
is built from a realistic mean/spread we'd expect for that business type,
based on how the scoring factors typically behave for that kind of
merchant. In production, this would be replaced by the real distribution
of actual scored merchants in that category, updated continuously.

Say this explicitly in your pitch — it's a demonstration of the mechanism,
not a claim of real aggregate data. That honesty is a strength, not a
weakness, in front of judges.
"""

import random
import statistics as stats

random.seed(11)  # deterministic peer distributions across runs

# category_key -> (mean_score, std_dev, display_label)
CATEGORY_PROFILES = {
    "kirana_grocery": (74, 11, "Kirana & Grocery Stores"),
    "apparel_retail": (66, 14, "Apparel & General Retail"),
    "seasonal_festive": (58, 17, "Seasonal & Festive Goods Vendors"),
    "food_beverage": (52, 15, "Small Food & Beverage Outlets"),
    "general_service": (63, 14, "General Services & Repair Shops"),
}

PEER_SAMPLE_SIZE = 500


def _generate_peer_distribution(category_key):
    """Generates a realistic reference distribution of scores for a category.
    Cached implicitly by call site (see get_benchmark) to avoid regenerating
    on every request."""
    mean_score, std_dev, _ = CATEGORY_PROFILES[category_key]
    samples = [
        max(0, min(100, round(random.gauss(mean_score, std_dev), 1)))
        for _ in range(PEER_SAMPLE_SIZE)
    ]
    return samples


_DISTRIBUTION_CACHE = {}


def get_benchmark(score, category_key):
    """
    Returns how a given score compares to its category's peer distribution.

    Returns: {
        "category_label": "Kirana & Grocery Stores",
        "percentile": 78,               # this merchant beats 78% of peers
        "peer_median": 74.0,
        "peer_mean": 73.8,
        "message": "You're in the top 22% of Kirana & Grocery Stores."
    }
    """
    if category_key not in CATEGORY_PROFILES:
        category_key = "general_service"  # safe fallback

    if category_key not in _DISTRIBUTION_CACHE:
        _DISTRIBUTION_CACHE[category_key] = _generate_peer_distribution(category_key)
    distribution = _DISTRIBUTION_CACHE[category_key]

    _, _, label = CATEGORY_PROFILES[category_key]

    below_or_equal = sum(1 for s in distribution if s <= score)
    percentile = round((below_or_equal / len(distribution)) * 100)
    top_pct = 100 - percentile

    if percentile >= 90:
        message = f"You're in the top {max(top_pct, 1)}% of {label} — an exceptionally strong profile."
    elif percentile >= 50:
        message = f"You're in the top {top_pct}% of {label} — above the typical peer in this category."
    else:
        message = f"You're currently ahead of {percentile}% of {label} — there's room to close the gap with typical peers."

    return {
        "category_key": category_key,
        "category_label": label,
        "percentile": percentile,
        "peer_median": round(stats.median(distribution), 1),
        "peer_mean": round(stats.mean(distribution), 1),
        "message": message,
    }


def list_categories():
    """For populating a dropdown in the UI."""
    return [
        {"key": k, "label": v[2]} for k, v in CATEGORY_PROFILES.items()
    ]


if __name__ == "__main__":
    test_cases = [
        ("Stable Kirana Store", 92.1, "kirana_grocery"),
        ("Growing New Shop", 82.7, "apparel_retail"),
        ("Seasonal Vendor", 69.3, "seasonal_festive"),
        ("Risky Declining Shop", 51.4, "food_beverage"),
        ("Gaming Attempt Shop", 72.5, "general_service"),
    ]

    for name, score, category in test_cases:
        result = get_benchmark(score, category)
        print(f"{name} (score {score}, {result['category_label']})")
        print(f"  Percentile: {result['percentile']}  |  Peer median: {result['peer_median']}  |  Peer mean: {result['peer_mean']}")
        print(f"  {result['message']}\n")
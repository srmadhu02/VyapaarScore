"""
UPI Cash-Flow Digital Footprint Scorer
Day 1: Synthetic Data Generator

Generates 6 months of realistic daily UPI transaction data for 4 merchant
personas, designed so the scoring engine (score_engine.py) clearly
differentiates them — good demo material for the hackathon.

Personas:
  1. stable_kirana      -> High score (reliable, consistent, established)
  2. growing_shop        -> Medium-high score (upward trend, newer)
  3. seasonal_vendor      -> Medium score (volatile but real business)
  4. risky_declining      -> Low score (declining, unreliable, thin customer base)
"""

import csv
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

START_DATE = datetime(2025, 12, 31)  # 6 months back from ~ July 1 2026
NUM_DAYS = 182

PAYER_NAMES = [f"user{n}@okhdfc" for n in range(1, 400)]
PAYER_NAMES += [f"cust{n}@ybl" for n in range(1, 400)]
PAYER_NAMES += [f"payer{n}@paytm" for n in range(1, 400)]

MERCHANT_VPA = {
    "stable_kirana": "sharma.kirana@okicici",
    "growing_shop": "newageapparel@ybl",
    "seasonal_vendor": "festivedecor@okaxis",
    "risky_declining": "citychaishop@paytm",
}


def txn_id():
    return "TXN" + uuid.uuid4().hex[:12].upper()


def gen_stable_kirana():
    """Established kirana store: daily transactions, low volatility,
    slow steady growth, large repeat-customer base, near-zero failures."""
    rows = []
    base_daily_txns = 22
    base_ticket = 180
    repeat_pool = random.sample(PAYER_NAMES, 150)  # loyal customer base
    casual_pool = random.sample([p for p in PAYER_NAMES if p not in repeat_pool], 200)  # local neighborhood walk-ins

    for day in range(NUM_DAYS):
        date = START_DATE + timedelta(days=day)
        # slow linear growth over 6 months (~15% growth)
        growth_factor = 1 + (day / NUM_DAYS) * 0.15
        weekday_boost = 1.15 if date.weekday() in (5, 6) else 1.0  # weekend bump
        num_txns = max(1, int(random.gauss(base_daily_txns * growth_factor * weekday_boost, 2.5)))

        for _ in range(num_txns):
            # 85% repeat customers, 15% new/one-off (from a bounded local pool)
            payer = random.choice(repeat_pool) if random.random() < 0.85 else random.choice(casual_pool)
            amount = max(20, round(random.gauss(base_ticket, 60), 2))
            hour = random.choices(range(7, 22), weights=[1,2,3,4,5,6,6,5,4,4,5,6,6,4,2])[0]
            ts = date.replace(hour=hour, minute=random.randint(0, 59))
            status = "success" if random.random() > 0.005 else "failed"  # 0.5% failure
            rows.append([txn_id(), ts.isoformat(), amount, "credit", payer, status, MERCHANT_VPA["stable_kirana"]])

        # occasional debit (supplier payment / refund) - small %
        if random.random() < 0.1:
            amount = round(random.uniform(500, 3000), 2)
            ts = date.replace(hour=random.randint(9, 18))
            rows.append([txn_id(), ts.isoformat(), amount, "debit", "supplier@okicici", "success", MERCHANT_VPA["stable_kirana"]])

    return rows


def gen_growing_shop():
    """Newer small apparel/general shop, ~6 months of history, clear
    upward growth trend, moderately diverse customers, very few failures."""
    rows = []
    base_daily_txns = 6
    base_ticket = 450
    repeat_pool = random.sample(PAYER_NAMES, 60)
    casual_pool = random.sample([p for p in PAYER_NAMES if p not in repeat_pool], 130)

    for day in range(NUM_DAYS):
        date = START_DATE + timedelta(days=day)
        # strong growth: starts small, nearly doubles by month 6
        growth_factor = 1 + (day / NUM_DAYS) * 0.9
        weekend_boost = 1.3 if date.weekday() in (5, 6) else 1.0
        num_txns = max(0, int(random.gauss(base_daily_txns * growth_factor * weekend_boost, 2)))

        for _ in range(num_txns):
            payer = random.choice(repeat_pool) if random.random() < 0.55 else random.choice(casual_pool)
            amount = max(50, round(random.gauss(base_ticket * growth_factor**0.3, 150), 2))
            hour = random.randint(10, 21)
            ts = date.replace(hour=hour, minute=random.randint(0, 59))
            status = "success" if random.random() > 0.02 else "failed"  # 2% failure
            rows.append([txn_id(), ts.isoformat(), amount, "credit", payer, status, MERCHANT_VPA["growing_shop"]])

        if random.random() < 0.08:
            amount = round(random.uniform(800, 5000), 2)
            ts = date.replace(hour=random.randint(9, 18))
            rows.append([txn_id(), ts.isoformat(), amount, "debit", "wholesaler@ybl", "success", MERCHANT_VPA["growing_shop"]])

    return rows


def gen_seasonal_vendor():
    """Festive decor / seasonal goods vendor: highly volatile, big spikes
    around festival windows, near-dead months otherwise, real but 'lumpy'
    business. Moderate failure rate due to bulk/rush order issues."""
    rows = []
    # festival spike windows (day index ranges within the 182-day period)
    spike_windows = [(20, 35), (95, 115), (150, 170)]  # e.g. wedding season, festival, New Year
    repeat_pool = random.sample(PAYER_NAMES, 40)
    casual_pool = random.sample([p for p in PAYER_NAMES if p not in repeat_pool], 110)

    for day in range(NUM_DAYS):
        date = START_DATE + timedelta(days=day)
        in_spike = any(s <= day <= e for s, e in spike_windows)
        base = random.gauss(14, 5) if in_spike else random.gauss(1.5, 1.2)
        num_txns = max(0, int(base))

        for _ in range(num_txns):
            payer = random.choice(repeat_pool) if random.random() < 0.4 else random.choice(casual_pool)
            amount = max(100, round(random.gauss(650, 300), 2))
            hour = random.randint(9, 20)
            ts = date.replace(hour=hour, minute=random.randint(0, 59))
            status = "success" if random.random() > 0.04 else "failed"  # 4% failure
            rows.append([txn_id(), ts.isoformat(), amount, "credit", payer, status, MERCHANT_VPA["seasonal_vendor"]])

        if in_spike and random.random() < 0.2:
            amount = round(random.uniform(1000, 8000), 2)
            ts = date.replace(hour=random.randint(9, 18))
            rows.append([txn_id(), ts.isoformat(), amount, "debit", "rawmaterial@okaxis", "success", MERCHANT_VPA["seasonal_vendor"]])

    return rows


def gen_risky_declining():
    """Small tea/chai shop showing a declining trend, thin & mostly
    one-off customer base, higher failure/bounce rate, low buffer -
    a realistic 'risky' profile for score contrast."""
    rows = []
    base_daily_txns = 10
    base_ticket = 30
    repeat_pool = random.sample(PAYER_NAMES, 15)  # very thin loyal base
    casual_pool = random.sample([p for p in PAYER_NAMES if p not in repeat_pool], 90)  # mostly passersby

    for day in range(NUM_DAYS):
        date = START_DATE + timedelta(days=day)
        # declining trend: starts okay, drops off ~40% by end
        decline_factor = 1 - (day / NUM_DAYS) * 0.4
        # add noisy volatility on top
        volatility = random.gauss(1, 0.35)
        num_txns = max(0, int(base_daily_txns * decline_factor * max(0.2, volatility)))

        for _ in range(num_txns):
            payer = random.choice(repeat_pool) if random.random() < 0.25 else random.choice(casual_pool)
            amount = max(10, round(random.gauss(base_ticket, 15), 2))
            hour = random.randint(6, 22)
            ts = date.replace(hour=hour, minute=random.randint(0, 59))
            status = "success" if random.random() > 0.09 else "failed"  # 9% failure rate
            rows.append([txn_id(), ts.isoformat(), amount, "credit", payer, status, MERCHANT_VPA["risky_declining"]])

        # occasional larger debit outflow that strains buffer
        if random.random() < 0.12:
            amount = round(random.uniform(300, 1200), 2)
            ts = date.replace(hour=random.randint(9, 20))
            rows.append([txn_id(), ts.isoformat(), amount, "debit", "landlord@paytm", "success", MERCHANT_VPA["risky_declining"]])

    return rows


def write_csv(filename, rows):
    header = ["transaction_id", "timestamp", "amount", "type", "payer_vpa", "status", "merchant_vpa"]
    rows_sorted = sorted(rows, key=lambda r: r[1])
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_sorted)
    print(f"Wrote {len(rows_sorted)} rows -> {filename}")


if __name__ == "__main__":
    personas = {
        "stable_kirana": gen_stable_kirana,
        "growing_shop": gen_growing_shop,
        "seasonal_vendor": gen_seasonal_vendor,
        "risky_declining": gen_risky_declining,
    }
    for name, gen_fn in personas.items():
        rows = gen_fn()
        write_csv(f"/home/claude/wealthscore/{name}.csv", rows)

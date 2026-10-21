"""Generate a SYNTHETIC sample dataset in the UIDAI enrolment layout.

Columns: date (dd-mm-yyyy), state, district, pincode,
         age_0_5, age_5_17, age_18_greater

Nothing here is real enrolment data. Pincodes are invented (valid-looking
6-digit codes with a plausible regional prefix). The file exists so the
dashboard and the website can be run end to end without the real dataset.

Usage:  python scripts/generate_sample_data.py
"""
import os

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# state -> (pincode prefix, {district: relative size})
STATES = {
    "Maharashtra": ("41", {"Pune": 1.3, "Mumbai Suburban": 1.5, "Nagpur": 0.9, "Thane": 1.2, "Nashik": 0.8}),
    "Uttar Pradesh": ("22", {"Lucknow": 1.2, "Kanpur Nagar": 1.0, "Varanasi": 0.9, "Gorakhpur": 0.9, "Agra": 0.8}),
    "Bihar": ("80", {"Patna": 1.3, "Gaya": 0.8, "Muzaffarpur": 0.8, "Bhagalpur": 0.7, "Darbhanga": 0.7}),
    "Karnataka": ("56", {"Bengaluru Urban": 1.6, "Mysuru": 0.8, "Belagavi": 0.8, "Dharwad": 0.7, "Kalaburagi": 0.7}),
    "Tamil Nadu": ("60", {"Chennai": 1.4, "Coimbatore": 1.0, "Madurai": 0.8, "Salem": 0.7, "Tiruchirappalli": 0.7}),
    "West Bengal": ("71", {"Kolkata": 1.4, "Howrah": 1.0, "Darjeeling": 0.6, "Murshidabad": 1.0, "Paschim Medinipur": 0.8}),
}
PINCODES_PER_DISTRICT = 4
DATES = pd.date_range("2025-03-01", "2025-12-31", freq="D")

# (district, pincode index or None for the whole district, start, days, multiplier)
EVENTS = [
    ("Pune", 0, "2025-06-10", 3, 5.0),
    ("Patna", None, "2025-09-20", 7, 2.6),
    ("Coimbatore", 2, "2025-08-04", 2, 6.0),
    ("Murshidabad", 1, "2025-11-12", 3, 5.0),
    ("Lucknow", None, "2025-07-01", 5, 2.2),
    ("Bengaluru Urban", 3, "2025-10-06", 2, 6.0),
]


def build_pincodes():
    used = set()
    out = []
    for state, (prefix, districts) in STATES.items():
        for district, size in districts.items():
            for i in range(PINCODES_PER_DISTRICT):
                while True:
                    pin = int(prefix + f"{rng.integers(0, 1000):03d}")
                    if pin not in used:
                        used.add(pin)
                        break
                out.append((state, district, i, pin, size * rng.lognormal(0, 0.35)))
    return out


def main():
    event_mult = {}
    for district, idx, start, days, mult in EVENTS:
        for d in pd.date_range(start, periods=days):
            event_mult[(district, idx, d)] = mult

    rows = []
    for state, district, idx, pin, weight in build_pincodes():
        for day in DATES:
            weekend = day.dayofweek >= 5
            if rng.random() > (0.45 if weekend else 0.75):
                continue
            m = event_mult.get((district, None, day), 1.0) * event_mult.get((district, idx, day), 1.0)
            school = 1.6 if day.month in (6, 7) else 1.0  # admission season lifts child enrolments
            drift = 1 + 0.0006 * (day - DATES[0]).days
            base = 7.0 * weight * m
            a05 = rng.poisson(base * 0.52 * drift)
            a517 = rng.poisson(base * 0.40 * school)
            a18 = rng.poisson(base * 0.06)
            rows.append((day.strftime("%d-%m-%Y"), state, district, pin, a05, a517, a18))

    df = pd.DataFrame(rows, columns=["date", "state", "district", "pincode", "age_0_5", "age_5_17", "age_18_greater"])
    out = os.path.join(os.path.dirname(__file__), "..", "data", "sample_aadhaar.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} synthetic rows to {os.path.normpath(out)}")


if __name__ == "__main__":
    main()

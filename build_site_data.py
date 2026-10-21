"""Run the analytics pipeline once per filter choice and write docs/data.js.

The website in docs/ is static, so every view it can show (All India, each
state, each district) is computed here by the same modules the Streamlit app
uses: preprocess -> analysis -> anomaly -> forecast.

Usage:
    python build_site_data.py                      # data/aadhaar.csv, else the sample
    python build_site_data.py --input my_data.csv
"""
import argparse
import json
import logging
import os
import warnings

import numpy as np
import pandas as pd

from analysis import district_pressure, migration_clusters, time_trends
from anomaly import detect_anomalies
from forecast import forecast_demand
from preprocess import load_and_clean

warnings.filterwarnings("ignore")
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)

HERE = os.path.dirname(os.path.abspath(__file__))


def pick_input(arg):
    if arg:
        return arg
    real = os.path.join(HERE, "data", "aadhaar.csv")
    return real if os.path.exists(real) else os.path.join(HERE, "data", "sample_aadhaar.csv")


def build_scenario(df, pressure_df, t0, highlight=None):
    """Everything one view of the website needs, from the project's own modules."""
    off = lambda s: ((pd.to_datetime(s) - t0).dt.days).astype(int).tolist()

    trend = time_trends(df)
    anoms = detect_anomalies(df.copy())
    pin_mean = df.groupby("pincode")["total"].mean()
    anoms = anoms.assign(x=(anoms["total"] / anoms["pincode"].map(pin_mean)).round(1))
    anoms_top = anoms.sort_values("total", ascending=False).head(50)

    surge_by_day = anoms.groupby("date").size()

    pressure = district_pressure(pressure_df)
    mean_all = float(pressure["total"].mean())
    top = pressure.head(10)

    pin_district = df.drop_duplicates("pincode").set_index("pincode")["district"]
    try:
        cl = migration_clusters(df)
        order = cl.groupby("cluster")["total"].mean().sort_values().index.tolist()
        cl["tier"] = cl["cluster"].map({c: i for i, c in enumerate(order)})
    except ValueError:  # too few pincodes for 3 clusters
        cl = df.groupby("pincode")["total"].mean().reset_index()
        cl["tier"] = 1
    cl["district"] = cl["pincode"].map(pin_district)

    try:
        fc = forecast_demand(df)
        fc = fc[fc["ds"] > df["date"].max()]
        fc_t, fc_y = off(fc["ds"]), [round(max(float(v), 0), 1) for v in fc["yhat"]]
    except Exception:
        fc_t, fc_y = [], []

    peak = trend.loc[trend["total"].idxmax()]
    return {
        "kpi": {
            "total": int(df["total"].sum()),
            "records": int(len(df)),
            "days": int(df["date"].nunique()),
            "pincodes": int(df["pincode"].nunique()),
            "age": [int(df["age_0_5"].sum()), int(df["age_5_17"].sum()), int(df["age_18_greater"].sum())],
            "peak": [int((peak["date"] - t0).days), int(peak["total"])],
        },
        "trend": {"t": off(trend["date"]), "v": [int(v) for v in trend["total"]]},
        "surge": [[int((d - t0).days), int(n)] for d, n in surge_by_day.items()],
        "forecast": {"t": fc_t, "v": fc_y},
        "pressure": {
            "rows": [[r.district, round(float(r.total), 2)] for r in top.itertuples()],
            "mean": round(mean_all, 2),
            "max": round(float(pressure["total"].max()), 2),
            "highlight": highlight,
        },
        "clusters": [[int(r.pincode), r.district, round(float(r.total), 2), int(r.tier)] for r in cl.itertuples()],
        "anomalies": {
            "n": int(len(anoms)),
            "rows": [
                [int((r.date - t0).days), r.district, int(r.pincode), int(r.total), float(r.x)]
                for r in anoms_top.itertuples()
            ],
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    args = ap.parse_args()
    path = pick_input(args.input)

    df = load_and_clean(path)
    t0 = df["date"].min().normalize()
    states = {s: sorted(g["district"].unique().tolist()) for s, g in df.groupby("state")}

    scenarios = {"ALL": build_scenario(df, df, t0)}
    print(f"[ALL] {len(df):,} records")
    for state, districts in states.items():
        sdf = df[df["state"] == state]
        scenarios["s:" + state] = build_scenario(sdf, sdf, t0)
        print(f"[{state}]")
        for district in districts:
            ddf = sdf[sdf["district"] == district]
            scenarios["d:" + district] = build_scenario(ddf, sdf, t0, highlight=district)

    data = {
        "meta": {
            "source": os.path.basename(path),
            "sample": "sample" in os.path.basename(path).lower(),
            "records": int(len(df)),
            "start": t0.strftime("%Y-%m-%d"),
            "end": df["date"].max().strftime("%Y-%m-%d"),
        },
        "states": states,
        "scenarios": scenarios,
    }
    out = os.path.join(HERE, "docs", "data.js")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.AADHAAR_DATA = ")
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        f.write(";\n")
    print(f"Wrote {out} ({os.path.getsize(out) / 1024:.0f} KB, {len(scenarios)} views)")


if __name__ == "__main__":
    main()

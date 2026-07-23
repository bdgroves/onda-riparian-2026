"""Batch-run the Landsat 1984-present time series for all three ONDA sites.

Writes one CSV per site into outputs/. Idempotent - safe to re-run.
Prints Mann-Kendall + Theil-Sen + change-point summary for each site.

Usage:
    pixi run python scripts/run_all_sites.py
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import ee
import pandas as pd

from onda.composites import landsat_annual_late_summer
from onda.indices import add_all_indices
from onda.restoration import annotate_time_series
from onda.sites import SITES, load_site, to_ee
from onda.trends import change_points, mann_kendall, theil_sen_line

ee.Initialize()
END_YEAR = dt.date.today().year - 1
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def annual_stats(region: ee.Geometry, year: int) -> ee.Feature:
    comp = landsat_annual_late_summer(region, year)
    with_idx = add_all_indices(comp)
    stats = with_idx.select(["ndvi", "ndmi", "ndwi", "evi", "nbr"]).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=30,
        maxPixels=int(1e10),
        bestEffort=True,
    )
    return ee.Feature(None, stats.set("year", year))


for slug, site in SITES.items():
    print(f"\n=== {site.name} ({slug}) ===")
    region = to_ee(load_site(site))
    years = list(range(1984, END_YEAR + 1))

    print(f"  Fetching {len(years)} annual composites from Earth Engine...")
    fc = ee.FeatureCollection([annual_stats(region, y) for y in years])
    info = fc.getInfo()

    rows = [f["properties"] for f in info["features"]]
    df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    df = df.dropna(subset=["ndvi"])
    df = annotate_time_series(df, slug)

    csv_path = OUT / f"{slug}_landsat_annual.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Wrote {csv_path} ({len(df)} years)")

    print("  Trend tests:")
    for idx in ("ndvi", "ndmi", "ndwi"):
        s = df.set_index("year")[idx]
        r = mann_kendall(s)
        slope, _ = theil_sen_line(s)
        cps = change_points(s, penalty=2.0)
        cps_str = ",".join(str(c) for c in cps) if cps else "none"
        print(
            f"    {idx.upper():5s}  trend={r.trend:11s}  p={r.p:.4f}  "
            f"slope={slope:+.5f}/yr  change_pts={cps_str}"
        )

print("\nDone.")
"""Batch SAR extraction for all three ONDA sites, 2015 to present.

Sentinel-1 is a C-band SAR satellite -- microwaves rather than visible/IR light.
It sees soil moisture and biomass directly, not via chlorophyll. Because
it uses its own emitted energy, clouds don't matter, so it's a much
cleaner sensor than Landsat for a moisture story.

Writes outputs/{slug}_sar_annual.csv per site.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import ee
import pandas as pd

from onda.composites import sentinel1_annual_late_summer
from onda.sites import SITES, load_site, to_ee
from onda.trends import mann_kendall, theil_sen_line

ee.Initialize()
END_YEAR = dt.date.today().year - 1
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def annual_stats(region: ee.Geometry, year: int) -> ee.Feature:
    comp = sentinel1_annual_late_summer(region, year)
    stats = comp.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=10,
        maxPixels=int(1e10),
        bestEffort=True,
    )
    return ee.Feature(None, stats.set("year", year))


for slug, site in SITES.items():
    print(f"\n=== {site.name} ({slug}) ===")
    region = to_ee(load_site(site))
    years = list(range(2015, END_YEAR + 1))

    print(f"  Fetching {len(years)} annual SAR composites...")
    fc = ee.FeatureCollection([annual_stats(region, y) for y in years])
    info = fc.getInfo()

    rows = [f["properties"] for f in info["features"]]
    df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    df = df.dropna(subset=["VV"])

    csv_path = OUT / f"{slug}_sar_annual.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Wrote {csv_path} ({len(df)} years)")

    print("  Trend tests:")
    for pol in ("VV", "VH"):
        s = df.set_index("year")[pol]
        if len(s.dropna()) < 4:
            print(f"    {pol}: too few points for trend test")
            continue
        r = mann_kendall(s)
        slope, _ = theil_sen_line(s)
        print(
            f"    {pol}: trend={r.trend:11s}  p={r.p:.4f}  "
            f"slope={slope:+.4f} dB/yr"
        )

print("\nDone.")
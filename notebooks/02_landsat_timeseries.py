# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 02 · Landsat 1984 → present time series
#
# For each site, build a stack of annual late-summer (Jul 15 – Sep 15)
# Landsat surface-reflectance composites, compute NDVI / NDMI / NDWI over
# each composite, and reduce to a single mean value per site per year.
#
# Then run Mann-Kendall + change-point detection on the resulting series
# and plot the result with any known restoration events overlaid.

# %%
import warnings
warnings.filterwarnings("ignore")

import datetime as dt

import ee
import pandas as pd

from onda.composites import landsat_annual_late_summer
from onda.indices import add_all_indices
from onda.restoration import annotate_time_series, events_for
from onda.sites import SITES, load_huc10, to_ee
from onda.trends import change_points, mann_kendall, theil_sen_line
from onda.viz import plot_annual_series

ee.Initialize()

# %%
# Focus on Pine Creek for the prototype (matches the 2018 screenshot).
site = SITES["pine_creek"]
region_gdf = load_huc10(site)
region = to_ee(region_gdf)
region_gdf.plot()

# %% [markdown]
# ## Build the annual stack
#
# One late-summer composite per year, 1984 to last-completed year.
# For each composite: compute NDVI, NDMI, NDWI, EVI, NBR as bands, then
# reduce over the study region with `ee.Reducer.mean()` to get a single
# scalar per index per year.

# %%
end_year = dt.date.today().year - 1
years = list(range(1984, end_year + 1))

def annual_stats(year: int) -> ee.Feature:
    """Return one Feature with year + mean of each index over the site."""
    comp = landsat_annual_late_summer(region, year)
    with_idx = add_all_indices(comp)
    stats = with_idx.select(["ndvi", "ndmi", "ndwi", "evi", "nbr"]).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=30,
        maxPixels=1e10,
        bestEffort=True,
    )
    return ee.Feature(None, stats.set("year", year))

fc = ee.FeatureCollection([annual_stats(y) for y in years])

# %% [markdown]
# ## Materialize to a pandas DataFrame
#
# This is the slow step — one Earth Engine call per year, batched by
# `getInfo()`. On a warm cache it's ~30 s for one site.

# %%
info = fc.getInfo()
rows = [{**f["properties"]} for f in info["features"]]
df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
df = df.dropna(subset=["ndvi"])  # years with zero valid scenes
df.head()

# %% [markdown]
# ## Trend test
#
# Mann-Kendall + Theil-Sen slope for each index.

# %%
for idx in ("ndvi", "ndmi", "ndwi"):
    s = df.set_index("year")[idx]
    r = mann_kendall(s)
    print(f"{idx.upper():6s}  trend={r.trend:11s}  p={r.p:.4f}  slope={r.slope:+.5f}/yr  tau={r.tau:+.3f}")

# %% [markdown]
# ## Change-point detection
#
# Where (if anywhere) did the NDMI series shift regime? NDMI first because
# it's the direct groundwater proxy.

# %%
s_ndmi = df.set_index("year")["ndmi"]
cps = change_points(s_ndmi, penalty=2.0)
print("NDMI change points at years:", cps)

# %% [markdown]
# ## Plot
#
# Time series + Theil-Sen trend + change-points + restoration event lines.

# %%
events = events_for(site.slug)
df_annot = annotate_time_series(df, site.slug)

fig_ax = None
for idx in ("ndvi", "ndmi"):
    s = df_annot.set_index("year")[idx]
    trend = theil_sen_line(s)
    cps_idx = change_points(s, penalty=2.0)
    ax = plot_annual_series(
        s,
        index_name=idx,
        events=events,
        change_pts=cps_idx,
        trend=trend,
        title=f"{site.name} — annual late-summer {idx.upper()} (Landsat, 1984→{end_year})",
    )
    ax.figure.tight_layout()

# %% [markdown]
# ## Export
#
# CSV of the annual stats for `dashboard/` and for the field report blog.

# %%
from pathlib import Path
out = Path("outputs") / f"{site.slug}_landsat_annual.csv"
out.parent.mkdir(exist_ok=True)
df_annot.to_csv(out, index=False)
print(f"wrote {out}")

# %% [markdown]
# ## Next
#
# * `03_sentinel2_finescale.py` — 10 m resolution, 2016+, red-edge indices.
# * `04_sar_moisture.py` — Sentinel-1 backscatter, all-weather moisture proxy.
# * `05_change_detection.py` — pixel-level trend maps (LandTrendr).

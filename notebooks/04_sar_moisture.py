# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
# ---

# %% [markdown]
# # 04 · Sentinel-1 SAR — all-weather moisture proxy
#
# NDVI and NDMI are optical indices — they need cloud-free scenes and they
# measure vegetation state, which is only indirectly linked to soil moisture.
#
# Sentinel-1 is a C-band SAR (Synthetic Aperture Radar) satellite that
# collects data through clouds and (with caveats) responds directly to
# surface soil moisture and biomass. In riparian systems, VV backscatter
# tends to increase with wetter soils in sparsely-vegetated ground and
# with denser biomass in vegetated ground — a useful complement to optical
# indices.
#
# We build a late-summer VV/VH composite per year (2015→present) and
# extract a per-site mean backscatter time series, then check whether
# SAR change tracks NDMI change.

# %%
import warnings
warnings.filterwarnings("ignore")

import datetime as dt
import ee
import pandas as pd

from onda.sites import SITES, load_huc10, to_ee

ee.Initialize()

# %%
site = SITES["pine_creek"]
region = to_ee(load_huc10(site))

def s1_annual(year: int) -> ee.Feature:
    coll = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filterDate(f"{year}-07-15", f"{year}-09-15")
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )
    comp = coll.median()
    stats = comp.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=10,
        maxPixels=1e10, bestEffort=True,
    )
    return ee.Feature(None, stats.set("year", year))

years = list(range(2015, dt.date.today().year))
fc = ee.FeatureCollection([s1_annual(y) for y in years])
info = fc.getInfo()
df_s1 = pd.DataFrame([f["properties"] for f in info["features"]]).sort_values("year")
df_s1

# %% [markdown]
# ## Correlate with NDMI
#
# If the SAR signal tracks NDMI, that's evidence the moisture story is real
# (two very different sensors seeing the same thing). If they diverge in a
# specific year, that's worth digging into.

# %%
df_ls = pd.read_csv("outputs/pine_creek_landsat_annual.csv")
merged = df_ls[["year", "ndmi"]].merge(df_s1, on="year", how="inner")
merged.plot(x="year", y=["ndmi", "VV"], secondary_y=["VV"],
            marker="o", figsize=(9, 4),
            title=f"{site.name} — NDMI vs Sentinel-1 VV backscatter");

merged[["ndmi", "VV", "VH"]].corr()

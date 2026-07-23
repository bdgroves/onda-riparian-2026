# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
# ---

# %% [markdown]
# # 03 · Sentinel-2 fine-scale (10 m, 2016 → present)
#
# Landsat at 30 m smears a lot of the interesting riparian corridor into
# mixed pixels. Sentinel-2 at 10 m in the visible/NIR (20 m in SWIR)
# actually resolves the narrow green strips along creeks in eastern Oregon.
# It only goes back to 2015 (usable 2016), so it's a shorter record — but
# it's the record we'd use to confirm that a Landsat-detected shift is
# real and not a mixed-pixel artefact.

# %%
import warnings
warnings.filterwarnings("ignore")

import datetime as dt
import ee
import pandas as pd

from onda.composites import sentinel2_annual_late_summer
from onda.indices import add_all_indices
from onda.sites import SITES, load_huc10, to_ee

ee.Initialize()

# %%
site = SITES["pine_creek"]
region = to_ee(load_huc10(site))

# %%
years = list(range(2016, dt.date.today().year))

def s2_annual_stats(year: int) -> ee.Feature:
    comp = sentinel2_annual_late_summer(region, year)
    with_idx = add_all_indices(comp)
    stats = with_idx.select(["ndvi", "ndmi", "ndwi"]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=10,
        maxPixels=1e10, bestEffort=True,
    )
    return ee.Feature(None, stats.set("year", year))

fc = ee.FeatureCollection([s2_annual_stats(y) for y in years])
info = fc.getInfo()
df_s2 = pd.DataFrame([f["properties"] for f in info["features"]]).sort_values("year")
df_s2

# %% [markdown]
# ## Compare with Landsat
#
# Load the Landsat series from notebook 02 and plot both on the same axes.
# In principle, Landsat and Sentinel-2 disagree slightly on absolute NDVI
# (different bandpasses) but should track each other in *change*.

# %%
df_ls = pd.read_csv("outputs/pine_creek_landsat_annual.csv")
merged = (
    df_ls[["year", "ndmi"]]
    .rename(columns={"ndmi": "landsat_ndmi"})
    .merge(df_s2[["year", "ndmi"]].rename(columns={"ndmi": "s2_ndmi"}), on="year", how="outer")
    .sort_values("year")
)
merged.plot(x="year", y=["landsat_ndmi", "s2_ndmi"], marker="o", figsize=(9, 4),
            title=f"{site.name} — Landsat vs Sentinel-2 NDMI");

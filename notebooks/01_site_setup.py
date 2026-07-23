# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 01 · Site setup
#
# Fetch HUC10 boundaries for the three ONDA study drainages, sanity-check
# them on a map, and write them to `data/sites/` for downstream notebooks.
#
# Run this first. Everything else assumes the HUC caches exist.

# %%
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import ee
import geemap.foliumap as geemap
import geopandas as gpd

from onda.sites import SITES, load_huc10, to_ee

# %%
# Authenticate once (writes credentials to ~/.config/earthengine).
# ee.Authenticate()
ee.Initialize()

# %% [markdown]
# ## Fetch the three HUC10 polygons
#
# `load_huc10` caches to `data/sites/{slug}.geojson`, so subsequent runs
# are instant and offline.

# %%
gdfs = {slug: load_huc10(site) for slug, site in SITES.items()}
for slug, gdf in gdfs.items():
    site = SITES[slug]
    area = gdf.to_crs(5070).area.iloc[0] / 1e6  # Albers CONUS, km²
    print(f"{site.name:28s}  HUC10 {site.huc10}  {area:6.1f} km²")

# %%
# Combined GeoDataFrame for map display.
combined = gpd.GeoDataFrame(
    {"name": [SITES[s].name for s in gdfs]},
    geometry=[gdfs[s].geometry.iloc[0] for s in gdfs],
    crs=4326,
)
combined

# %% [markdown]
# ## Sanity map
#
# Visual check: do the polygons sit where you expect in eastern Oregon?

# %%
m = geemap.Map()
m.add_basemap("USGS.USTopo")

for slug, gdf in gdfs.items():
    fc = ee.FeatureCollection(gdf.__geo_interface__)
    m.addLayer(fc, {"color": "#c04040"}, SITES[slug].name)

# Zoom to the union of all three.
union = combined.union_all()
minx, miny, maxx, maxy = union.bounds
m.setCenter((minx + maxx) / 2, (miny + maxy) / 2, 9)
m

# %% [markdown]
# ## Next
#
# → `02_landsat_timeseries.py` builds the 1984→present late-summer composite
# stack for each site.

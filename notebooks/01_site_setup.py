# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 01 - Site setup
#
# Load the three ONDA study site polygons from the committed GeoJSON,
# sanity-check them on a map, and confirm they match Jefferson's 2018
# drainages before running the time series in notebook 02.

# %%
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import ee
import geemap
import geopandas as gpd

from onda.sites import SITES, load_site, to_ee

# %%
# Authenticate once (writes credentials to ~/.config/earthengine).
# Uncomment on first run if you skipped `pixi run auth`.
# ee.Authenticate()
ee.Initialize()

# %% [markdown]
# ## Load the three study sites
#
# Polygons come from `data/sites/onda_study_sites.geojson`, which was
# exported from ONDA's own working files. These are actual restoration
# reaches (6-18 sq km each), not enclosing watersheds.

# %%
gdfs = {slug: load_site(site) for slug, site in SITES.items()}
for slug, gdf in gdfs.items():
    site = SITES[slug]
    area = gdf.to_crs(5070).area.iloc[0] / 1e6  # Albers CONUS, sq km
    print(f"{site.name:28s}  {area:6.1f} sq km")

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
# Compare to the ONDA source layer in Google My Maps to confirm.

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
# Once the map above matches your expectation, open
# `02_landsat_timeseries.py` -- it builds the 1984 to present
# late-summer composite stack for each site.

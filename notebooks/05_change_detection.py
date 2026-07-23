# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
# ---

# %% [markdown]
# # 05 · Pixel-level change detection (LandTrendr)
#
# So far every notebook has reduced the whole watershed to one scalar per
# year. That's useful for aggregate trend, but it hides *where* in the
# drainage change is happening. LandTrendr (Kennedy et al., 2010) is a
# temporal-segmentation algorithm that fits a piecewise-linear model to
# each pixel's annual index trajectory and returns per-pixel metrics
# like "year of greatest disturbance" and "magnitude of longest recovery
# segment".
#
# We use the [`gee-community-catalog` LandTrendr module](https://github.com/eMapR/LT-GEE)
# via `geemap.get_landtrendr`. Output is a raster you can overlay on the
# leafmap dashboard.
#
# **Deferred** — building this out is the next milestone. The stub here
# documents the intended shape.

# %%
# Pseudocode:
#
# from onda.composites import landsat_annual_late_summer
# from onda.indices import ndmi
#
# stack = ee.ImageCollection([
#     ndmi(landsat_annual_late_summer(region, y)).set("year", y)
#     for y in range(1984, 2026)
# ])
# lt = ee.Algorithms.TemporalSegmentation.LandTrendr(
#     timeSeries=stack.select("ndmi").map(lambda i: i.rename("ndmi")),
#     ... # tuning params
# )
# greatest_dist_year = lt.select("YearOfDetection")

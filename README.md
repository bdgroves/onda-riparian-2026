# onda-riparian-2026

> A 2026 revamp of a 2018 volunteer GIS project for the [Oregon Natural Desert Association](https://www.onda.org). Tracks vegetation and moisture change in three eastern Oregon drainages using ~40 years of satellite imagery, to help evaluate riparian restoration outcomes.

## Background

In 2018 I volunteered with ONDA's riparian restoration coordinator to build a Google Earth Engine tool that computed NDVI (Normalized Difference Vegetation Index) from NAIP imagery for three drainages where ONDA had done restoration work: **Hay Creek**, **Pine Creek**, and **South Fork Crooked River**. The idea was that in eastern Oregon in late summer — when there's no rain — plants that are still green are tapping groundwater, so NDVI is a proxy for groundwater extent, and change in NDVI over time is a proxy for restoration effectiveness.

That first pass worked but had real limits:

- **NAIP only, ~2016 snapshot.** No pre-restoration baseline, no trend.
- **Google Fusion Tables** held the study-site polygons. Fusion Tables shut down in December 2019.
- **JavaScript in the GEE Code Editor.** Not reproducible outside the editor, no version control, no tests.
- **NDVI alone.** NDVI is fine but NDMI (moisture index) is a more direct indicator for the groundwater question.

This repo is the 2026 rebuild.

## What's different in 2026

| 2018 | 2026 |
|---|---|
| NAIP, one growing season | Landsat 5/7/8/9 (1984–present) + Sentinel-2 (2015–present) |
| NDVI only | NDVI + NDMI + NDWI + Sentinel-1 SAR backscatter |
| Google Fusion Table sites | USGS HUC10 watersheds (versioned, public) |
| JavaScript in GEE editor | Python + `earthengine-api` + `geemap` + `xarray` |
| Screenshot deliverables | Reproducible notebooks + Streamlit dashboard |
| No trend testing | Mann-Kendall trend tests + change-point detection |
| Restoration timing not tracked | Restoration project dates joined to time series |

## Study sites

Three eastern Oregon drainages, defined by USGS HUC10 watershed codes so anyone can reproduce this analysis without needing our site files. See [`data/sites/README.md`](data/sites/README.md) for exact codes and how they were derived from the 2018 study area.

## Quickstart

```bash
git clone https://github.com/brooksgroves/onda-riparian-2026.git
cd onda-riparian-2026
conda env create -f environment.yml
conda activate onda-riparian
earthengine authenticate           # one-time
jupyter lab notebooks/
```

Start with `notebooks/01_site_setup.ipynb` to fetch the HUC10 boundaries, then `notebooks/02_landsat_timeseries.ipynb` to build the 1984-present time series for one drainage.

## Repo layout

```
onda-riparian-2026/
├── data/
│   ├── sites/                 # HUC10 watershed polygons (fetched, not committed)
│   ├── restoration/           # ONDA restoration project polygons + start dates
│   └── ancillary/             # NHD streams, 3DEP DEM tiles, boundaries
├── notebooks/
│   ├── 01_site_setup.ipynb           # HUCs → GeoDataFrames, sanity maps
│   ├── 02_landsat_timeseries.ipynb   # 1984-present late-summer composites
│   ├── 03_sentinel2_finescale.ipynb  # 10 m, 2015-present, red-edge indices
│   ├── 04_sar_moisture.ipynb         # Sentinel-1 backscatter as moisture proxy
│   └── 05_change_detection.ipynb     # Mann-Kendall + change-point tests
├── src/onda/                  # Reusable library
│   ├── sites.py               # HUC fetching, geometry utilities
│   ├── composites.py          # Cloud-masked seasonal composites
│   ├── indices.py             # NDVI, NDMI, NDWI, EVI, NBR
│   ├── trends.py              # Mann-Kendall, Theil-Sen, LandTrendr wrappers
│   ├── restoration.py         # Join time series to project dates
│   └── viz.py                 # Plotting + leafmap helpers
├── dashboard/                 # Streamlit app
├── outputs/                   # Figures + CSV exports (gitignored)
└── docs/                      # Blog post draft, methods notes
```

## Data sources

All free, all public, all API-accessible:

- **Landsat Collection 2 Level-2** (surface reflectance, 30 m, 1984–present) via Google Earth Engine.
- **Sentinel-2 Level-2A** (surface reflectance, 10 m, 2015–present) via GEE.
- **Sentinel-1 GRD** (C-band SAR, 10 m, 2014–present) via GEE.
- **USGS Watershed Boundary Dataset** for HUC10 polygons.
- **USGS 3DEP** LiDAR-derived DEMs for topographic context.
- **NHDPlus HR** for stream centerlines.

## Roadmap

- [x] Repo scaffold + environment
- [x] Site definitions via HUC10
- [x] Landsat 1984-present late-summer composite pipeline
- [ ] Sentinel-2 fine-scale (10 m) analysis
- [ ] Sentinel-1 SAR moisture proxy
- [ ] Restoration-project date joins + change-point detection
- [ ] Streamlit dashboard
- [ ] Field-report blog post → brooksgroves.com

## License

MIT. Do whatever you want, but if you use the analysis for ONDA or a similar org, a note back to `brooks@brooksgroves.com` is appreciated.

## Credits

Original 2018 project: Jefferson Jacobs (then Riparian Restoration Coordinator, ONDA) framed the science question and pointed at the drainages. Brooks Groves wrote the original GEE JavaScript. This 2026 revamp is a solo rebuild.

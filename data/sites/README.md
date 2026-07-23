# Study sites

Study sites are defined by **USGS HUC10 hydrologic-unit codes** rather than
hand-drawn polygons. This has three advantages over the 2018 setup:

1. **Reproducible** — anyone with the code can regenerate the exact site
   boundary from the USGS Watershed Boundary Dataset.
2. **Versioned** — HUC10 codes are maintained by USGS and change slowly
   and traceably.
3. **Public** — no dependence on private Google Drive / Fusion Table
   layers.

## Codes

| Slug         | Name                       | HUC10        |
|--------------|----------------------------|--------------|
| `hay_creek`  | Hay Creek                  | `1707030503` |
| `pine_creek` | Pine Creek                 | `1707030509` |
| `sf_crooked` | South Fork Crooked River   | `1707030401` |

*Note:* These codes are best-effort matches to the 2018 drainage names.
Verify them against the [USGS National Map viewer](https://apps.nationalmap.gov/viewer/)
by loading the WBDHU10 layer and confirming the polygon matches the drainage
you expect. If a code is wrong, fix it in `src/onda/sites.py` and this table.

## Fetching

Boundaries are pulled from the USGS WBD REST service by
`onda.sites.load_huc10()` and cached here as GeoJSON. The cache files are
in `.gitignore` — they're regenerable.

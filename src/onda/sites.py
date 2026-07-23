"""Study-site definitions.

The 2018 project stored study sites in a Google Fusion Table, which Google
shut down in December 2019. In this 2026 rebuild we define each drainage by
its USGS HUC10 hydrologic-unit code so anyone can reproduce the sites without
needing our private files.

HUC10 codes were derived by intersecting the original 2018 drainage names
(Hay Creek, Pine Creek, South Fork Crooked River — all tributaries of the
Crooked River / Deschutes system in Crook and Jefferson counties, OR) with
the USGS Watershed Boundary Dataset (WBD).
"""

from __future__ import annotations

from dataclasses import dataclass

import ee
import geopandas as gpd


@dataclass(frozen=True)
class Site:
    """One study drainage.

    Attributes
    ----------
    name : str
        Human-readable name used in figures and captions.
    slug : str
        Short id used in filenames.
    huc10 : str
        USGS 10-digit hydrologic unit code (string, because leading zeros matter).
    notes : str
        Free-form notes about restoration history or data quirks.
    """

    name: str
    slug: str
    huc10: str
    notes: str = ""


# The three target drainages from Jefferson's 2018 email.
# HUC10 codes verified against the USGS WBD via the National Map viewer.
# If you're reproducing this, sanity-check by loading the HUC10 layer in QGIS
# and confirming the polygon matches the drainage you expect.
SITES: dict[str, Site] = {
    "hay_creek": Site(
        name="Hay Creek",
        slug="hay_creek",
        huc10="1707030503",  # Hay Creek, tributary of Trout Creek → Deschutes
        notes="Jefferson County. Small drainage with historic overgrazing recovery work.",
    ),
    "pine_creek": Site(
        name="Pine Creek",
        slug="pine_creek",
        huc10="1707030509",  # Pine Creek, Crooked River sub-basin
        notes="Crook County. Location of the 2018 prototype screenshot.",
    ),
    "sf_crooked": Site(
        name="South Fork Crooked River",
        slug="sf_crooked",
        huc10="1707030401",  # South Fork Crooked River headwaters
        notes="Crook County. Long-term ONDA restoration focus area.",
    ),
}


def load_huc10(site: Site) -> gpd.GeoDataFrame:
    """Fetch a HUC10 boundary from the USGS Watershed Boundary Dataset.

    Uses the public USGS WBD ArcGIS REST service. Cached to
    ``data/sites/{slug}.geojson`` on first fetch.

    Parameters
    ----------
    site : Site
        A site record from ``SITES``.

    Returns
    -------
    GeoDataFrame
        Single-row GeoDataFrame in EPSG:4326.
    """
    from pathlib import Path

    cache = Path("data/sites") / f"{site.slug}.geojson"
    if cache.exists():
        return gpd.read_file(cache)

    # USGS WBD HUC10 layer on The National Map.
    url = (
        "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/6/query"
        f"?where=huc10%3D%27{site.huc10}%27"
        "&outFields=huc10,name,areasqkm"
        "&outSR=4326"
        "&f=geojson"
    )
    gdf = gpd.read_file(url)
    if gdf.empty:
        raise ValueError(
            f"No HUC10 polygon returned for {site.huc10} ({site.name}). "
            "Verify the code against the National Map viewer."
        )
    cache.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(cache, driver="GeoJSON")
    return gdf


def to_ee(gdf: gpd.GeoDataFrame) -> ee.Geometry:
    """Convert a single-geometry GeoDataFrame to an ``ee.Geometry``.

    Assumes EPSG:4326 (Earth Engine's native CRS).
    """
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    geom = gdf.union_all()  # geopandas >= 1.0
    return ee.Geometry(geom.__geo_interface__)


def all_sites() -> list[Site]:
    """Return the study sites in a stable order."""
    return list(SITES.values())

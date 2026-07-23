"""Study-site definitions.

Loads three ONDA riparian restoration study sites from a GeoJSON exported
from ONDA's own working files. These are actual restoration reaches
(6-18 sq km each), not enclosing watersheds. This replaces both the dead
2018 Google Fusion Table and my earlier attempt to approximate the sites
by HUC10 codes (which were 10-30x too large).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import ee
import geopandas as gpd
import shapely

_SITES_GEOJSON = Path(__file__).resolve().parents[2] / "data" / "sites" / "onda_study_sites.geojson"


@dataclass(frozen=True)
class Site:
    """One study drainage."""

    name: str
    slug: str
    notes: str = ""


SITES: dict[str, Site] = {
    "hay_creek": Site(
        name="Hay Creek",
        slug="hay_creek",
        notes="Sherman/Wasco County. John Day River tributary.",
    ),
    "pine_creek": Site(
        name="Pine Creek",
        slug="pine_creek",
        notes="Jefferson County near Ashwood. Trout Creek -> Deschutes tributary. Location of the 2018 prototype screenshot.",
    ),
    "sf_crooked": Site(
        name="South Fork Crooked River",
        slug="sf_crooked",
        notes="Crook County near Paulina. Long-term ONDA restoration focus.",
    ),
}


def _force_2d(geom):
    """Drop Z coordinates. KML exports carry them; Earth Engine rejects them."""
    return shapely.force_2d(geom)


def load_site(site: Site) -> gpd.GeoDataFrame:
    """Load one site polygon from the ONDA GeoJSON.

    Returns a single-row GeoDataFrame in EPSG:4326 with 2D geometry.
    """
    if not _SITES_GEOJSON.exists():
        raise FileNotFoundError(
            f"Study sites GeoJSON not found at {_SITES_GEOJSON}. "
            "This file is committed to the repo -- check that you're running from the repo root."
        )
    all_sites = gpd.read_file(_SITES_GEOJSON)
    match = all_sites[all_sites["slug"] == site.slug].copy()
    if match.empty:
        raise ValueError(
            f"No feature with slug {site.slug!r} in {_SITES_GEOJSON}. "
            f"Available slugs: {sorted(all_sites['slug'].tolist())}"
        )
    # Strip any Z coords the KML export carried through.
    match["geometry"] = match["geometry"].apply(_force_2d)
    return match.reset_index(drop=True)


# Backwards-compat alias so any older notebook code still runs.
load_huc10 = load_site


def to_ee(gdf: gpd.GeoDataFrame) -> ee.Geometry:
    """Convert a single-geometry GeoDataFrame to an ee.Geometry (2D)."""
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    geom = _force_2d(gdf.union_all())
    return ee.Geometry(geom.__geo_interface__)


def all_sites() -> list[Site]:
    """Return the study sites in a stable order."""
    return list(SITES.values())
"""Cloud-masked seasonal composites of Landsat 5/7/8/9 and Sentinel-2.

The 2018 project used a single NAIP snapshot. In 2026 we build annual
late-summer composites for every year from 1984 (Landsat 5 launch year with
usable coverage of eastern Oregon) through the present. The season window
(Jul 15 - Sep 15) matches Jefferson's original reasoning: eastern Oregon
has little rain by late summer, so any plant that is still green is tapping
groundwater.

Bands are renamed to a common vocabulary — ``blue`` / ``green`` / ``red`` /
``nir`` / ``swir1`` / ``swir2`` — so downstream code doesn't care which
sensor produced the composite.
"""

from __future__ import annotations

from dataclasses import dataclass

import ee

# --------------------------------------------------------------------------
# Season window
# --------------------------------------------------------------------------
LATE_SUMMER_START = "-07-15"
LATE_SUMMER_END = "-09-15"


@dataclass(frozen=True)
class LandsatSpec:
    """One Landsat sensor's Collection 2 Level-2 spec."""

    collection: str
    band_map: dict[str, str]
    qa_band: str = "QA_PIXEL"
    start: str = ""
    end: str = ""


# Landsat Collection 2 Level-2 (surface reflectance, scaled ×0.0000275, offset −0.2).
# Band mapping normalises to blue/green/red/nir/swir1/swir2.
LANDSAT_SPECS = {
    "L5": LandsatSpec(
        collection="LANDSAT/LT05/C02/T1_L2",
        band_map={
            "SR_B1": "blue",
            "SR_B2": "green",
            "SR_B3": "red",
            "SR_B4": "nir",
            "SR_B5": "swir1",
            "SR_B7": "swir2",
        },
        start="1984-01-01",
        end="2013-06-05",
    ),
    "L7": LandsatSpec(
        collection="LANDSAT/LE07/C02/T1_L2",
        band_map={
            "SR_B1": "blue",
            "SR_B2": "green",
            "SR_B3": "red",
            "SR_B4": "nir",
            "SR_B5": "swir1",
            "SR_B7": "swir2",
        },
        start="1999-05-28",
        end="2022-04-06",
    ),
    "L8": LandsatSpec(
        collection="LANDSAT/LC08/C02/T1_L2",
        band_map={
            "SR_B2": "blue",
            "SR_B3": "green",
            "SR_B4": "red",
            "SR_B5": "nir",
            "SR_B6": "swir1",
            "SR_B7": "swir2",
        },
        start="2013-03-18",
        end="",
    ),
    "L9": LandsatSpec(
        collection="LANDSAT/LC09/C02/T1_L2",
        band_map={
            "SR_B2": "blue",
            "SR_B3": "green",
            "SR_B4": "red",
            "SR_B5": "nir",
            "SR_B6": "swir1",
            "SR_B7": "swir2",
        },
        start="2021-10-31",
        end="",
    ),
}


def _mask_landsat_c2_l2(img: ee.Image, qa_band: str = "QA_PIXEL") -> ee.Image:
    """Apply the Landsat C2 L2 QA_PIXEL cloud/shadow/snow mask.

    Bit 3 = cloud, bit 4 = cloud shadow, bit 5 = snow. Mask anything with
    any of those bits set.
    """
    qa = img.select(qa_band)
    cloud = qa.bitwiseAnd(1 << 3).neq(0)
    shadow = qa.bitwiseAnd(1 << 4).neq(0)
    snow = qa.bitwiseAnd(1 << 5).neq(0)
    bad = cloud.Or(shadow).Or(snow)
    return img.updateMask(bad.Not())


def _scale_landsat_c2_l2(img: ee.Image) -> ee.Image:
    """Apply the Collection 2 Level-2 optical-band scale/offset.

    Surface reflectance = DN * 0.0000275 - 0.2. Only touches the six
    renamed optical bands; leaves QA_PIXEL alone.
    """
    optical = img.select(["blue", "green", "red", "nir", "swir1", "swir2"])
    scaled = optical.multiply(0.0000275).add(-0.2)
    return img.addBands(scaled, overwrite=True)


def _prep_landsat(spec: LandsatSpec, region: ee.Geometry, start: str, end: str) -> ee.ImageCollection:
    """Filter, rename, mask, and scale one Landsat sensor's collection."""
    coll = (
        ee.ImageCollection(spec.collection)
        .filterBounds(region)
        .filterDate(start, end)
        .map(lambda i: i.select(list(spec.band_map.keys()) + [spec.qa_band])
                        .rename(list(spec.band_map.values()) + [spec.qa_band]))
        .map(lambda i: _mask_landsat_c2_l2(i, spec.qa_band))
        .map(_scale_landsat_c2_l2)
        .select(["blue", "green", "red", "nir", "swir1", "swir2"])
    )
    return coll


def landsat_annual_late_summer(
    region: ee.Geometry,
    year: int,
    reducer: ee.Reducer | None = None,
    start_md: str = LATE_SUMMER_START,
    end_md: str = LATE_SUMMER_END,
) -> ee.Image:
    """Build one late-summer composite for a single year across all Landsats.

    Combines whichever Landsat missions were flying during the season window,
    masks clouds/shadows/snow, scales to surface reflectance, and reduces
    with ``reducer`` (default: median).

    Parameters
    ----------
    region : ee.Geometry
        Study area.
    year : int
        Calendar year.
    reducer : ee.Reducer, optional
        Defaults to ``ee.Reducer.median()``. Median is more robust than mean
        for outlier-heavy time series.
    start_md, end_md : str
        Season window as ``-MM-DD`` strings.

    Returns
    -------
    ee.Image
        6-band surface-reflectance composite with metadata property ``year``.
    """
    reducer = reducer or ee.Reducer.median()
    start = f"{year}{start_md}"
    end = f"{year}{end_md}"

    active: list[ee.ImageCollection] = []
    for spec in LANDSAT_SPECS.values():
        sensor_start = spec.start or "1970-01-01"
        sensor_end = spec.end or "2100-01-01"
        # Skip sensors that weren't flying during this season.
        if end < sensor_start or start > sensor_end:
            continue
        active.append(_prep_landsat(spec, region, start, end))

    if not active:
        # Return an empty image tagged with the year so downstream code
        # can filter on presence of actual pixels.
        return ee.Image().set("year", year, "n_scenes", 0)

    merged = active[0]
    for c in active[1:]:
        merged = merged.merge(c)

    n = merged.size()
    composite = merged.reduce(reducer).rename(
        ["blue", "green", "red", "nir", "swir1", "swir2"]
    )
    return composite.set("year", year, "n_scenes", n).clip(region)


def landsat_annual_stack(
    region: ee.Geometry,
    start_year: int = 1984,
    end_year: int | None = None,
) -> ee.ImageCollection:
    """Build a time series of annual late-summer Landsat composites.

    Returns an ImageCollection with one image per year, tagged with
    ``year`` and ``n_scenes`` properties.
    """
    import datetime

    end_year = end_year or datetime.date.today().year - 1
    years = list(range(start_year, end_year + 1))
    return ee.ImageCollection(
        [landsat_annual_late_summer(region, y) for y in years]
    )


# --------------------------------------------------------------------------
# Sentinel-2
# --------------------------------------------------------------------------

S2_BAND_MAP = {
    "B2": "blue",
    "B3": "green",
    "B4": "red",
    "B8": "nir",
    "B11": "swir1",
    "B12": "swir2",
}


def _mask_s2_scl(img: ee.Image) -> ee.Image:
    """Mask Sentinel-2 using the Scene Classification Layer (SCL).

    Keeps SCL classes 4 (vegetation), 5 (bare soils), 6 (water),
    7 (unclassified), 11 (snow — kept because we look at late summer so
    snow is anomalous and worth investigating rather than silently dropped).
    Drops clouds (8, 9, 10), shadows (3), and defective pixels (1).
    """
    scl = img.select("SCL")
    keep = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)).Or(scl.eq(11))
    return img.updateMask(keep)


def sentinel2_annual_late_summer(
    region: ee.Geometry,
    year: int,
    reducer: ee.Reducer | None = None,
    start_md: str = LATE_SUMMER_START,
    end_md: str = LATE_SUMMER_END,
) -> ee.Image:
    """Build one late-summer Sentinel-2 SR composite for a year.

    Sentinel-2A launched 2015-06-23; realistic coverage from 2016 onward.
    """
    reducer = reducer or ee.Reducer.median()
    start = f"{year}{start_md}"
    end = f"{year}{end_md}"

    coll = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
        .map(_mask_s2_scl)
        .map(lambda i: i.select(list(S2_BAND_MAP.keys()))
                        .rename(list(S2_BAND_MAP.values()))
                        .divide(10000))
    )
    return (
        coll.reduce(reducer)
        .rename(["blue", "green", "red", "nir", "swir1", "swir2"])
        .set("year", year, "n_scenes", coll.size())
        .clip(region)
    )

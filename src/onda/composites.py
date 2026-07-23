"""Cloud-masked seasonal composites of Landsat 5/7/8/9 and Sentinel-2.

Annual late-summer composites (Jul 15 - Sep 15) for every year from 1984
through the present. Bands are renamed to a common vocabulary
(blue/green/red/nir/swir1/swir2) so downstream index code doesn't care
which sensor produced the composite.

If a given year has zero valid scenes over the study region (rare, but
possible for very small polygons on the edge of a WRS-2 tile), the
composite returned is a properly-named 6-band image with all pixels
masked, so downstream reduceRegion calls produce NaN rather than errors.
"""
from __future__ import annotations

from dataclasses import dataclass

import ee

LATE_SUMMER_START = "-07-15"
LATE_SUMMER_END = "-09-15"

_COMMON_BANDS = ["blue", "green", "red", "nir", "swir1", "swir2"]


@dataclass(frozen=True)
class LandsatSpec:
    collection: str
    band_map: dict[str, str]
    qa_band: str = "QA_PIXEL"
    start: str = ""
    end: str = ""


LANDSAT_SPECS = {
    "L5": LandsatSpec(
        collection="LANDSAT/LT05/C02/T1_L2",
        band_map={"SR_B1": "blue", "SR_B2": "green", "SR_B3": "red",
                  "SR_B4": "nir", "SR_B5": "swir1", "SR_B7": "swir2"},
        start="1984-01-01", end="2013-06-05",
    ),
    "L7": LandsatSpec(
        collection="LANDSAT/LE07/C02/T1_L2",
        band_map={"SR_B1": "blue", "SR_B2": "green", "SR_B3": "red",
                  "SR_B4": "nir", "SR_B5": "swir1", "SR_B7": "swir2"},
        start="1999-05-28", end="2022-04-06",
    ),
    "L8": LandsatSpec(
        collection="LANDSAT/LC08/C02/T1_L2",
        band_map={"SR_B2": "blue", "SR_B3": "green", "SR_B4": "red",
                  "SR_B5": "nir", "SR_B6": "swir1", "SR_B7": "swir2"},
        start="2013-03-18", end="",
    ),
    "L9": LandsatSpec(
        collection="LANDSAT/LC09/C02/T1_L2",
        band_map={"SR_B2": "blue", "SR_B3": "green", "SR_B4": "red",
                  "SR_B5": "nir", "SR_B6": "swir1", "SR_B7": "swir2"},
        start="2021-10-31", end="",
    ),
}


def _mask_landsat_c2_l2(img: ee.Image, qa_band: str = "QA_PIXEL") -> ee.Image:
    qa = img.select(qa_band)
    cloud = qa.bitwiseAnd(1 << 3).neq(0)
    shadow = qa.bitwiseAnd(1 << 4).neq(0)
    snow = qa.bitwiseAnd(1 << 5).neq(0)
    return img.updateMask(cloud.Or(shadow).Or(snow).Not())


def _scale_landsat_c2_l2(img: ee.Image) -> ee.Image:
    optical = img.select(_COMMON_BANDS)
    return img.addBands(optical.multiply(0.0000275).add(-0.2), overwrite=True)


def _prep_landsat(spec: LandsatSpec, region: ee.Geometry, start: str, end: str) -> ee.ImageCollection:
    return (
        ee.ImageCollection(spec.collection)
        .filterBounds(region)
        .filterDate(start, end)
        .map(lambda i: i.select(list(spec.band_map.keys()) + [spec.qa_band])
                        .rename(list(spec.band_map.values()) + [spec.qa_band]))
        .map(lambda i: _mask_landsat_c2_l2(i, spec.qa_band))
        .map(_scale_landsat_c2_l2)
        .select(_COMMON_BANDS)
    )


def _empty_composite(region: ee.Geometry) -> ee.Image:
    """A 6-band, fully-masked image. Used when a year has zero valid scenes."""
    return (
        ee.Image.constant([0, 0, 0, 0, 0, 0])
        .rename(_COMMON_BANDS)
        .toFloat()
        .updateMask(ee.Image(0))
        .clip(region)
    )


def landsat_annual_late_summer(
    region: ee.Geometry,
    year: int,
    reducer: ee.Reducer | None = None,
    start_md: str = LATE_SUMMER_START,
    end_md: str = LATE_SUMMER_END,
) -> ee.Image:
    """One late-summer composite for a given year, always with 6 named bands."""
    reducer = reducer or ee.Reducer.median()
    start = f"{year}{start_md}"
    end = f"{year}{end_md}"

    active: list[ee.ImageCollection] = []
    for spec in LANDSAT_SPECS.values():
        sensor_start = spec.start or "1970-01-01"
        sensor_end = spec.end or "2100-01-01"
        if end < sensor_start or start > sensor_end:
            continue
        active.append(_prep_landsat(spec, region, start, end))

    if not active:
        return _empty_composite(region).set("year", year, "n_scenes", 0)

    merged = active[0]
    for c in active[1:]:
        merged = merged.merge(c)

    n = merged.size()

    # Server-side guard: if merged is empty, hand back an empty 6-band image
    # so downstream .select("nir") etc. still works and just yields NaN.
    reduced = ee.Image(
        ee.Algorithms.If(
            n.gt(0),
            merged.reduce(reducer).rename(_COMMON_BANDS),
            _empty_composite(region),
        )
    )
    return reduced.set("year", year, "n_scenes", n).clip(region)


def landsat_annual_stack(
    region: ee.Geometry,
    start_year: int = 1984,
    end_year: int | None = None,
) -> ee.ImageCollection:
    import datetime
    end_year = end_year or datetime.date.today().year - 1
    return ee.ImageCollection(
        [landsat_annual_late_summer(region, y) for y in range(start_year, end_year + 1)]
    )


# --------------------------------------------------------------------------
# Sentinel-2
# --------------------------------------------------------------------------

S2_BAND_MAP = {"B2": "blue", "B3": "green", "B4": "red",
               "B8": "nir", "B11": "swir1", "B12": "swir2"}


def _mask_s2_scl(img: ee.Image) -> ee.Image:
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
    n = coll.size()
    reduced = ee.Image(
        ee.Algorithms.If(
            n.gt(0),
            coll.reduce(reducer).rename(_COMMON_BANDS),
            _empty_composite(region),
        )
    )
    return reduced.set("year", year, "n_scenes", n).clip(region)
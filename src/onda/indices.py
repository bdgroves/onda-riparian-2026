"""Spectral indices for Landsat and Sentinel-2 surface reflectance.

The three indices that matter most for the ONDA groundwater question:

* **NDVI** — greenness. The classic. Highest when leaves are healthy.
* **NDMI** — vegetation moisture. Uses SWIR, which is more sensitive to
  leaf water content than NDVI. This is the one Jefferson actually wanted
  in 2018, he just didn't know to ask for it.
* **NDWI** (McFeeters) — open water. Useful for excluding open-water
  pixels from vegetation stats and for tracking wetted-channel extent.

Each function takes an ``ee.Image`` with band names already normalized
to a common vocabulary (see ``composites.rename_bands``): ``blue``, ``green``,
``red``, ``nir``, ``swir1``, ``swir2``. This keeps the same code working
across Landsat 5/7/8/9 and Sentinel-2 without special cases.
"""

from __future__ import annotations

import ee


def ndvi(img: ee.Image) -> ee.Image:
    """Normalized Difference Vegetation Index. (nir - red) / (nir + red)."""
    return img.normalizedDifference(["nir", "red"]).rename("ndvi")


def ndmi(img: ee.Image) -> ee.Image:
    """Normalized Difference Moisture Index. (nir - swir1) / (nir + swir1).

    A.k.a. NDWI-Gao. Sensitive to leaf water content; excellent for
    riparian and groundwater-dependent-vegetation work in arid systems.
    """
    return img.normalizedDifference(["nir", "swir1"]).rename("ndmi")


def ndwi(img: ee.Image) -> ee.Image:
    """McFeeters NDWI for open water. (green - nir) / (green + nir).

    Note: distinct from Gao's NDWI, which we call NDMI above.
    """
    return img.normalizedDifference(["green", "nir"]).rename("ndwi")


def evi(img: ee.Image) -> ee.Image:
    """Enhanced Vegetation Index.

    ``2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1)``.
    Less prone to saturation than NDVI in dense canopy; useful cross-check.
    """
    return img.expression(
        "2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)",
        {
            "nir": img.select("nir"),
            "red": img.select("red"),
            "blue": img.select("blue"),
        },
    ).rename("evi")


def nbr(img: ee.Image) -> ee.Image:
    """Normalized Burn Ratio. (nir - swir2) / (nir + swir2).

    Not directly a moisture index, but change in NBR flags fire, which
    can confound vegetation trend analysis. Worth including.
    """
    return img.normalizedDifference(["nir", "swir2"]).rename("nbr")


def add_all_indices(img: ee.Image) -> ee.Image:
    """Add ndvi, ndmi, ndwi, evi, nbr as bands to ``img``.

    Convenience for mapping over an ImageCollection.
    """
    return img.addBands([ndvi(img), ndmi(img), ndwi(img), evi(img), nbr(img)])

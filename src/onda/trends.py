"""Trend testing and change-point detection for annual index time series.

The 2018 project had no way to say whether a change in NDVI was
meaningful or just noise. We fix that here with two complementary tools:

* **Mann-Kendall** — nonparametric test for monotonic trend. Standard
  in hydrology and paleoclimate. Handles ties, doesn't assume normality,
  robust to outliers. We use the seasonal variant when appropriate.
* **Change-point detection** — locates the year (or years) at which
  the mean/trend of the series shifted. Useful for asking "did the
  vegetation regime shift after the 2015 restoration?" without having
  to specify the shift date up front.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MKResult:
    """Mann-Kendall trend test result."""

    trend: str  # "increasing", "decreasing", "no trend"
    h: bool  # is trend significant at alpha
    p: float
    z: float
    tau: float  # Kendall's tau
    s: float
    var_s: float
    slope: float  # Theil-Sen slope, units per year
    intercept: float


def mann_kendall(series: pd.Series, alpha: float = 0.05) -> MKResult:
    """Run the Mann-Kendall trend test with Theil-Sen slope estimator.

    Parameters
    ----------
    series : pd.Series
        Indexed by year (int). NaNs are dropped.
    alpha : float
        Significance level. Default 0.05.

    Returns
    -------
    MKResult
    """
    try:
        import pymannkendall as mk
    except ImportError as e:
        raise ImportError(
            "pymannkendall is required. Install with `conda install -c conda-forge pymannkendall`."
        ) from e

    s = series.dropna().sort_index()
    if len(s) < 4:
        raise ValueError(f"Need at least 4 points for MK test, got {len(s)}.")

    r = mk.original_test(s.values, alpha=alpha)
    return MKResult(
        trend=r.trend,
        h=bool(r.h),
        p=float(r.p),
        z=float(r.z),
        tau=float(r.Tau),
        s=float(r.s),
        var_s=float(r.var_s),
        slope=float(r.slope),
        intercept=float(r.intercept),
    )


def change_points(
    series: pd.Series,
    n_bkps: int | None = None,
    penalty: float = 3.0,
    model: str = "rbf",
) -> list[int]:
    """Detect change points in an annual time series.

    Uses the PELT algorithm from ``ruptures``. If ``n_bkps`` is given,
    forces that many breakpoints; otherwise selects automatically using
    ``penalty``.

    Parameters
    ----------
    series : pd.Series
        Indexed by year, sorted ascending.
    n_bkps : int, optional
        If given, forces exactly this many change points (via Dynp).
    penalty : float
        Penalty for the PELT algorithm when ``n_bkps`` is None.
        Higher penalty → fewer change points.
    model : str
        Cost model: "l1", "l2", "rbf", "normal". Default "rbf" works well
        for the moderately non-Gaussian shifts we see in NDVI series.

    Returns
    -------
    list[int]
        Years at which change points occur (the year at the *start* of
        each new segment, excluding the final endpoint).
    """
    try:
        import ruptures as rpt
    except ImportError as e:
        raise ImportError(
            "ruptures is required. Install with `conda install -c conda-forge ruptures`."
        ) from e

    s = series.dropna().sort_index()
    if len(s) < 6:
        return []
    values = s.values.reshape(-1, 1)

    if n_bkps is not None:
        algo = rpt.Dynp(model=model).fit(values)
        bkps = algo.predict(n_bkps=n_bkps)
    else:
        algo = rpt.Pelt(model=model).fit(values)
        bkps = algo.predict(pen=penalty)

    # ruptures returns 1-indexed positions including the final endpoint;
    # drop that and map back to years.
    years = s.index.to_list()
    return [years[b] for b in bkps if b < len(years)]


def theil_sen_line(series: pd.Series) -> tuple[float, float]:
    """Return (slope_per_year, intercept) using the Theil-Sen estimator.

    Convenience wrapper for plotting a trend line.
    """
    from scipy import stats

    s = series.dropna().sort_index()
    r = stats.theilslopes(s.values, s.index.values.astype(float))
    return float(r.slope), float(r.intercept)


def rolling_stats(series: pd.Series, window: int = 5) -> pd.DataFrame:
    """Centered rolling mean and std for visual smoothing."""
    return pd.DataFrame(
        {
            "value": series,
            "roll_mean": series.rolling(window, center=True, min_periods=3).mean(),
            "roll_std": series.rolling(window, center=True, min_periods=3).std(),
        }
    )

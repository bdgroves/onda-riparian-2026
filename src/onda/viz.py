"""Plotting and mapping helpers.

Two families of visuals:

1. **Time-series plots** â€” annual index values with Theil-Sen trend line,
   rolling smoother, restoration event vlines, and change-point markers.
2. **Interactive maps** â€” leafmap wrappers for showing composites and
   trend rasters side-by-side. See ``dashboard/`` for the Streamlit version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

if TYPE_CHECKING:
    import ee

# Palette. Kept intentionally muted â€” real data over vibe.
PAL = {
    "ndvi": "#3f7f3f",
    "ndmi": "#1f6faf",
    "ndwi": "#0d3b66",
    "trend": "#c04040",
    "cp": "#8a2be2",
    "event": "#e08a1a",
    "roll": "#666666",
}


def plot_annual_series(
    series: pd.Series,
    index_name: str = "ndvi",
    events: pd.DataFrame | None = None,
    change_pts: list[int] | None = None,
    trend: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
    title: str | None = None,
) -> plt.Axes:
    """Plot an annual index series with optional trend / change-points / events.

    Parameters
    ----------
    series : pd.Series
        Indexed by year (int).
    index_name : str
        For legend colouring; one of the keys in ``PAL`` or any color string.
    events : DataFrame, optional
        Restoration events with columns ``start_year`` and ``project_name``.
    change_pts : list of int, optional
        Years to mark as change points.
    trend : (slope, intercept), optional
        If given, draws a Theil-Sen trend line.
    ax : matplotlib Axes, optional
    title : str, optional
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4))

    color = PAL.get(index_name.lower(), index_name)
    s = series.dropna().sort_index()

    ax.plot(s.index, s.values, marker="o", ms=4, lw=1.2, color=color, label=index_name.upper())

    roll = s.rolling(5, center=True, min_periods=3).mean()
    ax.plot(roll.index, roll.values, lw=2, color=PAL["roll"], alpha=0.7, label="5-yr rolling mean")

    if trend is not None:
        slope, intercept = trend
        xs = s.index.values.astype(float)
        ys = slope * xs + intercept
        ax.plot(xs, ys, ls="--", color=PAL["trend"], lw=1.5,
                label=f"Theil-Sen slope: {slope:+.4f}/yr")

    if change_pts:
        for cp in change_pts:
            ax.axvline(cp, ls=":", color=PAL["cp"], alpha=0.7)
        ax.axvline(change_pts[0], ls=":", color=PAL["cp"], alpha=0.7,
                   label="change-point")

    if events is not None and not events.empty:
        for _, row in events.iterrows():
            ax.axvline(row["start_year"], ls="-", color=PAL["event"], alpha=0.4, lw=2)
        ax.axvline(events.iloc[0]["start_year"], ls="-",
                   color=PAL["event"], alpha=0.4, lw=2, label="restoration event")

    ax.set_xlabel("Year")
    ax.set_ylabel(index_name.upper())
    if title:
        ax.set_title(title)
    ax.legend(loc="best", fontsize=9, frameon=False)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    return ax


def leafmap_composite(image, region, vis_params: dict, name: str = "composite"):
    """Return a leafmap Map showing an ee.Image composite over a region.

    Deferred import so the library doesn't demand leafmap for non-map code.
    """
    import geemap

    m = geemap.Map()
    m.centerObject(region, 11)
    m.addLayer(image, vis_params, name)
    m.addLayer(region, {"color": "white"}, "study area")
    return m


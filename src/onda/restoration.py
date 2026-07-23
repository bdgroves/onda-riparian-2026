"""Join remote-sensing time series to ONDA restoration project events.

ONDA installs beaver dam analogs (BDAs), plants riparian vegetation, and
does other ground work at specific sites in specific years. To evaluate
whether a change in NDVI/NDMI is plausibly a restoration outcome vs.
background variability, we need to know when work happened.

Restoration events are stored in ``data/restoration/events.csv`` with
columns:

    site_slug, project_name, start_year, treatment_type, notes

Where ``site_slug`` matches ``onda.sites.SITES`` keys. Fill this file
in as you learn about specific projects; the pipeline treats missing
events gracefully.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_EVENTS_PATH = Path("data/restoration/events.csv")


def load_events(path: str | Path = DEFAULT_EVENTS_PATH) -> pd.DataFrame:
    """Load the restoration events CSV.

    If the file doesn't exist, returns an empty DataFrame with the
    expected columns rather than raising.
    """
    p = Path(path)
    cols = ["site_slug", "project_name", "start_year", "treatment_type", "notes"]
    if not p.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(p)
    missing = set(cols) - set(df.columns)
    if missing:
        raise ValueError(f"events.csv is missing columns: {sorted(missing)}")
    df["start_year"] = df["start_year"].astype(int)
    return df


def events_for(site_slug: str, path: str | Path = DEFAULT_EVENTS_PATH) -> pd.DataFrame:
    """Return events for one site, sorted by start_year."""
    df = load_events(path)
    return df[df["site_slug"] == site_slug].sort_values("start_year").reset_index(drop=True)


def annotate_time_series(
    ts: pd.DataFrame,
    site_slug: str,
    year_col: str = "year",
    path: str | Path = DEFAULT_EVENTS_PATH,
) -> pd.DataFrame:
    """Add a ``restoration_event`` column marking rows in event years.

    The value is the project name if an event started that year, else NaN.
    Multiple events in one year are concatenated with " + ".
    """
    events = events_for(site_slug, path=path)
    if events.empty:
        out = ts.copy()
        out["restoration_event"] = pd.NA
        return out

    per_year = events.groupby("start_year")["project_name"].apply(
        lambda s: " + ".join(s.astype(str))
    )
    out = ts.copy()
    out["restoration_event"] = out[year_col].map(per_year)
    return out

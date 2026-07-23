"""Join remote-sensing time series to ONDA restoration project events.

Events live in data/restoration/events.csv with columns:
    site_slug, project_name, start_year, treatment_type, notes

Fill it in as you get project info from ONDA. The pipeline treats the file
as optional and treats missing / empty / malformed rows gracefully.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_EVENTS_PATH = Path("data/restoration/events.csv")
_COLS = ["site_slug", "project_name", "start_year", "treatment_type", "notes"]


def load_events(path: str | Path = DEFAULT_EVENTS_PATH) -> pd.DataFrame:
    """Load the restoration events CSV.

    Returns an empty DataFrame with the expected columns if the file
    is missing, empty, or has no valid data rows.
    """
    p = Path(path)
    empty = pd.DataFrame(columns=_COLS)
    if not p.exists():
        return empty

    try:
        df = pd.read_csv(p, comment="#")
    except pd.errors.EmptyDataError:
        return empty

    if df.empty:
        return empty

    missing = set(_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"events.csv is missing columns: {sorted(missing)}")

    # Coerce start_year to int, dropping rows where it can't be parsed.
    df["start_year"] = pd.to_numeric(df["start_year"], errors="coerce")
    df = df.dropna(subset=["start_year"])
    df["start_year"] = df["start_year"].astype(int)
    return df.reset_index(drop=True)


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
    """Add a `restoration_event` column marking rows in event years."""
    events = events_for(site_slug, path=path)
    out = ts.copy()
    if events.empty:
        out["restoration_event"] = pd.NA
        return out

    per_year = events.groupby("start_year")["project_name"].apply(
        lambda s: " + ".join(s.astype(str))
    )
    out["restoration_event"] = out[year_col].map(per_year)
    return out
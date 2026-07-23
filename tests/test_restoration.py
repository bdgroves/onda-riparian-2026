"""Tests for onda.restoration."""

from pathlib import Path

import pandas as pd

from onda.restoration import annotate_time_series, events_for, load_events


def test_load_events_missing_file_returns_empty(tmp_path: Path):
    df = load_events(tmp_path / "nope.csv")
    assert df.empty
    assert list(df.columns) == [
        "site_slug", "project_name", "start_year", "treatment_type", "notes"
    ]


def test_load_events_reads_csv(tmp_path: Path):
    p = tmp_path / "events.csv"
    p.write_text(
        "site_slug,project_name,start_year,treatment_type,notes\n"
        "pine_creek,Test,2016,bda,x\n"
    )
    df = load_events(p)
    assert len(df) == 1
    assert df.iloc[0]["start_year"] == 2016


def test_annotate_time_series_adds_event_column(tmp_path: Path):
    p = tmp_path / "events.csv"
    p.write_text(
        "site_slug,project_name,start_year,treatment_type,notes\n"
        "pine_creek,BDA,2016,bda,\n"
        "pine_creek,Planting,2019,planting,\n"
    )
    ts = pd.DataFrame({"year": [2015, 2016, 2017, 2018, 2019, 2020], "ndmi": [0.3] * 6})
    out = annotate_time_series(ts, "pine_creek", path=p)
    assert out.loc[out["year"] == 2016, "restoration_event"].iloc[0] == "BDA"
    assert out.loc[out["year"] == 2019, "restoration_event"].iloc[0] == "Planting"
    assert pd.isna(out.loc[out["year"] == 2015, "restoration_event"].iloc[0])


def test_events_for_returns_empty_for_unknown_site(tmp_path: Path):
    p = tmp_path / "events.csv"
    p.write_text(
        "site_slug,project_name,start_year,treatment_type,notes\n"
        "pine_creek,BDA,2016,bda,\n"
    )
    df = events_for("unknown_site", path=p)
    assert df.empty

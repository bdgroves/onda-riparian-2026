"""Tests for trend and change-point functions.

These use synthetic data so they run without Earth Engine / network.
"""

import numpy as np
import pandas as pd
import pytest

from onda.trends import change_points, mann_kendall, rolling_stats, theil_sen_line


@pytest.fixture
def increasing_series() -> pd.Series:
    """A noisy but clearly increasing series 1984→2024."""
    rng = np.random.default_rng(42)
    years = np.arange(1984, 2025)
    values = 0.2 + 0.005 * (years - 1984) + rng.normal(0, 0.02, len(years))
    return pd.Series(values, index=years, name="ndmi")


@pytest.fixture
def flat_series() -> pd.Series:
    rng = np.random.default_rng(7)
    years = np.arange(1984, 2025)
    values = 0.3 + rng.normal(0, 0.02, len(years))
    return pd.Series(values, index=years, name="ndmi")


@pytest.fixture
def stepped_series() -> pd.Series:
    """A series with a clear regime shift in 2010."""
    rng = np.random.default_rng(11)
    years = np.arange(1984, 2025)
    values = np.where(years < 2010, 0.3, 0.45) + rng.normal(0, 0.02, len(years))
    return pd.Series(values, index=years, name="ndmi")


def test_mann_kendall_detects_increase(increasing_series):
    r = mann_kendall(increasing_series)
    assert r.trend == "increasing"
    assert r.h is True
    assert r.p < 0.05
    assert r.slope > 0


def test_mann_kendall_no_trend_on_flat(flat_series):
    r = mann_kendall(flat_series)
    assert r.trend == "no trend"
    assert r.h is False


def test_mann_kendall_short_series_raises():
    s = pd.Series([1.0, 2.0], index=[2000, 2001])
    with pytest.raises(ValueError):
        mann_kendall(s)


def test_theil_sen_slope_positive_for_increasing(increasing_series):
    slope, _ = theil_sen_line(increasing_series)
    assert slope > 0


def test_change_points_finds_2010_shift(stepped_series):
    cps = change_points(stepped_series, penalty=1.0)
    # Should find at least one change point, close to 2010
    assert cps, f"expected at least one change point, got {cps}"
    assert min(abs(c - 2010) for c in cps) <= 2, f"got change points {cps}"


def test_change_points_returns_empty_for_short():
    s = pd.Series([0.3, 0.4, 0.35], index=[2000, 2001, 2002])
    assert change_points(s) == []


def test_rolling_stats_shape(increasing_series):
    out = rolling_stats(increasing_series, window=5)
    assert set(out.columns) == {"value", "roll_mean", "roll_std"}
    assert len(out) == len(increasing_series)

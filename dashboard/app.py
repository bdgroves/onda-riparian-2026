"""ONDA Riparian Index Explorer — Streamlit dashboard.

Serves cached CSVs from ``outputs/`` and lets a non-technical viewer
(e.g. an ONDA staffer) pick a site, pick an index, and see the trend
alongside restoration events.

Run:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from onda.restoration import events_for
from onda.sites import SITES
from onda.trends import change_points, mann_kendall, theil_sen_line
from onda.viz import plot_annual_series

st.set_page_config(page_title="ONDA Riparian Index Explorer", layout="wide")

st.title("ONDA Riparian Index Explorer")
st.caption(
    "40+ years of Landsat surface reflectance over eastern Oregon "
    "restoration drainages. A 2026 rebuild of a 2018 volunteer project."
)

# ---------------------------------------------------------------- controls
col_a, col_b = st.columns(2)
site_slug = col_a.selectbox(
    "Site", options=list(SITES.keys()),
    format_func=lambda s: SITES[s].name,
)
index = col_b.selectbox("Index", options=["ndmi", "ndvi", "ndwi", "evi"])

# ---------------------------------------------------------------- data load
csv = Path("outputs") / f"{site_slug}_landsat_annual.csv"
if not csv.exists():
    st.warning(
        f"No cached data for {SITES[site_slug].name} yet. "
        f"Run `notebooks/02_landsat_timeseries.py` for this site first."
    )
    st.stop()

df = pd.read_csv(csv)
series = df.set_index("year")[index]

# ---------------------------------------------------------------- stats
mk = mann_kendall(series)
slope, intercept = theil_sen_line(series)
cps = change_points(series, penalty=2.0)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Trend", mk.trend)
m2.metric("Theil-Sen slope /yr", f"{slope:+.5f}")
m3.metric("MK p-value", f"{mk.p:.3f}")
m4.metric("Change points", ", ".join(str(c) for c in cps) or "none")

# ---------------------------------------------------------------- plot
events = events_for(site_slug)
ax = plot_annual_series(
    series, index_name=index,
    events=events, change_pts=cps,
    trend=(slope, intercept),
    title=f"{SITES[site_slug].name} · annual late-summer {index.upper()}",
)
st.pyplot(ax.figure)

with st.expander("Raw data"):
    st.dataframe(df)

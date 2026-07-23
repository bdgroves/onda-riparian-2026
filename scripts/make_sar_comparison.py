"""Compare Sentinel-1 SAR backscatter with Landsat NDMI, per site.

The core question this figure answers: does an independent (radar) sensor
see the same moisture story that the optical NDMI series told?

If SAR VV correlates well with NDMI within each site, the moisture signal
is real. If they disagree, the NDMI trend is probably driven by vegetation
structure change (biomass, canopy) rather than actual soil moisture.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from onda.sites import SITES

OUT = Path("outputs")


def load_pair(slug: str) -> pd.DataFrame:
    ls = pd.read_csv(OUT / f"{slug}_landsat_annual.csv")[["year", "ndmi"]]
    sar = pd.read_csv(OUT / f"{slug}_sar_annual.csv")[["year", "VV", "VH"]]
    return ls.merge(sar, on="year", how="outer").sort_values("year").reset_index(drop=True)


fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)

for ax, (slug, site) in zip(axes, SITES.items()):
    df = load_pair(slug)
    df_shared = df.dropna(subset=["ndmi", "VV"])

    r, p = (float("nan"), float("nan"))
    if len(df_shared) >= 3:
        r, p = stats.pearsonr(df_shared["ndmi"], df_shared["VV"])

    ax2 = ax.twinx()
    ax.plot(df["year"], df["ndmi"], "o-", color="#1f6faf", ms=4, lw=1.2,
            label="Landsat NDMI")
    ax2.plot(df["year"], df["VV"], "s-", color="#c04040", ms=4, lw=1.2, alpha=0.75,
             label="Sentinel-1 VV (dB)")

    ax.set_ylabel("NDMI", color="#1f6faf")
    ax2.set_ylabel("VV backscatter (dB)", color="#c04040")
    ax.tick_params(axis="y", labelcolor="#1f6faf")
    ax2.tick_params(axis="y", labelcolor="#c04040")

    if not pd.isna(r):
        ax.set_title(
            f"{site.name}   Pearson r = {r:+.2f}, p = {p:.3f}  "
            f"(n = {len(df_shared)} shared years)",
            fontsize=10,
        )
    else:
        ax.set_title(site.name, fontsize=10)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Year")
fig.suptitle(
    "Independent moisture check: Landsat NDMI vs Sentinel-1 SAR backscatter",
    y=0.995,
    fontsize=12,
)
fig.tight_layout()
out_path = OUT / "sar_vs_ndmi.png"
fig.savefig(out_path, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out_path}")
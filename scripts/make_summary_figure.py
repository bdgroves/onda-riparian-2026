"""Generate summary figures from the three-site Landsat CSVs.

Reads outputs/{slug}_landsat_annual.csv for each site in SITES and produces:

  outputs/three_site_grid.png            - 3 rows (sites) x 3 cols (indices)
                                            with points, 5-yr rolling, and trend
  outputs/three_site_ndmi_comparison.png - z-scored NDMI overlay, all sites
  outputs/three_site_ndwi_comparison.png - z-scored NDWI overlay, all sites

Usage:
    pixi run python scripts/make_summary_figure.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from onda.sites import SITES
from onda.trends import change_points

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

PALETTE = {"ndvi": "#3f7f3f", "ndmi": "#1f6faf", "ndwi": "#0d3b66"}
LONG_NAMES = {
    "ndvi": "NDVI (greenness)",
    "ndmi": "NDMI (leaf moisture)",
    "ndwi": "NDWI (open water)",
}
SITE_COLORS = {"hay_creek": "#c04040", "pine_creek": "#e08a1a", "sf_crooked": "#2a8f2a"}


def load_site_csv(slug: str) -> pd.DataFrame:
    path = OUT / f"{slug}_landsat_annual.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run scripts/run_all_sites.py first."
        )
    return pd.read_csv(path).sort_values("year").reset_index(drop=True)


# ---------------------------------------------------------------- Grid figure
def make_grid_figure(dfs: dict[str, pd.DataFrame]) -> None:
    fig, axes = plt.subplots(3, 3, figsize=(14, 9), sharex=True)

    for i, (slug, site) in enumerate(SITES.items()):
        df = dfs[slug]
        for j, idx in enumerate(("ndvi", "ndmi", "ndwi")):
            ax = axes[i, j]
            y = df[idx].dropna().values
            x = df.loc[df[idx].notna(), "year"].values.astype(float)

            # Raw + rolling + Theil-Sen
            ax.plot(x, y, "o-", color=PALETTE[idx], ms=3, lw=0.9, alpha=0.7)
            roll = pd.Series(y).rolling(5, center=True, min_periods=3).mean()
            ax.plot(x, roll, color="#333", lw=1.8, alpha=0.75,
                    label="5-yr rolling" if (i == 0 and j == 0) else None)
            ts = stats.theilslopes(y, x)
            ax.plot(x, ts.slope * x + ts.intercept, "--", color="#c04040", lw=1.2,
                    label="Theil-Sen" if (i == 0 and j == 0) else None)

            # Change points
            cps = change_points(pd.Series(y, index=x.astype(int)), penalty=2.0)
            for cp in cps:
                ax.axvline(cp, ls=":", color="#8a2be2", alpha=0.65, lw=1.2)

            # Slope annotation
            ax.text(0.03, 0.94,
                    f"slope: {ts.slope:+.4f}/yr",
                    transform=ax.transAxes, fontsize=8,
                    verticalalignment="top",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1.5))

            if j == 0:
                ax.set_ylabel(site.name, fontsize=10, fontweight="bold")
            if i == 0:
                ax.set_title(LONG_NAMES[idx], fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=8)

    axes[-1, 1].set_xlabel("Year", fontsize=10)
    fig.suptitle("ONDA riparian sites - Landsat 1984-2025 (late-summer composites)",
                 y=0.995, fontsize=12)
    # Add legend outside
    handles, labels = axes[0, 0].get_legend_handles_labels()
    handles.append(plt.Line2D([], [], ls=":", color="#8a2be2", lw=1.2, label="change-point"))
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9, frameon=False,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    out = OUT / "three_site_grid.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ---------------------------------------------------------------- Overlay figures
def make_overlay(dfs: dict[str, pd.DataFrame], idx: str) -> None:
    """Z-scored overlay of one index across all sites, showing divergence."""
    fig, ax = plt.subplots(figsize=(10, 5))

    for slug, site in SITES.items():
        df = dfs[slug]
        y = df[idx].dropna()
        x = df.loc[df[idx].notna(), "year"].astype(float)
        z = (y - y.mean()) / y.std()

        color = SITE_COLORS[slug]
        ax.plot(x, z, "o-", color=color, ms=3, lw=0.9, alpha=0.5, label=None)
        roll = z.rolling(5, center=True, min_periods=3).mean()
        ax.plot(x, roll, color=color, lw=2.2, label=site.name)

    ax.axhline(0, color="#888", lw=0.7, ls="-")
    ax.set_ylabel(f"{idx.upper()} (z-score, 5-yr rolling)")
    ax.set_xlabel("Year")
    ax.set_title(f"{LONG_NAMES[idx]} - z-scored across sites, 1984-2025")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    out = OUT / f"three_site_{idx}_comparison.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    dfs = {slug: load_site_csv(slug) for slug in SITES}
    make_grid_figure(dfs)
    make_overlay(dfs, "ndmi")
    make_overlay(dfs, "ndwi")
    print("\nDone. Three figures in outputs/.")
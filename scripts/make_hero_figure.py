"""Generate the hero figure: map of the three sites + summary stats panel.

Reads:  data/sites/onda_study_sites_enriched.geojson
Writes: outputs/hero_figure.png

Portfolio-quality summary suitable for the top of the README, the blog
post, and Jefferson's email.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patheffects import withStroke

SITES_GEOJSON = Path("data/sites/onda_study_sites_enriched.geojson")
OUT = Path("outputs/hero_figure.png")

SITE_COLORS = {
    "sf_crooked": "#2a8f2a",  # restoration-success candidate = green
    "pine_creek": "#e08a1a",  # green-but-drying = amber
    "hay_creek":  "#c04040",  # green-but-drying = red
}
DISPLAY_ORDER = ["sf_crooked", "pine_creek", "hay_creek"]

LABEL_OFFSETS = {
    "hay_creek":  ( 0.03,  0.04),
    "pine_creek": (-0.15,  0.02),
    "sf_crooked": ( 0.03, -0.03),
}


def _fmt_arrow(trend: str) -> str:
    return {"increasing": "^", "decreasing": "v", "no trend": "="}[trend]


def _cell_color(trend: str, p: float) -> str:
    sig = p < 0.05
    if trend == "increasing" and sig: return "#2a8f2a"
    if trend == "decreasing" and sig: return "#c04040"
    if sig:                            return "#8a5a2a"
    return "#999"


def make_hero(sites: gpd.GeoDataFrame) -> None:
    fig = plt.figure(figsize=(15, 8.5), facecolor="white")
    gs = GridSpec(1, 2, width_ratios=[1.15, 1], wspace=0.08, figure=fig)

    # --------------------------------------- Map
    ax_map = fig.add_subplot(gs[0, 0])
    ax_map.set_facecolor("#f4f1e8")

    plot_sites = sites.copy()
    plot_sites["_color"] = plot_sites["slug"].map(SITE_COLORS)
    plot_sites.plot(ax=ax_map, color=plot_sites["_color"],
                    edgecolor="#111", lw=1.5, alpha=0.75, zorder=3)

    for _, row in sites.iterrows():
        slug = row["slug"]
        cent = row.geometry.centroid
        dx, dy = LABEL_OFFSETS[slug]
        ax_map.annotate(
            row["name"],
            xy=(cent.x, cent.y), xytext=(cent.x + dx, cent.y + dy),
            fontsize=11, fontweight="bold", color="#111",
            ha="left" if dx > 0 else "right",
            arrowprops=dict(arrowstyle="-", color="#555", lw=0.8),
            path_effects=[withStroke(linewidth=2.5, foreground="white")],
            zorder=5,
        )

    minx, miny, maxx, maxy = sites.total_bounds
    pad_x, pad_y = (maxx - minx) * 0.35, (maxy - miny) * 0.10
    ax_map.set_xlim(minx - pad_x, maxx + pad_x)
    ax_map.set_ylim(miny - pad_y, maxy + pad_y)
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    for spine in ax_map.spines.values():
        spine.set_color("#888")

    ax_map.text(0.02, 0.98, "Three ONDA riparian restoration reaches",
                transform=ax_map.transAxes, fontsize=14, fontweight="bold",
                color="#111", va="top", ha="left",
                path_effects=[withStroke(linewidth=3, foreground="white")])
    ax_map.text(0.02, 0.945, "Central & eastern Oregon  |  6.7 to 17.5 km each",
                transform=ax_map.transAxes, fontsize=10, color="#444",
                va="top", ha="left",
                path_effects=[withStroke(linewidth=2.5, foreground="white")])

    ax_map.annotate("N", xy=(0.94, 0.90), xycoords="axes fraction",
                    fontsize=14, fontweight="bold", ha="center", va="center", color="#111")
    ax_map.annotate("", xy=(0.94, 0.94), xytext=(0.94, 0.86),
                    xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#111", lw=1.5))

    legend_patches = [
        mpatches.Patch(color=SITE_COLORS["sf_crooked"],
                       label="SF Crooked  -  wetting hypothesis (2005-2015)"),
        mpatches.Patch(color=SITE_COLORS["pine_creek"],
                       label="Pine Creek  -  regime shift in 2019"),
        mpatches.Patch(color=SITE_COLORS["hay_creek"],
                       label="Hay Creek  -  recent SAR-detected wetting"),
    ]
    ax_map.legend(handles=legend_patches, loc="lower left",
                  fontsize=9, frameon=True, facecolor="white",
                  edgecolor="#888", framealpha=0.92)

    # --------------------------------------- Stats panel
    ax_stat = fig.add_subplot(gs[0, 1])
    ax_stat.set_facecolor("white")
    ax_stat.set_xlim(0, 10)
    ax_stat.set_ylim(0, 10)
    ax_stat.axis("off")

    ax_stat.text(0, 9.75, "40 years of Landsat  +  10 years of Sentinel-1 SAR",
                 fontsize=13, fontweight="bold", color="#111")
    ax_stat.text(0, 9.35, "Late-summer composites, Jul 15 - Sep 15, per-site polygon mean",
                 fontsize=9, color="#555", style="italic")
    ax_stat.plot([0, 10], [9.15, 9.15], color="#111", lw=1.5)

    sites_by_slug = {row["slug"]: row for _, row in sites.iterrows()}
    row_ys = [7.4, 4.7, 2.0]

    for y, slug in zip(row_ys, DISPLAY_ORDER):
        site = sites_by_slug[slug]
        color = SITE_COLORS[slug]

        ax_stat.add_patch(mpatches.Rectangle((0, y - 0.55), 0.28, 1.9,
                                             facecolor=color, edgecolor="none"))
        ax_stat.text(0.45, y + 0.85, site["name"], fontsize=12, fontweight="bold",
                     color="#111", va="center")
        notes = site["notes"] if pd.notna_or_str(site.get("notes")) else ""
        ax_stat.text(0.45, y + 0.35, notes.split(".")[0],
                     fontsize=8, color="#666", va="center", style="italic")

        cells = [
            ("NDVI",   site["landsat_ndvi_trend"], site["landsat_ndvi_p"], site["landsat_ndvi_slope_per_yr"]),
            ("NDMI",   site["landsat_ndmi_trend"], site["landsat_ndmi_p"], site["landsat_ndmi_slope_per_yr"]),
            ("NDWI",   site["landsat_ndwi_trend"], site["landsat_ndwi_p"], site["landsat_ndwi_slope_per_yr"]),
            ("SAR VV", site.get("sar_vv_trend", "-"), site.get("sar_vv_p", 1.0), site.get("sar_vv_slope_dB_per_yr", 0.0)),
        ]
        x_start, col_w = 0.45, 2.35
        for i, (label, trend, p, slope) in enumerate(cells):
            cx = x_start + i * col_w
            marker = _fmt_arrow(trend) if trend in ("increasing", "decreasing", "no trend") else "?"
            color_ = _cell_color(trend, p) if trend in ("increasing", "decreasing", "no trend") else "#999"
            weight = "bold" if p < 0.05 else "normal"
            ax_stat.text(cx, y - 0.15, label, fontsize=8, color="#333",
                         fontweight="bold", va="center")
            ax_stat.text(cx, y - 0.55, f"{marker}  {trend}",
                         fontsize=9, color=color_, va="center", fontweight=weight)
            ax_stat.text(cx, y - 0.95, f"p={p:.3f}  ({slope:+.4f}/yr)",
                         fontsize=7.5, color="#555", va="center")

        ax_stat.text(0.45, y - 1.55, f"Story: {site['story']}",
                     fontsize=8.5, color="#111", style="italic", wrap=True)

        if y != row_ys[-1]:
            ax_stat.plot([0, 10], [y - 2.0, y - 2.0], color="#e0e0e0", lw=0.8)

    ax_stat.plot([0, 10], [0.3, 0.3], color="#111", lw=1.5)
    ax_stat.text(0, -0.15,
                 "Bold arrows = statistically significant (p < 0.05). "
                 "Colors: green = greening/wetting, red = drying, brown = mixed.",
                 fontsize=7.5, color="#666", va="top")

    fig.suptitle("ONDA Riparian 2026  |  Three sites, two sensors, one 40-year record",
                 y=0.99, fontsize=15, fontweight="bold", x=0.5)
    fig.text(0.5, 0.955,
             "A 2026 rebuild of a 2018 volunteer GIS project for the Oregon Natural Desert Association",
             ha="center", fontsize=10, style="italic", color="#555")

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {OUT}")


# Tiny helper: pandas.notna doesn't handle strings; this does
import pandas as pd
def _notna_or_str(x):
    return isinstance(x, str) or (x is not None and pd.notna(x))
pd.notna_or_str = _notna_or_str


if __name__ == "__main__":
    sites = gpd.read_file(SITES_GEOJSON)
    make_hero(sites)
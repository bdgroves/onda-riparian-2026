"""Generate the hero figure: Oregon overview map + three site cards.

Reads:
  data/sites/onda_study_sites_enriched.geojson
  data/ancillary/oregon_boundary.geojson

Writes:
  outputs/hero_figure.png

If the Oregon boundary isn't cached in data/ancillary/, this script
fetches it once from a stable GitHub-hosted geojson and caches it there.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
from matplotlib.patheffects import withStroke

SITES_GEOJSON = Path("data/sites/onda_study_sites_enriched.geojson")
OREGON_CACHE = Path("data/ancillary/oregon_boundary.geojson")
OUT = Path("outputs/hero_figure.png")

SITE_COLORS = {"sf_crooked": "#2a8f2a", "pine_creek": "#e08a1a", "hay_creek": "#c04040"}
STORY_ACCENT = {"sf_crooked": "#e8f4e8", "pine_creek": "#fdf1de", "hay_creek": "#f9e5e5"}
DISPLAY_ORDER = ["sf_crooked", "pine_creek", "hay_creek"]

LABEL_POSITIONS = {
    "hay_creek":  (-116.9, 45.55),
    "pine_creek": (-116.9, 44.75),
    "sf_crooked": (-116.9, 43.95),
}


def load_oregon() -> gpd.GeoDataFrame:
    """Load Oregon state boundary. Fetch and cache on first run."""
    if OREGON_CACHE.exists():
        return gpd.read_file(OREGON_CACHE)

    print("Oregon boundary not cached, fetching...")
    OREGON_CACHE.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read().decode())
    for feat in data.get("features", []):
        if feat.get("properties", {}).get("name") == "Oregon":
            payload = {"type": "FeatureCollection", "features": [feat]}
            with open(OREGON_CACHE, "w") as f:
                json.dump(payload, f)
            print(f"Cached {OREGON_CACHE}")
            gdf = gpd.read_file(OREGON_CACHE)
            if gdf.crs is None:
                gdf.set_crs(4326, inplace=True)
            return gdf
    raise RuntimeError("Oregon feature not found in the source dataset")


def _arrow(trend: str) -> str:
    return {"increasing": "\u25B2", "decreasing": "\u25BC", "no trend": "\u25CF"}.get(trend, "?")


def _cell_color(trend: str, p: float) -> str:
    sig = p < 0.05
    if trend == "increasing" and sig: return "#2a8f2a"
    if trend == "decreasing" and sig: return "#c04040"
    if sig:                            return "#8a5a2a"
    return "#888"


def draw_map(ax, sites, oregon, sites_by_slug):
    ax.set_facecolor("#eef2f7")
    ax.set_aspect("equal", adjustable="box")

    oregon.plot(ax=ax, color="#f6f0d9", edgecolor="#8a7859", linewidth=1.5, zorder=2)

    ax.text(-123.7, 45.3, "OREGON",
            fontsize=22, fontweight="bold", color="#e0d5a8",
            va="center", ha="center", zorder=3,
            path_effects=[withStroke(linewidth=1.5, foreground="#f6f0d9")])

    for slug in DISPLAY_ORDER:
        row = sites_by_slug[slug]
        poly = gpd.GeoSeries([row.geometry], crs=4326)
        poly.plot(ax=ax, color=SITE_COLORS[slug], alpha=0.9,
                  edgecolor="#111", linewidth=1.8, zorder=6)
        cent = row.geometry.centroid
        ax.plot(cent.x, cent.y, "o", ms=18, color="#111",
                markeredgecolor="white", markeredgewidth=2, zorder=7)
        ax.plot(cent.x, cent.y, "o", ms=12, color=SITE_COLORS[slug],
                markeredgecolor="white", markeredgewidth=1.5, zorder=8)
        lx, ly = LABEL_POSITIONS[slug]
        ax.annotate(row["name"], xy=(cent.x, cent.y), xytext=(lx, ly),
                    fontsize=12, fontweight="bold", color=SITE_COLORS[slug],
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color="#555", lw=1.0,
                                    connectionstyle="arc3,rad=0"),
                    zorder=9)

    minx, miny, maxx, maxy = oregon.total_bounds
    ax.set_xlim(minx - 0.5, maxx + 3.5)
    ax.set_ylim(miny - 0.5, maxy + 0.5)

    lon_ticks = np.arange(-124, -115, 2)
    lat_ticks = np.arange(42, 47, 1)
    for lon in lon_ticks:
        ax.axvline(lon, color="#ccc", lw=0.4, zorder=1, alpha=0.6)
    for lat in lat_ticks:
        ax.axhline(lat, color="#ccc", lw=0.4, zorder=1, alpha=0.6)
    ax.set_xticks(lon_ticks)
    ax.set_yticks(lat_ticks)
    ax.set_xticklabels([f"{abs(x)}\u00B0W" for x in lon_ticks], fontsize=8, color="#888")
    ax.set_yticklabels([f"{y}\u00B0N" for y in lat_ticks], fontsize=8, color="#888")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_color("#bbb"); spine.set_linewidth(0.8)

    xlim = ax.get_xlim(); ylim = ax.get_ylim()
    na_x = xlim[1] - (xlim[1] - xlim[0]) * 0.08
    na_y = ylim[0] + (ylim[1] - ylim[0]) * 0.10
    arrow_len = (ylim[1] - ylim[0]) * 0.055
    ax.annotate("", xy=(na_x, na_y + arrow_len), xytext=(na_x, na_y),
                arrowprops=dict(arrowstyle="->", color="#111", lw=1.8))
    ax.text(na_x, na_y + arrow_len + (ylim[1] - ylim[0]) * 0.012, "N",
            fontsize=11, fontweight="bold", ha="center", va="bottom", color="#111")

    scale_x0 = xlim[0] + (xlim[1] - xlim[0]) * 0.06
    scale_y = ylim[0] + (ylim[1] - ylim[0]) * 0.045
    scale_len_deg = 1.25
    ax.plot([scale_x0, scale_x0 + scale_len_deg], [scale_y, scale_y],
            color="#111", lw=2.5, solid_capstyle="butt")
    ax.plot([scale_x0, scale_x0], [scale_y - 0.05, scale_y + 0.05], color="#111", lw=2)
    ax.plot([scale_x0 + scale_len_deg] * 2, [scale_y - 0.05, scale_y + 0.05], color="#111", lw=2)
    ax.text(scale_x0 + scale_len_deg / 2, scale_y - 0.20, "100 km",
            fontsize=8, ha="center", va="top", color="#111", fontweight="bold")


def draw_card(ax, site, color, accent):
    ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)

    ax.add_patch(FancyBboxPatch((0.5, 1), 99, 98,
        boxstyle="round,pad=0.5,rounding_size=2",
        linewidth=1, edgecolor="#e0e0e0", facecolor="#fdfdfd", zorder=1))
    ax.add_patch(mpatches.Rectangle((0.5, 1), 2.2, 98,
        facecolor=color, edgecolor="none", zorder=2))

    ax.text(5.5, 87, site["name"], fontsize=16, fontweight="bold",
            color="#111", va="center")
    notes = (site.get("notes") or "").split(".")[0]
    ax.text(5.5, 75, notes, fontsize=9.5, color="#666", va="center", style="italic")

    metrics = [
        ("NDVI",   site["landsat_ndvi_trend"], site["landsat_ndvi_p"],
         site["landsat_ndvi_slope_per_yr"], "40-yr Landsat"),
        ("NDMI",   site["landsat_ndmi_trend"], site["landsat_ndmi_p"],
         site["landsat_ndmi_slope_per_yr"], "40-yr Landsat"),
        ("NDWI",   site["landsat_ndwi_trend"], site["landsat_ndwi_p"],
         site["landsat_ndwi_slope_per_yr"], "40-yr Landsat"),
        ("SAR VV", site.get("sar_vv_trend", "-"), site.get("sar_vv_p", 1.0),
         site.get("sar_vv_slope_dB_per_yr", 0.0), "10-yr Sentinel-1"),
    ]
    col_x = [7, 30, 53, 76]
    for (label, trend, p, slope, source), x0 in zip(metrics, col_x):
        ax.text(x0, 59, label, fontsize=10, fontweight="bold", color="#333", va="center")
        ax.text(x0, 52.5, source, fontsize=7.5, color="#999", va="center")

        sig = p < 0.05
        cc = _cell_color(trend, p)
        weight = "bold" if sig else "normal"
        arrow_size = 22 if sig else 18
        ax.text(x0, 37, _arrow(trend), fontsize=arrow_size, color=cc,
                va="center", fontweight="bold")
        ax.text(x0 + 5.5, 37, trend, fontsize=10.5, color=cc,
                va="center", fontweight=weight)
        ax.text(x0, 22, f"p = {p:.3f}", fontsize=8.5, color="#555", va="center")
        slope_units = " dB/yr" if label == "SAR VV" else " /yr"
        ax.text(x0, 15, f"slope: {slope:+.4f}{slope_units}",
                fontsize=8, color="#777", va="center", family="monospace")

    story = site.get("story", "")
    ax.add_patch(FancyBboxPatch((5, 2), 92, 7,
        boxstyle="round,pad=0.3,rounding_size=1.2",
        linewidth=0, facecolor=accent, edgecolor="none", zorder=2))
    ax.text(6.5, 5.5, "Story:", fontsize=9, fontweight="bold", color=color, va="center")
    ax.text(14, 5.5, story, fontsize=9, color="#333", va="center", style="italic")


def main() -> None:
    sites = gpd.read_file(SITES_GEOJSON)
    oregon = load_oregon()
    if oregon.crs is None:
        oregon.set_crs(4326, inplace=True)
    sites_by_slug = {row["slug"]: row for _, row in sites.iterrows()}

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(17, 10.5), facecolor="white")
    gs = GridSpec(2, 2, figure=fig,
                  width_ratios=[0.55, 1], height_ratios=[0.11, 1],
                  wspace=0.05, hspace=0.05,
                  left=0.03, right=0.97, top=0.97, bottom=0.04)

    # Header
    ax_h = fig.add_subplot(gs[0, :]); ax_h.axis("off")
    ax_h.set_xlim(0, 1); ax_h.set_ylim(0, 1)
    ax_h.text(0.005, 0.62, "ONDA Riparian 2026",
              fontsize=26, fontweight="bold", color="#111", va="center")
    ax_h.text(0.29, 0.70,
              "Three sites  \u00B7  two sensors  \u00B7  one 40-year record",
              fontsize=15, color="#333", va="center", style="italic")
    ax_h.text(0.005, 0.15,
              "A 2026 rebuild of a 2018 volunteer GIS project for the Oregon Natural Desert "
              "Association  \u00B7  Landsat 1984\u20132025  \u00B7  Sentinel-1 SAR 2015\u20132024",
              fontsize=10.5, color="#666", va="center")
    ax_h.plot([0, 1], [0.02, 0.02], color="#c0c0c0", lw=1, clip_on=False)

    # Map
    ax_map = fig.add_subplot(gs[1, 0])
    draw_map(ax_map, sites, oregon, sites_by_slug)

    # Cards
    gs_cards = gs[1, 1].subgridspec(3, 1, hspace=0.17)
    for i, slug in enumerate(DISPLAY_ORDER):
        ax_card = fig.add_subplot(gs_cards[i, 0])
        draw_card(ax_card, sites_by_slug[slug], SITE_COLORS[slug], STORY_ACCENT[slug])

    fig.text(0.62, 0.015,
             "Bold arrows = statistically significant (p < 0.05).  "
             "\u25B2 = increasing, \u25BC = decreasing, \u25CF = no trend.  "
             "Green = greening or wetting, red = drying, brown = mixed significance.",
             fontsize=8.5, color="#666", va="center", ha="center", style="italic")

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
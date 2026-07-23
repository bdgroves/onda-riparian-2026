---
title: "Revisiting a 2018 desert-riparian volunteer project, eight years later"
subtitle: "What changes when you rebuild a Google Earth Engine JavaScript prototype as a modern Python remote-sensing pipeline"
date: 2026-07-24
draft: true
tags: [remote-sensing, gis, onda, oregon, landsat, earth-engine, python]
category: field-report
---

## The project

In spring 2018 I was finishing a GIS certificate at the University of Washington
and cold-emailed the [Oregon Natural Desert Association](https://onda.org) asking
if they had any volunteer GIS work. Their riparian restoration coordinator, Jefferson
Jacobs, wrote back with two projects. One involved Oregon Department of Transportation
right-of-way analysis. The other was to use the (then relatively new) Google Earth
Engine platform to compute NDVI — the Normalized Difference Vegetation Index — for
three drainages in eastern Oregon where ONDA had been doing restoration work: **Hay
Creek**, **Pine Creek**, and the **South Fork of the Crooked River**.

The idea behind the NDVI work is elegant. Eastern Oregon in late summer is dry.
No rain from mid-July through early September in most years. So any plant that
is still green in August has to be pulling water from somewhere — and in these
drainages, "somewhere" almost always means a shallow groundwater aquifer connected
to the creek. Map the green pixels in August, and you've mapped the shape of the
functional groundwater system. Do it every year, and you can watch groundwater
extent expand or contract in response to restoration work: beaver dam analogs,
riparian plantings, channel-plug-and-pond, grazing exclusion.

I got a prototype working in the GEE Code Editor by fall 2018. NAIP imagery,
NDVI computed per pixel, average NDVI over each drainage. A screenshot of Pine
Creek was the deliverable. Jefferson was happy. I moved on to other work.

That was eight years ago.

## What's changed since 2018

A lot, as it turns out. In no particular order:

- **Google killed Fusion Tables** in December 2019. The three drainage polygons
  were stored there. Gone.
- **The GEE ecosystem grew up.** The JavaScript Code Editor is still fine for
  quick looks, but the Python API + [`geemap`](https://geemap.org) is now the
  standard for anything reproducible.
- **Landsat Collection 2** replaced Collection 1 in 2021, with better geometric
  and radiometric calibration back to 1984.
- **Sentinel-2** started producing usable imagery in 2016 — 10 m resolution
  versus Landsat's 30 m, which actually resolves the narrow green strips along
  eastern Oregon creeks instead of smearing them into mixed pixels.
- **Sentinel-1** (C-band SAR, all-weather, 2015→) makes it feasible to check
  optical results against a completely independent sensor.
- **`pymannkendall`** and **`ruptures`** turned trend testing and change-point
  detection into two-line imports.
- **NDMI** (Normalized Difference Moisture Index) turned out to be a better
  index for the actual question we were asking. NDVI measures greenness; NDMI
  uses the shortwave-infrared band to measure leaf water content, which is a
  more direct signal for the "is this plant tapping groundwater" question.

## The rebuild

The 2026 version lives at
[github.com/brooksgroves/onda-riparian-2026](https://github.com/brooksgroves/onda-riparian-2026).
It has:

- A **Python package** (`onda`) with modules for site loading, composite
  building, index computation, trend testing, and plotting. All lazy imports,
  full docstrings, and the pure-python modules are unit-tested.
- **Five notebooks** covering site setup, Landsat 1984→present, Sentinel-2
  fine-scale, Sentinel-1 SAR moisture, and pixel-level change detection.
- A **Streamlit dashboard** for the pick-a-site pick-an-index-and-look use case.
- **Study sites as USGS HUC10 codes** rather than Fusion Tables, so anyone can
  reproduce the exact site boundaries from a public, versioned source.
- **CI** on GitHub Actions running tests on every push.

## The interesting technical bits

**Cross-sensor harmonization.** Landsat 5, 7, 8, and 9 each name their bands
differently — Landsat 5 calls the near-infrared band `SR_B4`, Landsat 8 calls
it `SR_B5`. The `composites` module renames everything to a common vocabulary
(`blue`, `green`, `red`, `nir`, `swir1`, `swir2`) at the earliest possible
step, so every downstream index computation is one function that works across
all four sensors and Sentinel-2. This was the single biggest quality-of-life
improvement over the 2018 code, which had a separate branch per sensor.

**QA bit-masking.** Landsat Collection 2 Level-2 comes with a `QA_PIXEL`
band whose bits mark cloud, cloud shadow, snow, water, and dilated cloud.
The 2018 prototype ignored these; the 2026 version masks them properly. On
a bad-weather year this can be the difference between a defensible mean and
a meaningless one.

**Trend testing vs. eyeballing.** The 2018 output was a screenshot. The 2026
output is a Mann-Kendall test with a p-value and a Theil-Sen slope, so we can
distinguish "NDMI has risen 0.03 units per decade with p < 0.01" from "NDMI
wiggled around noisily and I want it to have gone up." When you're advising
a nonprofit whose funders want evidence of impact, that distinction matters.

**Change-point detection.** For each site we run a PELT algorithm to find
years at which the index series shifted regime. If a change point lands within
a couple of years of a known restoration project, that's suggestive. If it
lands 15 years before any known work, we probably need to talk to ONDA about
what else was happening in that watershed.

## What the analysis has to say (once it runs)

_This section is a placeholder. Run notebook `02_landsat_timeseries.ipynb`
against your Earth Engine account, then drop the figures and the Mann-Kendall
outputs in here. Suggested structure:_

1. **Per-site figure**: annual NDMI 1984→present with 5-yr rolling mean,
   Theil-Sen trend, and any change points and restoration events overlaid.
2. **Cross-site table**: MK trend direction, p-value, and per-decade slope for
   each of the three drainages, for NDVI, NDMI, and NDWI.
3. **One anomaly narrative**: pick the site with the largest change point and
   write two paragraphs on what happened in that year — was it fire, a
   restoration project, a drought, a flood?

## What I'd still love to add

- **Restoration project polygons.** Right now the pipeline knows *when*
  restoration happened at each site but not *where*. Getting exact
  project polygons from ONDA would let us do inside-vs-outside comparisons
  within a single watershed, which is a much cleaner test than aggregate
  watershed means.
- **LandTrendr**. Pixel-level temporal segmentation. There's a stub notebook
  ready to fill in.
- **A field trip.** Every quantitative story wants a qualitative ground-truth
  visit. Someday.

## Credit

Jefferson Jacobs framed the science question and pointed at the drainages in
2018. Everything I wrote just implements his idea.

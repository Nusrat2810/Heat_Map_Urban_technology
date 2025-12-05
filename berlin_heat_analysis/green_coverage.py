"""
Berlin Green Coverage Heatmap
Shows % green area per administrative region
Uses the same OSM boundaries and green-area calculations as priority map
"""

import osmnx as ox
import geopandas as gpd
import pandas as pd
import folium
import branca.colormap as cm
from shapely.geometry import mapping
from rapidfuzz import process

# ---------------- Load Berlin administrative areas ----------------
print("📥 Loading Berlin administrative areas...")
gdf_areas = ox.features_from_place(
    "Berlin, Germany",
    tags={"boundary": "administrative", "admin_level": "10"}
)
gdf_areas = gdf_areas[["name", "geometry"]].dropna(subset=["geometry"]).reset_index(drop=True)
gdf_areas = gdf_areas.rename(columns={"name": "area"})

# Keep only areas fully inside Berlin
berlin_boundary = ox.geocode_to_gdf("Berlin, Germany").geometry.iloc[0]
gdf_areas = gdf_areas[gdf_areas.geometry.intersects(berlin_boundary)]
gdf_areas = gdf_areas[gdf_areas.geometry.within(berlin_boundary.buffer(0.0001))]
gdf_areas = gdf_areas[gdf_areas["area"] != "Berlin"]
print(f"✅ Kept {len(gdf_areas)} areas fully inside Berlin")

# ---------------- Extract green areas ----------------
print("🌿 Fetching green areas from OSM...")
tags = {
    "leisure": ["park", "garden"],
    "landuse": ["forest", "grass", "meadow"]
}
gdf_green = ox.features_from_place("Berlin, Germany", tags)
gdf_green = gdf_green[["geometry"]].dropna().reset_index(drop=True)

# ---------------- Compute green coverage ----------------
print("📐 Calculating green coverage...")
gdf_areas = gdf_areas.to_crs(epsg=32633)
gdf_green = gdf_green.to_crs(epsg=32633)

gdf_areas["green_area"] = 0.0
for i, area in gdf_areas.iterrows():
    geom = area["geometry"]
    intersected = gdf_green[gdf_green.intersects(geom)].copy()
    if not intersected.empty:
        intersected["geometry"] = intersected["geometry"].intersection(geom)
        green_total = intersected["geometry"].area.sum()
        area_total = geom.area
        gdf_areas.at[i, "green_area"] = green_total / area_total

print("🌱 Green coverage calculation complete")

# Back to WGS84
gdf_areas = gdf_areas.to_crs(epsg=4326)

# ---------------- Create Folium map ----------------
print("🗺️ Generating Green Coverage Map...")

# Color scale: Red (low green) → Green (high green)
colormap = cm.linear.RdYlGn_11.scale(
    gdf_areas["green_area"].min(), gdf_areas["green_area"].max()
).to_step(10)
colormap.caption = "Green Coverage (%)"

# Build GeoJSON for map
features = []
for _, row in gdf_areas.iterrows():
    feature = {
        "type": "Feature",
        "geometry": mapping(row["geometry"]),
        "properties": {
            "area": row["area"],
            "green_coverage": round(row["green_area"] * 100, 2)  # convert to percent
        },
    }
    features.append(feature)

geojson = {"type": "FeatureCollection", "features": features}

# Base map
m = folium.Map(location=[52.52, 13.405], zoom_start=11, tiles="CartoDB positron")

# GeoJson layer
folium.GeoJson(
    geojson,
    style_function=lambda f: {
        "fillColor": colormap(f["properties"]["green_coverage"]/100),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.75,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["area", "green_coverage"],
        aliases=["Area", "Green Coverage (%)"],
        localize=True
    ),
    name="Green Coverage"
).add_to(m)

colormap.add_to(m)

# ---------------- Save outputs ----------------
output_map = "map/berlin_green_coverage_map.html"
output_csv = "CSV/berlin_green_coverage.csv"

m.save(output_map)
gdf_areas[["area", "green_area"]].to_csv(output_csv, index=False)

print(f"✅ Green Coverage Map saved: {output_map}")
print(f"✅ CSV saved: {output_csv}")

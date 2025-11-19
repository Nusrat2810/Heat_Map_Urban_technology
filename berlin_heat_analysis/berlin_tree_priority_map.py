"""
Tree Plantation Priority Map
Removes non-Berlin areas
Computes green coverage & temperature-based priority using median temperature baseline
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

# Keep only areas fully within Berlin
berlin_boundary = ox.geocode_to_gdf("Berlin, Germany").geometry.iloc[0]
gdf_areas = gdf_areas[gdf_areas.geometry.intersects(berlin_boundary)]
gdf_areas = gdf_areas[gdf_areas.geometry.within(berlin_boundary.buffer(0.0001))]
gdf_areas = gdf_areas[gdf_areas["area"] != "Berlin"]
print(f"✅ Kept {len(gdf_areas)} areas fully inside Berlin")

# ---------------- Load temperature data ----------------
csv_file = "H:/BHT/urban technology/urban_project/CSV/berlin_mean_temperature_by_area.csv"
df_temp = pd.read_csv(csv_file)

# Fuzzy match CSV area names to OSM areas
print("🔗 Matching CSV names to OSM area names...")
csv_areas = df_temp["area"].tolist()
osm_areas = gdf_areas["area"].tolist()

mapped_names = []
for d in csv_areas:
    best_match, score, _ = process.extractOne(d, osm_areas)
    mapped_names.append(best_match if score > 80 else None)

df_temp["area"] = mapped_names
df_temp = df_temp.dropna(subset=["area"]).reset_index(drop=True)
print(f"✅ Mapped {len(df_temp)} temperature areas")

# ---------------- Extract green areas ----------------
print("🌿 Fetching green areas from OSM...")
tags = {
    "leisure": ["park", "garden"],
    "landuse": ["forest", "grass", "meadow"]
}
gdf_green = ox.features_from_place("Berlin, Germany", tags)
gdf_green = gdf_green[["geometry"]].dropna(subset=["geometry"]).reset_index(drop=True)

# ---------------- Compute green coverage ----------------
print("📐 Calculating green coverage...")
gdf_areas = gdf_areas.to_crs(epsg=32633)
gdf_green = gdf_green.to_crs(epsg=32633)

gdf_areas["green_area"] = 0.0
for i, area in gdf_areas.iterrows():
    area_geom = area["geometry"]
    intersected = gdf_green[gdf_green.intersects(area_geom)].copy()
    if not intersected.empty:
        intersected["geometry"] = intersected["geometry"].intersection(area_geom)
        green_area_total = intersected["geometry"].area.sum()
        area_total = area_geom.area
        gdf_areas.at[i, "green_area"] = green_area_total / area_total
print("✅ Green coverage computed")

# ---------------- Merge temperature data safely ----------------
gdf_areas = gdf_areas.merge(df_temp, on="area", how="left")


# ---------------- Compute priority score using median temp and normalize ----------------
median_temp = gdf_areas["mean_temp_c"].dropna().mean()
print(f"📊 Median temperature: {median_temp:.2f} °C")

def calc_priority(row):
    temp = row["mean_temp_c"]
    green = row["green_area"]
    
    # Low priority if temp <= median
    if temp <= median_temp or pd.isna(temp):
        return 1.0
    
    # Priority increases with temperature above median, decreases with green coverage
    temp_factor = temp - median_temp
    green_factor = 1 - green  # less green → higher priority
    return temp_factor * green_factor

# Calculate raw priority scores
gdf_areas["priority_score_raw"] = gdf_areas.apply(calc_priority, axis=1)

# Normalize between 0 and 1
max_score = gdf_areas["priority_score_raw"].max()
if max_score > 0:
    gdf_areas["priority_score"] = gdf_areas["priority_score_raw"] / max_score
else:
    gdf_areas["priority_score"] = 0.0

# Drop the temporary raw score column
gdf_areas.drop(columns=["priority_score_raw"], inplace=True)

# ---------------- Back to WGS84 for Folium ----------------
gdf_areas = gdf_areas.to_crs(epsg=4326)

# ---------------- Create interactive Folium map ----------------
print("🗺️ Generating Folium map...")

# Red→Green colormap (inverse YlOrRd)
colormap = cm.linear.RdYlGn_11.scale(
    gdf_areas["priority_score"].min(), gdf_areas["priority_score"].max()
).to_step(10)
colormap.caption = "Tree Plantation Priority (Red = High)"

# Build GeoJSON features
features = []
for _, row in gdf_areas.iterrows():
    feature = {
        "type": "Feature",
        "geometry": mapping(row["geometry"]),
        "properties": {
            "area": row["area"],
            "mean_temp_c": round(row["mean_temp_c"], 2) if pd.notnull(row["mean_temp_c"]) else None,
            "green_coverage": round(row["green_area"], 3),
            "priority_score": round(row["priority_score"], 2)
        },
    }
    features.append(feature)

geojson = {"type": "FeatureCollection", "features": features}

m = folium.Map(location=[52.52, 13.405], zoom_start=11, tiles="CartoDB positron")

folium.GeoJson(
    geojson,
    style_function=lambda feature: {
        "fillColor": colormap(feature["properties"]["priority_score"]),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.75,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["area", "mean_temp_c", "green_coverage", "priority_score"],
        aliases=["Area", "Avg Temp (°C)", "Green Coverage", "Priority Score"],
        localize=True
    ),
    name="Tree Plantation Priority"
).add_to(m)

colormap.add_to(m)

# ---------------- Save results ----------------
output_map = "map/berlin_tree_priority_map.html"
output_csv = "CSV/berlin_tree_priority_scores.csv"

m.save(output_map)
gdf_areas[["area", "mean_temp_c", "green_area", "priority_score"]].to_csv(output_csv, index=False)

print(f"✅ Map saved: {output_map}")
print(f"✅ CSV saved: {output_csv}")

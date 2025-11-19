"""
Interactive Yearly Heatmap
Filters CSV for year and creates GeoJSON + Folium map
"""

import folium
import geopandas as gpd
import osmnx as ox
import pandas as pd
from shapely.geometry import mapping

# ---------------- Load Berlin areas ----------------
gdf = ox.features_from_place(
    "Berlin, Germany",
    tags={"boundary": "administrative", "admin_level": "10"}
)
gdf = gdf[["name", "geometry"]].dropna(subset=["geometry"]).reset_index(drop=True)

# Filter to only areas inside Berlin
berlin_boundary = ox.geocode_to_gdf("Berlin, Germany").geometry.iloc[0]
gdf = gdf[gdf.geometry.intersects(berlin_boundary)]
gdf = gdf[gdf.geometry.within(berlin_boundary.buffer(0.0001))]
gdf = gdf[gdf["name"] != "Berlin"]

print(f"✅ Kept {len(gdf)} polygons inside Berlin only")

# ---------------- Load temperature CSV and filter for 2020 ----------------
csv_file = "H:/BHT/urban technology/urban_project/CSV/berlin_mean_temperature_2020_2024.csv"
df_avg = pd.read_csv(csv_file)

required_year = 2020
# Filter CSV for years
df_avg_yearly = df_avg[df_avg['year'] == required_year].reset_index(drop=True)

# Map area → temperature
temp_area = dict(zip(df_avg_yearly['area'], df_avg_yearly['mean_temp_c']))

# ---------------- Build GeoJSON ----------------
features = []
for _, row in gdf.iterrows():
    area_name = row['name']
    feature = {
        "type": "Feature",
        "geometry": mapping(row['geometry']),  # convert Polygon/MultiPolygon to dict
        "properties": {
            "area": area_name,
            "mean_temp_c": temp_area.get(area_name, None)
        }
    }
    features.append(feature)

geojson = {"type": "FeatureCollection", "features": features}

# ---------------- Create Folium map ----------------
m = folium.Map(location=[52.52, 13.405], zoom_start=11)

# Add choropleth layer
folium.Choropleth(
    geo_data=geojson,
    name= f'Average Summer Temp {required_year}',
    data=df_avg_yearly,
    columns=['area', 'mean_temp_c'],
    key_on='feature.properties.area',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name= f'Avg Summer Temp (°C) - {required_year}'
).add_to(m)

# Add tooltip
folium.GeoJson(
    geojson,
    tooltip=folium.GeoJsonTooltip(
        fields=['area', 'mean_temp_c'],
        aliases=['Area', 'Avg Temp (°C)'],
        localize=True
    )
).add_to(m)

# ---------------- Save map ----------------
output_file = f"map/berlin_avg_summer_temp_map_{required_year}.html"
m.save(output_file)
print(f"✅ Interactive {required_year} map saved as '{output_file}'")

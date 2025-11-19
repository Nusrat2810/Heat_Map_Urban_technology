"""
Interective Heatmap using folium
create Geojson and save created map
"""


import folium
import geopandas as gpd
import osmnx as ox
import pandas as pd
import json
from shapely.geometry import mapping

# Load Berlin areas
gdf = ox.features_from_place(
    "Berlin, Germany",
    tags={"boundary": "administrative", "admin_level": "10"}
)
gdf = gdf[["name", "geometry"]].dropna(subset=["geometry"]).reset_index(drop=True)

# Filter to only areas *inside* Berlin
berlin_boundary = ox.geocode_to_gdf("Berlin, Germany").geometry.iloc[0]
gdf = gdf[gdf.geometry.intersects(berlin_boundary)]
gdf = gdf[gdf.geometry.within(berlin_boundary.buffer(0.0001))]
gdf = gdf[gdf["name"] != "Berlin"]

print(f"✅ Kept {len(gdf)} polygons inside Berlin only")

# Load temperature CSV
df_avg = pd.read_csv("H:/BHT/urban technology/urban_project/CSV/berlin_mean_temperature_by_area.csv")
temp_area = dict(zip(df_avg['area'], df_avg['mean_temp_c']))

# Manually build GeoJSON with area and mean_temp_c in properties
features = []
for _, row in gdf.iterrows():
    area_name = row['name']
    feature = {
        "type": "Feature",
        "geometry": mapping(row['geometry']),  #convert Polygon/MultiPolygon to dict
        "properties": {
            "area": area_name,
            "mean_temp_c": temp_area.get(area_name, None)
        }
    }
    features.append(feature)

geojson = {"type": "FeatureCollection", "features": features}

# Create Folium map
m = folium.Map(location=[52.52, 13.405], zoom_start=10)

# Add choropleth
folium.Choropleth(
    geo_data=geojson,
    name='Average Summer Temp',
    data=df_avg,
    columns=['area', 'mean_temp_c'],
    key_on='feature.properties.area',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name='Avg Summer Temp (°C)'
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

# Save map
output_file = "map/berlin_avg_summer_temp_map.html"
m.save(output_file)
print(f"✅ Interactive map saved as '{output_file}'")

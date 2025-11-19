"""
Berlin 2020 - 2024 (June to August)
computes average summer temperature per area
and saves results as CSV
"""

import ee
import geopandas as gpd
import osmnx as ox
import pandas as pd
import requests
from shapely.geometry import shape, mapping

ee.Initialize(project='testing-project-352109')

# Load Berlin districts via OSMnx
print("📥 Downloading Berlin Area boundaries...")
gdf = ox.features_from_place(
    "Berlin, Germany",
    tags={"boundary": "administrative", "admin_level": "10"}
)

# Keep only name + geometry columns
gdf = gdf[["name", "geometry"]].dropna(subset=["geometry"]).reset_index(drop=True)
print(f"✅ Loaded {len(gdf)} Areas")

# Define MODIS dataset (Land Surface Temperature)
modis = ee.ImageCollection('MODIS/061/MOD11A2')  # 8-day LST dataset (1km resolution)
scale = 1000  # meters per pixel

# Define years and months
years = list(range(2020, 2025))
summer_months = [6, 7, 8]

# Compute mean summer temperature for each area
results = []

print("🌤️ Computing average summer temperature per Area...")
for year in years:
    # Filter for June–August of this year
    start_date = f"{year}-06-01"
    end_date = f"{year}-08-31"
    images = modis.filterDate(start_date, end_date).select('LST_Day_1km')

    for idx, row in gdf.iterrows():
        geom = ee.Geometry(mapping(row.geometry))

        # Compute mean LST over the area
        mean_area = images.mean().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geom,
            scale=scale,
            maxPixels=1e13
        )

        lst_value = mean_area.get('LST_Day_1km').getInfo()

        if lst_value is not None:
            # Convert Kelvin * 0.02 to Celsius
            temp_celsius = lst_value * 0.02 - 273.15
        else:
            temp_celsius = None

        results.append({
            "area": row["name"],
            "year": year,
            "mean_temp_c": temp_celsius
        })

        print(f"{year} - {row['name']}: {temp_celsius:.2f} °C" if temp_celsius else f"{year} - {row['name']}: No data")


# Save results to CSV
df = pd.DataFrame(results)
df.to_csv("CSV/berlin_mean_temperature_2020_2024.csv", index=False)
print("\n✅ Saved results to 'berlin_mean_temperature_2020_2024.csv'")

# average across years to cvs
mean_by_area = df.groupby("area")["mean_temp_c"].mean().reset_index()
mean_by_area.to_csv("CSV/berlin_mean_temperature_by_area.csv", index=False)
print("✅ Saved yearly averages to 'berlin_mean_temperature_by_area.csv'")

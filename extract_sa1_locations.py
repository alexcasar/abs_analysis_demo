"""
Extract SA1 locations from shapefile for Victoria codes.
This script reads the shapefile and creates Sa_Location.csv with only Victoria SA1 codes
present in SexAgeIncome_Vic.
"""

import geopandas as gpd
import pandas as pd
import os

# File paths
SHAPEFILE_PATH = "Raw/Locs/SA1_2021_AUST_GDA2020.shp"
SA_PATH = "Raw/Sa_Hours.csv"
OUTPUT_PATH = "Processed/Sa_Location.csv"

def extract_sa1_locations():
    """Extract SA1 locations for Victoria codes"""
    print("Loading shapefile...")
    # Read the shapefile
    gdf = gpd.read_file(SHAPEFILE_PATH)

    print(f"Shapefile loaded with {len(gdf)} records")
    print(f"Columns: {gdf.columns.tolist()}")

    # Read the file to get Victoria SA1 codes
    print("\nLoading SexAgeIncome_Vic to get Victoria SA1 codes...")
    df_income = pd.read_csv(SA_PATH)

    # The first column contains SA1 codes
    sa1_codes_vic = df_income.iloc[:, 0].astype(str).tolist()
    print(f"Found {len(sa1_codes_vic)} SA1 codes in Sa_Hours")

    # Filter shapefile to only include Victoria SA1 codes
    # The SA1 code field might be named differently in the shapefile
    # Common names: 'SA1_CODE21', 'SA1_CODE', 'SA1_MAIN21', etc.
    sa1_field = None
    for col in gdf.columns:
        if 'SA1' in col.upper() and 'CODE' in col.upper():
            sa1_field = col
            break

    if sa1_field is None:
        print("Available columns:", gdf.columns.tolist())
        raise ValueError("Could not find SA1 code field in shapefile")

    print(f"Using SA1 field: {sa1_field}")

    # Convert to string for matching
    gdf[sa1_field] = gdf[sa1_field].astype(str)

    # Filter for Victoria codes
    gdf_vic = gdf[gdf[sa1_field].isin(sa1_codes_vic)].copy()
    print(f"Filtered to {len(gdf_vic)} Victoria SA1 areas")

    # Calculate centroids for point locations
    gdf_vic['centroid'] = gdf_vic.geometry.centroid
    gdf_vic['longitude'] = gdf_vic['centroid'].x
    gdf_vic['latitude'] = gdf_vic['centroid'].y

    # Also keep the full geometry in WKT format
    gdf_vic['geometry_wkt'] = gdf_vic.geometry.to_wkt()

    # Calculate area in square kilometers
    # Convert to a projected CRS for accurate area calculation
    gdf_vic_projected = gdf_vic.to_crs('EPSG:3857')  # Web Mercator
    gdf_vic['area_km2'] = gdf_vic_projected.geometry.area / 1_000_000

    # Create output dataframe
    output_df = pd.DataFrame({
        'SA1_CODE': gdf_vic[sa1_field],
        'latitude': gdf_vic['latitude'],
        'longitude': gdf_vic['longitude'],
        'area_km2': gdf_vic['area_km2'],
    })

    # Save to CSV
    output_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSa_Location.csv created with {len(output_df)} records")
    print(f"Sample records:")
    print(output_df.head())

    return output_df

if __name__ == "__main__":
    extract_sa1_locations()

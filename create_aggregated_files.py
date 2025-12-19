"""
Create pre-aggregated files at Postcode and Suburb levels.
This avoids on-the-fly aggregation in the Streamlit app for better performance.
"""

import pandas as pd
import numpy as np
import os
from aggregation_utils import aggregate_to_postcode, aggregate_to_suburb, prepare_sa1_with_bounds


def aggregate_master_to_postcode(sa_master_df):
    """Aggregate Sa_Master (raw counts) to Postcode level"""
    # Filter out rows without postcode
    df = sa_master_df.dropna(subset=['postcode']).copy()

    # Identify which columns to sum (all numeric columns except lat/lon/area)
    exclude_cols = ['SA1', 'latitude', 'longitude', 'area_km2', 'postcode', 'suburb']
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    sum_cols = [col for col in numeric_cols if col not in exclude_cols]

    # Create aggregation dict
    agg_dict = {
        'latitude': 'mean',
        'longitude': 'mean',
        'area_km2': 'sum'
    }
    for col in sum_cols:
        agg_dict[col] = 'sum'

    # Aggregate
    aggregated = df.groupby('postcode').agg(agg_dict).reset_index()

    # Calculate geographic bounds
    bounds = df.groupby('postcode').agg({
        'latitude': ['min', 'max'],
        'longitude': ['min', 'max']
    })
    bounds.columns = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    bounds = bounds.reset_index()

    # Merge bounds
    aggregated = aggregated.merge(bounds, on='postcode', how='left')

    return aggregated


def aggregate_master_to_suburb(sa_master_df):
    """Aggregate Sa_Master (raw counts) to Suburb level"""
    # Filter out rows without suburb
    df = sa_master_df.dropna(subset=['suburb']).copy()

    # Identify which columns to sum (all numeric columns except lat/lon/area)
    exclude_cols = ['SA1', 'latitude', 'longitude', 'area_km2', 'postcode', 'suburb']
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    sum_cols = [col for col in numeric_cols if col not in exclude_cols]

    # Create aggregation dict
    agg_dict = {
        'latitude': 'mean',
        'longitude': 'mean',
        'area_km2': 'sum'
    }
    for col in sum_cols:
        agg_dict[col] = 'sum'

    # Aggregate
    aggregated = df.groupby('suburb').agg(agg_dict).reset_index()

    # Calculate geographic bounds
    bounds = df.groupby('suburb').agg({
        'latitude': ['min', 'max'],
        'longitude': ['min', 'max']
    })
    bounds.columns = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    bounds = bounds.reset_index()

    # Merge bounds
    aggregated = aggregated.merge(bounds, on='suburb', how='left')

    return aggregated


def main():
    print("Creating pre-aggregated files...")

    # Create output directories
    os.makedirs("Processed/Postcode", exist_ok=True)
    os.makedirs("Processed/Suburb", exist_ok=True)

    # Load SA1 master data (for Master aggregations with raw counts)
    print("Loading Sa_Master.csv...")
    sa_master = pd.read_csv("Processed/Sa_Master.csv")
    print(f"  Loaded {len(sa_master)} SA1 records with {len(sa_master.columns)} columns")

    # Load SA1 processed data (for Processed aggregations with calculated stats)
    print("Loading Sa_Master_Processed.csv...")
    sa_processed = pd.read_csv("Processed/Sa_Master_Processed.csv")
    print(f"  Loaded {len(sa_processed)} SA1 records with {len(sa_processed.columns)} columns")

    # Create SA1 with bounds (for consistency with aggregated data)
    print("\nPreparing SA1 data with bounds...")
    sa1_with_bounds = prepare_sa1_with_bounds(sa_processed)
    output_path = "Processed/Sa1_Processed_WithBounds.csv"
    sa1_with_bounds.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(sa1_with_bounds)}, Columns: {len(sa1_with_bounds.columns)}")

    # ===== POSTCODE LEVEL =====
    print("\n" + "="*50)
    print("POSTCODE LEVEL AGGREGATION")
    print("="*50)

    # Aggregate Master (raw counts)
    print("\nAggregating Postcode_Master.csv (raw counts)...")
    postcode_master = aggregate_master_to_postcode(sa_master)
    output_path = "Processed/Postcode/Postcode_Master.csv"
    postcode_master.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(postcode_master)}, Columns: {len(postcode_master.columns)}")

    # Aggregate Processed (calculated stats)
    print("\nAggregating Postcode_Processed.csv (calculated stats)...")
    postcode_processed = aggregate_to_postcode(sa_processed)
    output_path = "Processed/Postcode/Postcode_Processed.csv"
    postcode_processed.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(postcode_processed)}, Columns: {len(postcode_processed.columns)}")
    print(f"  Unique postcodes: {postcode_processed['postcode'].nunique()}")

    # ===== SUBURB LEVEL =====
    print("\n" + "="*50)
    print("SUBURB LEVEL AGGREGATION")
    print("="*50)

    # Aggregate Master (raw counts)
    print("\nAggregating Suburb_Master.csv (raw counts)...")
    suburb_master = aggregate_master_to_suburb(sa_master)
    output_path = "Processed/Suburb/Suburb_Master.csv"
    suburb_master.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(suburb_master)}, Columns: {len(suburb_master.columns)}")

    # Aggregate Processed (calculated stats)
    print("\nAggregating Suburb_Processed.csv (calculated stats)...")
    suburb_processed = aggregate_to_suburb(sa_processed)
    output_path = "Processed/Suburb/Suburb_Processed.csv"
    suburb_processed.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(suburb_processed)}, Columns: {len(suburb_processed.columns)}")
    print(f"  Unique suburbs: {suburb_processed['suburb'].nunique()}")

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print("All aggregated files created successfully!")
    print("\nGenerated files:")
    print("  - Processed/Sa1_Processed_WithBounds.csv")
    print("  - Processed/Postcode/Postcode_Master.csv")
    print("  - Processed/Postcode/Postcode_Processed.csv")
    print("  - Processed/Suburb/Suburb_Master.csv")
    print("  - Processed/Suburb/Suburb_Processed.csv")


if __name__ == "__main__":
    main()

"""
Create percentage-based master files (per capita distributions)
This converts raw counts to percentages for better comparison across areas
"""

import pandas as pd
import numpy as np
import os


def create_sa_master_pct():
    """Create Sa_Master_Pct.csv with percentage distributions"""
    print("Creating Sa_Master_Pct.csv...")

    # Load master file
    master = pd.read_csv("Processed/Sa_Master.csv")
    print(f"  Loaded {len(master)} SA1 records with {len(master.columns)} columns")

    # Identify the total population column
    total_pop_col = 'age_Total'

    if total_pop_col not in master.columns:
        raise ValueError(f"Total population column '{total_pop_col}' not found!")

    # Create percentage dataframe
    master_pct = master.copy()

    # Identify count columns to convert to percentages
    # These are numeric columns that represent counts (not lat/lon/area)
    exclude_cols = ['SA1', 'latitude', 'longitude', 'area_km2', 'postcode', 'suburb']

    # Get all numeric columns
    numeric_cols = master.select_dtypes(include=[np.number]).columns
    count_cols = [col for col in numeric_cols if col not in exclude_cols]

    print(f"  Converting {len(count_cols)} count columns to percentages...")

    # Convert counts to percentages
    for col in count_cols:
        # Divide by total population and multiply by 100
        # Use the appropriate total column for each category
        if col.startswith('age_'):
            denominator = master['age_Total']
        elif col.startswith('country_'):
            denominator = master['country_Total']
        elif col.startswith('income_'):
            denominator = master['income_Total']
        elif col.startswith('hours_'):
            denominator = master['hours_Total']
        elif col.startswith('households_'):
            # For households, use age_Total (total population)
            denominator = master['age_Total']
        elif col.startswith('counthealth_') or col.startswith('typehealth_'):
            # For health, use age_Total (total population)
            denominator = master['age_Total']
        else:
            # Default to age_Total
            denominator = master['age_Total']

        # Calculate percentage, handling division by zero
        master_pct[col] = (master[col] / denominator.replace(0, np.nan)) * 100

    # Save percentage file
    output_path = "Processed/Sa_Master_Pct.csv"
    master_pct.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(master_pct)}, Columns: {len(master_pct.columns)}")
    print()

    return master_pct


def create_country_master_pct():
    """Create Country_Master_Pct.csv with percentage distributions"""
    print("Creating Country_Master_Pct.csv...")

    # Load master file
    master = pd.read_csv("Processed/Country_Master.csv")
    print(f"  Loaded {len(master)} countries with {len(master.columns)} columns")

    # Create percentage dataframe
    master_pct = master.copy()

    # Identify count columns to convert to percentages
    exclude_cols = ['Country']

    # Get all numeric columns
    numeric_cols = master.select_dtypes(include=[np.number]).columns
    count_cols = [col for col in numeric_cols if col not in exclude_cols]

    print(f"  Converting {len(count_cols)} count columns to percentages...")

    # For country data, each category has its own total
    for col in count_cols:
        # Determine the appropriate total column
        if col.startswith('education_'):
            denominator = master['education_Total']
        elif col.startswith('income_'):
            denominator = master['income_Total']
        elif col.startswith('hours_'):
            denominator = master['hours_Total']
        else:
            # Try to find a matching Total column
            prefix = col.split('_')[0]
            total_col = f'{prefix}_Total'
            if total_col in master.columns:
                denominator = master[total_col]
            else:
                print(f"  Warning: No total column found for {col}, skipping")
                continue

        # Calculate percentage
        master_pct[col] = (master[col] / denominator.replace(0, np.nan)) * 100

    # Save percentage file
    output_path = "Processed/Country_Master_Pct.csv"
    master_pct.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(master_pct)}, Columns: {len(master_pct.columns)}")
    print()

    return master_pct


def aggregate_pct_to_postcode(sa_master_pct):
    """Aggregate percentage data to postcode level"""
    print("Aggregating to Postcode_Master_Pct.csv...")

    # Filter out rows without postcode
    df_pct = sa_master_pct.dropna(subset=['postcode']).copy()

    # Load the count data to use as weights
    sa_master = pd.read_csv("Processed/Sa_Master.csv")
    sa_master = sa_master.dropna(subset=['postcode'])

    # Merge pct and count data on SA1 to ensure proper alignment
    merged = df_pct.merge(sa_master, on='SA1', suffixes=('_pct', '_count'))

    # Identify percentage columns (exclude metadata)
    exclude_cols = ['SA1', 'latitude', 'longitude', 'area_km2', 'postcode', 'suburb']
    pct_cols = [col for col in df_pct.columns if col not in exclude_cols and df_pct[col].dtype in [np.float64, np.int64]]

    # Create result dataframe with metadata (use postcode from pct side) - keep as grouped
    result = merged.groupby('postcode_pct').agg({
        'latitude_pct': 'mean',
        'longitude_pct': 'mean',
        'area_km2_pct': 'sum'
    })

    # For each percentage column, recalculate percentage from counts
    for col in pct_cols:
        if f'{col}_count' in merged.columns:
            # Determine the appropriate denominator (total) for this column type
            if col.startswith('age_'):
                denominator_col = 'age_Total_count'
            elif col.startswith('country_'):
                denominator_col = 'country_Total_count'
            elif col.startswith('income_'):
                denominator_col = 'income_Total_count'
            elif col.startswith('hours_'):
                denominator_col = 'hours_Total_count'
            elif col.startswith('households_') or col.startswith('counthealth_') or col.startswith('typehealth_'):
                denominator_col = 'age_Total_count'
            else:
                denominator_col = 'age_Total_count'

            if denominator_col in merged.columns:
                # Recalculate percentage: sum(count) / sum(total) * 100 for each postcode
                grouped_numerator = merged.groupby('postcode_pct')[f'{col}_count'].sum()
                grouped_denominator = merged.groupby('postcode_pct')[denominator_col].sum()
                result[col] = (grouped_numerator / grouped_denominator.replace(0, np.nan)) * 100
            else:
                # Fallback to simple average if denominator not available
                result[col] = merged.groupby('postcode_pct')[f'{col}_pct'].mean()
        else:
            # Simple average if no count data available
            result[col] = merged.groupby('postcode_pct')[f'{col}_pct'].mean()

    # Now reset index and rename columns
    result = result.reset_index()
    result.rename(columns={
        'postcode_pct': 'postcode',
        'latitude_pct': 'latitude',
        'longitude_pct': 'longitude',
        'area_km2_pct': 'area_km2'
    }, inplace=True)

    # Calculate geographic bounds
    bounds = merged.groupby('postcode_pct').agg({
        'latitude_pct': ['min', 'max'],
        'longitude_pct': ['min', 'max']
    })
    bounds.columns = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    bounds = bounds.reset_index()
    bounds.rename(columns={'postcode_pct': 'postcode'}, inplace=True)

    result = result.merge(bounds, on='postcode', how='left')

    output_path = "Processed/Postcode/Postcode_Master_Pct.csv"
    result.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(result)}, Columns: {len(result.columns)}")
    print()

    return result


def aggregate_pct_to_suburb(sa_master_pct):
    """Aggregate percentage data to suburb level"""
    print("Aggregating to Suburb_Master_Pct.csv...")

    # Filter out rows without suburb
    df_pct = sa_master_pct.dropna(subset=['suburb']).copy()

    # Load the count data to use as weights
    sa_master = pd.read_csv("Processed/Sa_Master.csv")
    sa_master = sa_master.dropna(subset=['suburb'])

    # Merge pct and count data on SA1 to ensure proper alignment
    merged = df_pct.merge(sa_master, on='SA1', suffixes=('_pct', '_count'))

    # Identify percentage columns
    exclude_cols = ['SA1', 'latitude', 'longitude', 'area_km2', 'postcode', 'suburb']
    pct_cols = [col for col in df_pct.columns if col not in exclude_cols and df_pct[col].dtype in [np.float64, np.int64]]

    # Create result dataframe with metadata (use suburb from pct side) - keep as grouped
    result = merged.groupby('suburb_pct').agg({
        'latitude_pct': 'mean',
        'longitude_pct': 'mean',
        'area_km2_pct': 'sum'
    })

    # For each percentage column, recalculate percentage from counts
    for col in pct_cols:
        if f'{col}_count' in merged.columns:
            # Determine the appropriate denominator (total) for this column type
            if col.startswith('age_'):
                denominator_col = 'age_Total_count'
            elif col.startswith('country_'):
                denominator_col = 'country_Total_count'
            elif col.startswith('income_'):
                denominator_col = 'income_Total_count'
            elif col.startswith('hours_'):
                denominator_col = 'hours_Total_count'
            elif col.startswith('households_') or col.startswith('counthealth_') or col.startswith('typehealth_'):
                denominator_col = 'age_Total_count'
            else:
                denominator_col = 'age_Total_count'

            if denominator_col in merged.columns:
                # Recalculate percentage: sum(count) / sum(total) * 100 for each suburb
                grouped_numerator = merged.groupby('suburb_pct')[f'{col}_count'].sum()
                grouped_denominator = merged.groupby('suburb_pct')[denominator_col].sum()
                result[col] = (grouped_numerator / grouped_denominator.replace(0, np.nan)) * 100
            else:
                # Fallback to simple average if denominator not available
                result[col] = merged.groupby('suburb_pct')[f'{col}_pct'].mean()
        else:
            # Simple average if no count data available
            result[col] = merged.groupby('suburb_pct')[f'{col}_pct'].mean()

    # Now reset index and rename columns
    result = result.reset_index()
    result.rename(columns={
        'suburb_pct': 'suburb',
        'latitude_pct': 'latitude',
        'longitude_pct': 'longitude',
        'area_km2_pct': 'area_km2'
    }, inplace=True)

    # Calculate geographic bounds
    bounds = merged.groupby('suburb_pct').agg({
        'latitude_pct': ['min', 'max'],
        'longitude_pct': ['min', 'max']
    })
    bounds.columns = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    bounds = bounds.reset_index()
    bounds.rename(columns={'suburb_pct': 'suburb'}, inplace=True)

    result = result.merge(bounds, on='suburb', how='left')

    output_path = "Processed/Suburb/Suburb_Master_Pct.csv"
    result.to_csv(output_path, index=False)
    print(f"  Saved {output_path}")
    print(f"  Records: {len(result)}, Columns: {len(result.columns)}")
    print()

    return result


def main():
    print("=" * 60)
    print("CREATING PERCENTAGE-BASED MASTER FILES")
    print("=" * 60)
    print()

    # Create percentage files
    sa_master_pct = create_sa_master_pct()
    country_master_pct = create_country_master_pct()

    # Create aggregated percentage files
    postcode_pct = aggregate_pct_to_postcode(sa_master_pct)
    suburb_pct = aggregate_pct_to_suburb(sa_master_pct)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("All percentage files created successfully!")
    print("\nGenerated files:")
    print("  - Processed/Sa_Master_Pct.csv")
    print("  - Processed/Country_Master_Pct.csv")
    print("  - Processed/Postcode/Postcode_Master_Pct.csv")
    print("  - Processed/Suburb/Suburb_Master_Pct.csv")


if __name__ == "__main__":
    main()

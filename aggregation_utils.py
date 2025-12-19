"""
Utility functions for aggregating SA1 data to Postcode and Suburb levels
"""

import pandas as pd
import numpy as np


def aggregate_to_postcode(sa_processed_df):
    """
    Aggregate SA1-level data to Postcode level

    Args:
        sa_processed_df: DataFrame with SA1-level processed data

    Returns:
        DataFrame aggregated by postcode with geographic bounds
    """
    # Filter out rows without postcode
    df = sa_processed_df.dropna(subset=['postcode']).copy()

    # Define aggregation rules
    agg_dict = {
        'latitude': 'mean',  # Center point
        'longitude': 'mean',
        'area_km2': 'sum',
        'total_population': 'sum',
        'pop_0_14': 'sum',
        'pop_15_24': 'sum',
        'pop_25_54': 'sum',
        'pop_55_64': 'sum',
        'pop_65_plus': 'sum',
        'total_income_earners': 'sum',
        'total_workers': 'sum',
    }

    # Aggregate
    aggregated = df.groupby('postcode').agg(agg_dict)

    # Recalculate weighted averages
    # For avg_age, avg_income, avg_hours_worked - need to recalculate from totals
    if 'total_population' in df.columns and 'avg_age' in df.columns:
        weighted_age = (df['avg_age'] * df['total_population']).groupby(df['postcode']).sum()
        total_pop = df.groupby('postcode')['total_population'].sum()
        aggregated['avg_age'] = weighted_age / total_pop.replace(0, np.nan)

    if 'total_income_earners' in df.columns and 'avg_income' in df.columns:
        weighted_income = (df['avg_income'] * df['total_income_earners']).groupby(df['postcode']).sum()
        total_earners = df.groupby('postcode')['total_income_earners'].sum()
        aggregated['avg_income'] = weighted_income / total_earners.replace(0, np.nan)

    if 'total_workers' in df.columns and 'avg_hours_worked' in df.columns:
        weighted_hours = (df['avg_hours_worked'] * df['total_workers']).groupby(df['postcode']).sum()
        total_workers = df.groupby('postcode')['total_workers'].sum()
        aggregated['avg_hours_worked'] = weighted_hours / total_workers.replace(0, np.nan)

    # Reset index to make postcode a column
    aggregated = aggregated.reset_index()

    # Calculate population density
    aggregated['population_density'] = aggregated['total_population'] / aggregated['area_km2'].replace(0, np.nan)

    # Calculate hourly wage
    if 'avg_income' in aggregated.columns and 'avg_hours_worked' in aggregated.columns:
        annual_hours = aggregated['avg_hours_worked'] * 52
        aggregated['hourly_wage'] = aggregated['avg_income'] / annual_hours.replace(0, np.nan)

    # Calculate geographic bounds (min/max lat/lon for each postcode)
    bounds = df.groupby('postcode').agg({
        'latitude': ['min', 'max'],
        'longitude': ['min', 'max']
    })
    bounds.columns = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    bounds = bounds.reset_index()

    # Merge bounds
    aggregated = aggregated.merge(bounds, on='postcode', how='left')

    # Add identifier column
    aggregated['id'] = aggregated['postcode'].astype(str)
    aggregated['level'] = 'Postcode'

    return aggregated


def aggregate_to_suburb(sa_processed_df):
    """
    Aggregate SA1-level data to Suburb level

    Args:
        sa_processed_df: DataFrame with SA1-level processed data

    Returns:
        DataFrame aggregated by suburb with geographic bounds
    """
    # Filter out rows without suburb
    df = sa_processed_df.dropna(subset=['suburb']).copy()

    # Define aggregation rules
    agg_dict = {
        'latitude': 'mean',  # Center point
        'longitude': 'mean',
        'area_km2': 'sum',
        'total_population': 'sum',
        'pop_0_14': 'sum',
        'pop_15_24': 'sum',
        'pop_25_54': 'sum',
        'pop_55_64': 'sum',
        'pop_65_plus': 'sum',
        'total_income_earners': 'sum',
        'total_workers': 'sum',
    }

    # Aggregate
    aggregated = df.groupby('suburb').agg(agg_dict)

    # Recalculate weighted averages
    if 'total_population' in df.columns and 'avg_age' in df.columns:
        weighted_age = (df['avg_age'] * df['total_population']).groupby(df['suburb']).sum()
        total_pop = df.groupby('suburb')['total_population'].sum()
        aggregated['avg_age'] = weighted_age / total_pop.replace(0, np.nan)

    if 'total_income_earners' in df.columns and 'avg_income' in df.columns:
        weighted_income = (df['avg_income'] * df['total_income_earners']).groupby(df['suburb']).sum()
        total_earners = df.groupby('suburb')['total_income_earners'].sum()
        aggregated['avg_income'] = weighted_income / total_earners.replace(0, np.nan)

    if 'total_workers' in df.columns and 'avg_hours_worked' in df.columns:
        weighted_hours = (df['avg_hours_worked'] * df['total_workers']).groupby(df['suburb']).sum()
        total_workers = df.groupby('suburb')['total_workers'].sum()
        aggregated['avg_hours_worked'] = weighted_hours / total_workers.replace(0, np.nan)

    # Reset index to make suburb a column
    aggregated = aggregated.reset_index()

    # Calculate population density
    aggregated['population_density'] = aggregated['total_population'] / aggregated['area_km2'].replace(0, np.nan)

    # Calculate hourly wage
    if 'avg_income' in aggregated.columns and 'avg_hours_worked' in aggregated.columns:
        annual_hours = aggregated['avg_hours_worked'] * 52
        aggregated['hourly_wage'] = aggregated['avg_income'] / annual_hours.replace(0, np.nan)

    # Calculate geographic bounds (min/max lat/lon for each suburb)
    bounds = df.groupby('suburb').agg({
        'latitude': ['min', 'max'],
        'longitude': ['min', 'max']
    })
    bounds.columns = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    bounds = bounds.reset_index()

    # Merge bounds
    aggregated = aggregated.merge(bounds, on='suburb', how='left')

    # Add identifier column
    aggregated['id'] = aggregated['suburb']
    aggregated['level'] = 'Suburb'

    return aggregated


def prepare_sa1_with_bounds(sa_processed_df):
    """
    Prepare SA1 data with bounds (for consistency with aggregated data)

    Args:
        sa_processed_df: DataFrame with SA1-level processed data

    Returns:
        DataFrame with SA1 data including bounds columns
    """
    df = sa_processed_df.copy()

    # For SA1, bounds are just the point itself (or could use a small buffer)
    # Using a small offset to create a visible area
    lat_offset = 0.005  # approximately 500m
    lon_offset = 0.005

    df['lat_min'] = df['latitude'] - lat_offset
    df['lat_max'] = df['latitude'] + lat_offset
    df['lon_min'] = df['longitude'] - lon_offset
    df['lon_max'] = df['longitude'] + lon_offset
    df['id'] = df['SA1']
    df['level'] = 'SA1'

    return df


def get_aggregated_data(sa_processed_df, level='SA1'):
    """
    Get data at the specified aggregation level

    Args:
        sa_processed_df: DataFrame with SA1-level processed data
        level: 'SA1', 'Postcode', or 'Suburb'

    Returns:
        DataFrame at the requested aggregation level
    """
    if level == 'Postcode':
        return aggregate_to_postcode(sa_processed_df)
    elif level == 'Suburb':
        return aggregate_to_suburb(sa_processed_df)
    else:  # SA1
        return prepare_sa1_with_bounds(sa_processed_df)


def create_area_shapes(df):
    """
    Create rectangular shapes from lat/lon bounds for visualization

    Args:
        df: DataFrame with lat_min, lat_max, lon_min, lon_max columns

    Returns:
        List of shape dictionaries for plotly
    """
    shapes = []
    for _, row in df.iterrows():
        if pd.notna(row['lat_min']) and pd.notna(row['lon_min']):
            shape = {
                'type': 'rect',
                'x0': row['lon_min'],
                'y0': row['lat_min'],
                'x1': row['lon_max'],
                'y1': row['lat_max'],
                'line': {'width': 1, 'color': 'rgba(0, 0, 0, 0.3)'},
                'fillcolor': 'rgba(0, 0, 0, 0)'
            }
            shapes.append(shape)
    return shapes

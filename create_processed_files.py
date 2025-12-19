"""
Create processed master files with calculated statistics.
Analyzes column names to extract numeric values and calculate meaningful statistics.
"""

import pandas as pd
import numpy as np
import re


def extract_numeric_from_range(range_str):
    """Extract median value from a range string like '$1,000-$1,249 ($52,000-$64,999)' or '20-29 hours'"""
    # Try to find annual values in parentheses first (for income)
    annual_match = re.search(r'\((\$|)[0-9,]+-(\$|)([0-9,]+)\)', range_str)
    if annual_match:
        high = annual_match.group(3).replace(',', '')
        # Also get the low value
        low_match = re.search(r'\((\$|)([0-9,]+)', range_str)
        if low_match:
            low = low_match.group(2).replace(',', '')
            return (float(low) + float(high)) / 2

    # Try to find simple range like "20-29 hours" or "$300-$399"
    simple_match = re.search(r'(\d+)-(\d+)', range_str)
    if simple_match:
        low = float(simple_match.group(1))
        high = float(simple_match.group(2))
        return (low + high) / 2

    # Try to find "or more" or "+" patterns
    or_more_match = re.search(r'(\d+).*or more', range_str, re.IGNORECASE)
    if or_more_match:
        return float(or_more_match.group(1)) * 1.25  # Estimate 25% above minimum

    # Try to find single number
    single_match = re.search(r'(\d+)', range_str)
    if single_match:
        return float(single_match.group(1))

    return None


def create_sa_master_processed():
    """Create Sa_Master_Processed.csv with calculated statistics"""
    print("Creating Sa_Master_Processed.csv...")

    # Load the master file
    master = pd.read_csv("Processed/Sa_Master.csv")
    print(f"  Loaded Sa_Master with {len(master)} rows")

    # Create processed dataframe starting with basic info
    processed = master[['SA1', 'latitude', 'longitude', 'area_km2', 'postcode', 'suburb']].copy()

    # Calculate age statistics
    print("  Calculating age statistics...")
    age_cols = [col for col in master.columns if col.startswith('age_') and col != 'age_Total']

    if age_cols:
        age_values = []
        for col in age_cols:
            age = int(col.split('_')[1]) if col.split('_')[1].isdigit() else None
            if age is not None:
                age_values.append(age)

        # Calculate weighted average age
        age_sum = master[age_cols].sum(axis=1)
        weighted_age_sum = sum(master[f'age_{age}'] * age for age in age_values if f'age_{age}' in master.columns)
        processed['avg_age'] = weighted_age_sum / age_sum.replace(0, np.nan)

        # Total population
        processed['total_population'] = master['age_Total'] if 'age_Total' in master.columns else age_sum

        # Population density (people per km2)
        processed['population_density'] = processed['total_population'] / processed['area_km2'].replace(0, np.nan)

        # Age group distributions
        processed['pop_0_14'] = master[[f'age_{i}' for i in range(15) if f'age_{i}' in master.columns]].sum(axis=1)
        processed['pop_15_24'] = master[[f'age_{i}' for i in range(15, 25) if f'age_{i}' in master.columns]].sum(axis=1)
        processed['pop_25_54'] = master[[f'age_{i}' for i in range(25, 55) if f'age_{i}' in master.columns]].sum(axis=1)
        processed['pop_55_64'] = master[[f'age_{i}' for i in range(55, 65) if f'age_{i}' in master.columns]].sum(axis=1)
        processed['pop_65_plus'] = master[[f'age_{i}' for i in range(65, 116) if f'age_{i}' in master.columns]].sum(axis=1)

    # Calculate income statistics
    print("  Calculating income statistics...")
    income_cols = [col for col in master.columns if col.startswith('income_') and
                   'Not stated' not in col and 'Not applicable' not in col and
                   'Negative' not in col and 'Nil' not in col and col != 'income_Total']

    if income_cols:
        print(f"    Found {len(income_cols)} income columns")
        total_income_earners = pd.Series(0, index=master.index)
        weighted_income = pd.Series(0.0, index=master.index)

        for col in income_cols:
            income_value = extract_numeric_from_range(col)
            if income_value:
                # Fill NaN values with 0 for calculation
                col_values = master[col].fillna(0)
                total_income_earners += col_values
                weighted_income += col_values * income_value

        processed['avg_income'] = weighted_income / total_income_earners.replace(0, np.nan)
        processed['total_income_earners'] = total_income_earners

    # Calculate hours worked statistics
    print("  Calculating hours worked statistics...")
    hours_cols = [col for col in master.columns if col.startswith('hours_') and
                  'Not stated' not in col and 'Not applicable' not in col and
                  col != 'hours_Total' and '0 hours' not in col]

    if hours_cols:
        print(f"    Found {len(hours_cols)} hours columns")
        total_workers = pd.Series(0, index=master.index)
        weighted_hours = pd.Series(0.0, index=master.index)

        for col in hours_cols:
            hours_value = extract_numeric_from_range(col)
            if hours_value:
                # Fill NaN values with 0 for calculation
                col_values = master[col].fillna(0)
                total_workers += col_values
                weighted_hours += col_values * hours_value

        processed['avg_hours_worked'] = weighted_hours / total_workers.replace(0, np.nan)
        processed['total_workers'] = total_workers

    # Calculate hourly wage (annual income / (hours per week * 52))
    if 'avg_income' in processed.columns and 'avg_hours_worked' in processed.columns:
        annual_hours = processed['avg_hours_worked'] * 52
        processed['hourly_wage'] = processed['avg_income'] / annual_hours.replace(0, np.nan)

    # Save processed file
    output_path = "Processed/Sa_Master_Processed.csv"
    processed.to_csv(output_path, index=False)
    print(f"  Saved Sa_Master_Processed.csv with {len(processed)} rows and {len(processed.columns)} columns")
    print(f"  Columns: {list(processed.columns)}")
    print()

    return processed


def create_country_master_processed():
    """Create Country_Master_Processed.csv with calculated statistics"""
    print("Creating Country_Master_Processed.csv...")

    # Load the master file
    master = pd.read_csv("Processed/Country_Master.csv")
    print(f"  Loaded Country_Master with {len(master)} rows")

    # Create processed dataframe starting with country
    processed = master[['Country']].copy()

    # Calculate income statistics
    print("  Calculating income statistics...")
    income_cols = [col for col in master.columns if col.startswith('income_') and
                   'Not stated' not in col and 'Not applicable' not in col and
                   'Negative' not in col and 'Nil' not in col and col != 'income_Total']

    if income_cols:
        total_income_earners = 0
        weighted_income = 0

        for col in income_cols:
            income_value = extract_numeric_from_range(col)
            if income_value:
                total_income_earners += master[col].fillna(0)
                weighted_income += master[col].fillna(0) * income_value

        processed['avg_income'] = weighted_income / total_income_earners.replace(0, np.nan)
        processed['total_income_earners'] = total_income_earners
        processed['median_income'] = processed['avg_income']  # Approximate median as average

    # Calculate hours worked statistics
    print("  Calculating hours worked statistics...")
    hours_cols = [col for col in master.columns if col.startswith('hours_') and
                  'Not stated' not in col and 'Not applicable' not in col and
                  col != 'hours_Total' and '0 hours' not in col]

    if hours_cols:
        total_workers = 0
        weighted_hours = 0

        for col in hours_cols:
            hours_value = extract_numeric_from_range(col)
            if hours_value:
                total_workers += master[col].fillna(0)
                weighted_hours += master[col].fillna(0) * hours_value

        processed['avg_hours_worked'] = weighted_hours / total_workers.replace(0, np.nan)
        processed['total_workers'] = total_workers

    # Calculate hourly wage
    if 'avg_income' in processed.columns and 'avg_hours_worked' in processed.columns:
        annual_hours = processed['avg_hours_worked'] * 52
        processed['hourly_wage'] = processed['avg_income'] / annual_hours.replace(0, np.nan)

    # Calculate education statistics
    print("  Calculating education statistics...")
    education_cols = [col for col in master.columns if col.startswith('education_') and
                      'Not stated' not in col and 'Not applicable' not in col and
                      col != 'education_Total']

    if education_cols:
        processed['total_with_education'] = master[education_cols].sum(axis=1)
        
        postgrad_cols = [
            "education_Postgraduate Degree Level, nfd",
            "education_Doctoral Degree Level, nfd",
            "education_Higher Doctorate",
            "education_Professional Specialist Qualification, Doctoral Degree Level",
            "education_Master Degree Level, nfd",
            "education_Graduate Diploma and Graduate Certificate Level, nfd",
            "education_Graduate Diploma",
            "education_Graduate Certificate"
        ]

        if postgrad_cols:
            processed['postgraduate_count'] = master[postgrad_cols].sum(axis=1)
            processed['postgraduate_pct'] = (processed['postgraduate_count'] /
                                            processed['total_with_education'].replace(0, np.nan)) * 100

        # Count people with bachelor degrees
        bachelor_cols = [
            "education_Bachelor Degree Level, nfd",
            "education_Advanced Diploma and Diploma Level, nfd",
            "education_Advanced Diploma",
            "education_Associate Degree"
        ]
        if bachelor_cols:
            processed['bachelor_count'] = master[bachelor_cols].sum(axis=1)
            processed['bachelor_pct'] = (processed['bachelor_count'] /
                                        processed['total_with_education'].replace(0, np.nan)) * 100
            
        pre = [
            "education_Diploma Level, nfd",
            "education_Diploma",
            "education_Certificate III & IV Level, nfd",
            "education_Certificate IV",
            "education_Certificate III",
            "education_Certificate I & II Level, nfd",
            "education_Certificate II",
            "education_Certificate I",
            "education_Year 12",
            "education_Year 11",
            "education_Year 10",
            "education_Year 9",
            "education_Year 8 or below",
            "education_Inadequately described",
            "education_No educational attainment",
            "education_Not stated",
            "education_Not applicable"
        ]

    # Save processed file
    output_path = "Processed/Country_Master_Processed.csv"
    processed.to_csv(output_path, index=False)
    print(f"  Saved Country_Master_Processed.csv with {len(processed)} rows and {len(processed.columns)} columns")
    print(f"  Columns: {list(processed.columns)}")
    print()

    return processed


def main():
    # Create processed files
    sa_processed = create_sa_master_processed()
    country_processed = create_country_master_processed()

    print("Processed files created successfully!")
    print(f"\nSa_Master_Processed preview:")
    print(sa_processed[['SA1', 'total_population', 'avg_age', 'avg_income', 'avg_hours_worked']].head())

    print(f"\nCountry_Master_Processed preview:")
    print(country_processed[['Country', 'avg_income', 'avg_hours_worked', 'hourly_wage']].head(10))


if __name__ == "__main__":
    main()

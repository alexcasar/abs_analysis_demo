"""
Create master CSV files by combining all related data sources.
- Sa_Master.csv: Combines SA1-level data with locations, postcodes, and suburbs
- Country_Master.csv: Combines country-level data
"""

import pandas as pd
import numpy as np
import os


def clean_footer_rows(df):
    """Remove footer rows containing ABS copyright and licensing info"""
    footer_keywords = [
        'Dataset:',
        'Cells in this table',
        'Copyright Commonwealth',
        'ABS data licensed',
        'INFO',
        'TableBuilder'
    ]

    # Get the first column name
    first_col = df.columns[0]

    # Filter out rows where the first column contains any footer keywords
    mask = df[first_col].astype(str).apply(
        lambda x: not any(keyword in str(x) for keyword in footer_keywords)
    )

    return df[mask].copy()


def create_sa_master():
    """Create Sa_Master.csv by combining all SA1-level data"""
    print("Creating Sa_Master.csv...")

    # Load Sa1 location data
    print("  Loading Sa1_Location.csv...")
    df_location = pd.read_csv("Processed/Sa_Location.csv")
    df_location.rename(columns={'SA1_CODE': 'SA1'}, inplace=True)
    df_location['SA1'] = df_location['SA1'].astype(str)

    # Load Sa_Postcode to map SA1 to postcodes
    print("  Loading Sa_Postcode.csv...")
    df_sa_postcode = pd.read_csv("Raw/Sa_Postcode.csv", dtype=str)
    df_sa_postcode = clean_footer_rows(df_sa_postcode)
    sa1_col = df_sa_postcode.columns[0]
    df_sa_postcode.rename(columns={sa1_col: 'SA1'}, inplace=True)

    # Find the postcode column (first column with non-zero value for each row)
    postcode_cols = df_sa_postcode.columns[1:-1]  # Exclude SA1 and Total columns

    # Create postcode mapping - find first non-zero postcode for each SA1
    def find_postcode(row):
        for col in postcode_cols:
            try:
                if pd.notna(row[col]) and float(row[col]) > 0:
                    return col.replace(', VIC', '')
            except (ValueError, TypeError):
                continue
        return None

    df_sa_postcode['postcode'] = df_sa_postcode.apply(find_postcode, axis=1)

    # Keep only SA1 and postcode
    sa_postcode_map = df_sa_postcode[['SA1', 'postcode']].copy()

    # Load Postcode_Suburb mapping
    print("  Loading Postcode_Suburb.csv...")
    df_postcode_suburb = pd.read_csv("Raw/Postcode_Suburb.csv", dtype=str)
    df_postcode_suburb = clean_footer_rows(df_postcode_suburb)
    postcode_col = df_postcode_suburb.columns[0]
    df_postcode_suburb.rename(columns={postcode_col: 'postcode_raw'}, inplace=True)

    # Clean postcode format: "3000, VIC" -> "3000"
    df_postcode_suburb['postcode'] = df_postcode_suburb['postcode_raw'].str.replace(', VIC', '', regex=False).str.strip()

    # Find the suburb column (first column with non-zero value for each row)
    suburb_cols = [col for col in df_postcode_suburb.columns if col not in ['postcode_raw', 'postcode']]

    def find_suburb(row):
        for col in suburb_cols:
            try:
                if pd.notna(row[col]) and row[col] != '0' and float(row[col]) > 0:
                    return col
            except (ValueError, TypeError):
                continue
        return None

    df_postcode_suburb['suburb'] = df_postcode_suburb.apply(find_suburb, axis=1)

    # Keep only postcode and suburb
    postcode_suburb_map = df_postcode_suburb[['postcode', 'suburb']].copy()

    # Start with location data
    master = df_location.copy()

    # Add postcode
    master = master.merge(sa_postcode_map, on='SA1', how='left')

    # Convert postcode to string for suburb matching (removing .0 from float)
    master['postcode_str'] = master['postcode'].apply(lambda x: str(int(x)) if pd.notna(x) else None)

    # Add suburb
    master = master.merge(postcode_suburb_map, left_on='postcode_str', right_on='postcode', how='left', suffixes=('', '_suburb'))

    # Clean up: keep original postcode column, drop the temp ones
    if 'postcode_suburb' in master.columns:
        master = master.drop(columns=['postcode_suburb'])
    master = master.drop(columns=['postcode_str'])

    # Load and merge other Sa_ files (excluding Males/Females variants)
    sa_files = [
        ('Raw/Sa_Age.csv', 'age'),
        ('Raw/Sa_Country.csv', 'country'),
        ('Raw/Sa_Hours.csv', 'hours'),
        ('Raw/Sa_Income.csv', 'income'),
        ('Raw/Sa_Households.csv', 'households'),
        ('Raw/Sa_CountHealth.csv', 'counthealth'),
        ('Raw/Sa_TypeHealth.csv', 'typehealth'),
    ]

    for file_path, prefix in sa_files:
        print(f"  Loading {file_path}...")
        # Try reading without skiprows first
        try:
            df = pd.read_csv(file_path)
            # Check if first column is "Australian Bureau of Statistics"
            if 'Australian Bureau of Statistics' in str(df.columns[0]):
                # Re-read with skiprows
                df = pd.read_csv(file_path, skiprows=1)
        except Exception as e:
            # If there's an error, try with skiprows
            df = pd.read_csv(file_path, skiprows=1)

        # Clean footer rows
        df = clean_footer_rows(df)

        # Rename first column to SA1
        sa1_col = df.columns[0]
        df.rename(columns={sa1_col: 'SA1'}, inplace=True)
        df['SA1'] = df['SA1'].astype(str)

        # Rename other columns to avoid conflicts (add prefix)
        rename_dict = {}
        for col in df.columns[1:]:  # Skip SA1 column
            if col != 'Total':  # Keep Total as is or add prefix
                rename_dict[col] = f"{prefix}_{col}"
            else:
                rename_dict[col] = f"{prefix}_Total"

        df.rename(columns=rename_dict, inplace=True)

        # Merge with master
        master = master.merge(df, on='SA1', how='left')

    # Save master file
    output_path = "Processed/Sa_Master.csv"
    master.to_csv(output_path, index=False)
    print(f"  Saved Sa_Master.csv with {len(master)} rows and {len(master.columns)} columns")
    print(f"  Columns: {master.columns.tolist()[:10]}... (showing first 10)")
    print()

    return master


def create_country_master():
    """Create Country_Master.csv by combining all country-level data"""
    print("Creating Country_Master.csv...")

    # Load Country files
    country_files = [
        ('Raw/Country_Education.csv', 'education'),
        ('Raw/Country_Hours.csv', 'hours'),
        ('Raw/Country_Income.csv', 'income'),
    ]

    master = None

    for file_path, prefix in country_files:
        print(f"  Loading {file_path}...")
        # Try reading without skiprows first
        try:
            df = pd.read_csv(file_path)
            # Check if first column is "Australian Bureau of Statistics"
            if 'Australian Bureau of Statistics' in str(df.columns[0]):
                # Re-read with skiprows
                df = pd.read_csv(file_path, skiprows=1)
        except Exception as e:
            # If there's an error, try with skiprows
            df = pd.read_csv(file_path, skiprows=1)

        # Clean footer rows
        df = clean_footer_rows(df)

        # Rename first column to Country
        country_col = df.columns[0]
        df.rename(columns={country_col: 'Country'}, inplace=True)

        # Rename other columns to avoid conflicts (add prefix)
        rename_dict = {}
        for col in df.columns[1:]:  # Skip Country column
            if col != 'Total':
                rename_dict[col] = f"{prefix}_{col}"
            else:
                rename_dict[col] = f"{prefix}_Total"

        df.rename(columns=rename_dict, inplace=True)

        # Merge with master
        if master is None:
            master = df
        else:
            master = master.merge(df, on='Country', how='outer')

    # Save master file
    output_path = "Processed/Country_Master.csv"
    master.to_csv(output_path, index=False)
    print(f"  Saved Country_Master.csv with {len(master)} rows and {len(master.columns)} columns")
    print(f"  Columns: {master.columns.tolist()[:10]}... (showing first 10)")
    print()

    return master


def main():
    # Create processed directory if it doesn't exist
    os.makedirs("Processed", exist_ok=True)

    # Create master files
    sa_master = create_sa_master()
    country_master = create_country_master()

    print("Master files created successfully!")
    print(f"\nSa_Master preview:")
    print(sa_master[['SA1', 'latitude', 'longitude', 'postcode', 'suburb']].head())

    print(f"\nCountry_Master preview:")
    print(country_master[['Country']].head(10))


if __name__ == "__main__":
    main()

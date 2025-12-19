"""
Process nested CSV files from ABS census data.
Converts 2-level hierarchical columns into a single-level format with a new category column.
"""

import pandas as pd
import numpy as np
import os


def process_nested_csv(input_path, output_path):
    """
    Process a nested CSV file with 2-level headers.

    Parameters:
    - input_path: Path to the input CSV file
    - output_path: Path to save the processed CSV file
    """
    print(f"Processing {input_path}...")

    # Read the first two rows to understand the structure
    df = pd.read_csv(input_path, header=None)

    # Get the header rows
    level1_header = df.iloc[0].values
    level2_header = df.iloc[1].values

    # Get the data (skip first two rows)
    data = df.iloc[2:].reset_index(drop=True)

    # Get the row identifier name (first column name in level 2)
    row_id_name = level2_header[0]

    # Get the category name (first column name in level 1)
    category_name = level1_header[0]

    # Find unique level2 values (excluding the first one which is the row identifier)
    # Count how many times the second level repeats to understand the structure
    level2_values = []
    i = 1
    while i < len(level2_header):
        if level2_header[i] not in level2_values:
            level2_values.append(level2_header[i])
        else:
            # We've completed one cycle
            break
        i += 1

    # Now find unique level1 categories
    level1_categories = []
    current_cat = None
    for i in range(1, len(level1_header)):
        val = level1_header[i]
        if pd.notna(val) and val != '' and val != current_cat:
            level1_categories.append(val)
            current_cat = val

    print(f"  - Found {len(level1_categories)} categories in level 1: {level1_categories}")
    print(f"  - Found {len(level2_values)} columns in level 2")

    # Create the processed dataframe
    processed_rows = []

    # Process each data row
    for idx, row in data.iterrows():
        row_id = row[0]

        # For each level1 category, extract the corresponding columns
        col_idx = 1  # Start after the row identifier

        for category in level1_categories:
            new_row = {category_name: category}
            new_row[row_id_name] = row_id

            # Extract values for each level2 column
            for level2_col in level2_values:
                if col_idx < len(row):
                    new_row[level2_col] = row[col_idx]
                    col_idx += 1
                else:
                    new_row[level2_col] = np.nan

            processed_rows.append(new_row)

    # Create the final dataframe
    # Column order: row_id, category, then all level2 columns
    processed_df = pd.DataFrame(processed_rows)
    column_order = [row_id_name, category_name] + level2_values
    processed_df = processed_df[column_order]

    # Save to CSV
    processed_df.to_csv(output_path, index=False)
    print(f"  - Saved to {output_path}")
    print(f"  - Output shape: {processed_df.shape}")
    print()

    return processed_df


def main():
    # Define input and output paths
    raw_nested_dir = "Raw/Nested"
    processed_dir = "Processed"

    # Create processed directory if it doesn't exist
    os.makedirs(processed_dir, exist_ok=True)

    # Define the files to process
    files_to_process = [
        ("Sa_HealthTypes.csv", "Detail_Sa_HealthTypes.csv"),
        ("Sa_SexAge.csv", "Detail_Sa_SexAge.csv"),
        ("Sa_SexIncome.csv", "Detail_Sa_SexIncome.csv"),
    ]

    # Process each file
    for input_file, output_file in files_to_process:
        input_path = os.path.join(raw_nested_dir, input_file)
        output_path = os.path.join(processed_dir, output_file)

        if os.path.exists(input_path):
            try:
                process_nested_csv(input_path, output_path)
            except Exception as e:
                print(f"Error processing {input_file}: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"File not found: {input_path}")

    print("Processing complete!")


if __name__ == "__main__":
    main()

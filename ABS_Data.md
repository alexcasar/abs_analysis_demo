# Downloading ABS Census Data - Complete Guide

This guide walks you through downloading all required census data files from the Australian Bureau of Statistics (ABS) TableBuilder.

---

## Table of Contents
1. [What is TableBuilder?](#what-is-tablebuilder)
2. [Account Setup](#account-setup)
3. [Accessing the Dataset](#accessing-the-dataset)
4. [Creating Tables - Step by Step](#creating-tables---step-by-step)
5. [Required Tables for This Project](#required-tables-for-this-project)
6. [Tips and Best Practices](#tips-and-best-practices)
7. [Understanding Geographic Levels](#understanding-geographic-levels)

---

## What is TableBuilder?

**ABS TableBuilder** is a free online tool that lets you create custom tables from Australian census data. Instead of downloading entire datasets, you can select exactly the variables and geographic areas you need.

**Key Features:**
- Customizable data tables
- Multiple geographic levels (SA1, Postcode, Suburb)
- Employment, income, education, demographics, health data
- CSV export format

**Data Used:** 2021 Census of Population and Housing

---

## Account Setup

### Step 1: Create Free Account

1. Go to: https://tablebuilder.abs.gov.au/webapi/jsf/login.xhtml
2. Click **"Register"** (if you don't have an account)
3. Fill in your details:
   - Email address
   - Password
   - Organization (can be "Personal" or "Student")
   - Agree to terms and conditions
4. **Verify your email** (check inbox/spam folder)
5. **Login** with your credentials

---

## Accessing the Dataset

Once logged in:

1. Click on **"Data"** in the top menu
2. Navigate to: **2021 Census of Population and Housing**
3. Select: **Census TableBuilder Basic**
4. Choose: **2021 Census - Employment, Income and Education**

This opens the Table View where you can customize your tables. Feel free to explore the dataset, there are many variables available about a wide arrange of categories, so you have the potential of building very interesting tables that let you investigate very specific hypothesis.

---

## Creating Tables - Step by Step

We'll walk through creating `Sa_Income.csv` as an example. This process applies to all tables.

### Example: Creating Sa_Income.csv

This table shows **Income by SA1** (Statistical Area Level 1).

---

#### Step 1: Select Geographic Areas (Rows)

1. **Expand** the **"Geographical Areas (Usual Residence)"** folder on the left
2. Click the **left arrow** (◀) next to **"SA1 by Greater Capital City Statistical Areas (UR)"** to expand it
3. Find **"Victoria"** in the list
4. Click the **right arrow** (▶) next to **"Victoria"**
5. Select **"SA1 (UR)"** from the dropdown
   - This selects all ~15,000 Statistical Area 1 regions in Victoria
6. Click **"Add to: Row"** (near the top of the page)
   - Your preview table on the right should now show SA1 codes in rows

---

#### Step 2: Select Income Variable (Columns)

1. **Collapse** the Geographical Areas folder (click the left arrow)
2. **Expand** the **"Employment and Income"** folder
3. Find **"INCP Total Personal Income (weekly)"**
4. Click the **right arrow** (▶) next to it
5. Select the variable (this will show all income ranges)
6. Click **"Add to: Column"** (near the top)
   - Your preview table should now show income ranges as columns

---

#### Step 3: Preview Your Table

Your table should now look like:
- **Rows:** SA1 codes (e.g., 20101100101, 20101100102, ...)
- **Columns:** Income ranges (Negative/Nil income, $1-$149, $150-$299, ...)
- **Cells:** Count of people in each SA1 for each income range

---

#### Step 4: Save the Table

1. Click **"Save Table"** (top right)
2. Enter a descriptive name: `Sa_Income`
3. Click **"Save"**

---

#### Step 5: Queue for Download

1. Click **"Queue Table"** (top right, next to Save)
2. Use the same name: `Sa_Income`
3. Click **"Queue"**

---

#### Step 6: Download the Table

1. Click the **three dots (⋮)** next to the search bar (top right)
2. Select **"Saved and Queued Tables"**
3. Go to the **"Queued Tables"** tab
4. **Refresh** the page until Status shows **"Completed"** (usually 10-60 seconds)
5. Click **"Click here to download"**
6. **Download** the CSV file
7. Save it as `Sa_Income.csv` in your `Raw/` folder

---

#### Step 7: Table Cleaning

The table will get downloaded as a .zip folder, you first need to extract that to get the csv file.

Then, the files have some extra rows at the beginning with some metadata about the dataset. This extra rows make processing csv's trickier, for simplicity I manually edit this files to remove all the rows that come before the column names + the row that comes below the column names (which indicates the category of the rows).

After the manual edits, the csv should be in a rows x columns format without any extra data on top.

---

## Required Tables for This Project

Create the following tables using the same process. Each table specifies what goes in rows and columns.

### SA1-Level Tables (Victoria)

All SA1 tables use **SA1 (UR)** for Victoria as ROWS. 

| File Name | Rows | Columns | Location in Menu |
|-----------|------|---------|------------------|
| `Sa_Age.csv` | SA1 (Victoria) | AGEP Age | Person > Age |
| `Sa_Income.csv` | SA1 (Victoria) | INCP Total Personal Income (weekly) | Employment and Income > Income |
| `Sa_Hours.csv` | SA1 (Victoria) | HSCP Hours Worked | Employment and Income > Hours Worked |
| `Sa_Country.csv` | SA1 (Victoria) | BPLP Country of Birth | Cultural Diversity > Country of Birth |
| `Sa_Households.csv` | SA1 (Victoria) | RLHP Relationship in Household | Family and Household > Relationship in Household |
| `Sa_CountHealth.csv` | SA1 (Victoria) | CLTHP Count of Selected Long-term Health Conditions | Health > Long-term Health Conditions |
| `Sa_TypeHealth.csv` | SA1 (Victoria) | LTHP Type of Long-term Health Condition | Health > Long-term Health Conditions |

Plus any other tables in the Raw folder which follow the same format of Row_Column.csv
---

### Mapping Tables

These tables map SA1s to Postcodes and Postcodes to Suburbs.

| File Name | Rows | Columns | Notes |
|-----------|------|---------|-------|
| `Sa_Postcode.csv` | SA1 (Victoria) | POA Postcode | Under Geographical Areas |
| `Postcode_Suburb.csv` | POA Postcode (Victoria) | SSC Suburb/Locality | Under Geographical Areas |

**How to select Postcode/Suburb:**
- For Postcode: Expand "POA Postcode (UR)" → Select Victoria → Choose "POA (UR)"
- For Suburb: Expand "SSC Suburb/Locality (UR)" → Select Victoria → Choose "SSC (UR)"

---

### Country-Level Tables

These tables use **Country of Birth** as ROWS instead of SA1.

| File Name | Rows | Columns | Dataset |
|-----------|------|---------|---------|
| `Country_Education.csv` | BPLP Country of Birth | HEAP Highest Educational Attainment | Education |
| `Country_Income.csv` | BPLP Country of Birth | INCP Total Personal Income (weekly) | Employment and Income |
| `Country_Hours.csv` | BPLP Country of Birth | HSCP Hours Worked | Employment and Income |

**To select Country of Birth as rows:**
1. Expand "Cultural Diversity" folder
2. Find "BPLP Country of Birth"
3. Click right arrow → Select all countries
4. Click "Add to: Row"

---

### Shapefile for Geographic Locations

The shapefile is **not** downloaded from TableBuilder. Instead:

1. Go to: https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files
2. Download: **Statistical Area Level 1 (SA1) ASGS Edition 3 (2021) - Shapefile**
3. Extract the ZIP file
4. Copy the SA1 shapefile (all files: .shp, .shx, .dbf, .prj) to `Raw/Locs/`
5. Ensure the main file is named: `SA1_2021_AUST_GDA2020.shp`

---

## Tips and Best Practices

### 1. Naming Convention
Use a consistent format: `Row_Column.csv`
- Examples: `Sa_Income.csv`, `Sa_Age.csv`, `Country_Education.csv`
- This makes it easy to remember what each file contains

### 2. Check Preview Before Downloading
Always preview your table to ensure:
- Rows and columns are correct
- Data looks reasonable (no empty tables)
- All categories are included

### 3. Download Times
- Simple tables (1 row variable, 1 column variable): 10-60 seconds
- Complex tables (multiple variables): 1-5 minutes
- Very large tables (SA1 × multiple columns): up to 10 minutes

### 4. File Sizes
- SA1-level tables: Typically 2-20 MB
- Postcode/Suburb tables: Usually < 1 MB
- Country tables: Usually < 500 KB

### 5. Queue Multiple Tables
You can queue multiple tables at once and download them all together. This saves time!

---

## Understanding Geographic Levels

### SA1 (Statistical Area Level 1)
- **Count in Victoria:** ~15,482 areas
- **Population:** ~200-800 people per SA1
- **Use Case:** Most granular data for detailed mapping
- **Pros:** High precision, perfect for small-area analysis
- **Cons:** Large file sizes, harder to create multi-variable tables

**More info:** https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/main-structure-and-greater-capital-city-statistical-areas/statistical-area-level-1

### Postcode (POA)
- **Count in Victoria:** ~634 postcodes
- **Use Case:** Familiar geographic units for general analysis
- **Pros:** Smaller files, easier to create complex tables
- **Cons:** Less precise than SA1

### Suburb/Locality (SSC)
- **Count in Victoria:** ~628 suburbs
- **Use Case:** Recognizable place names for reporting
- **Pros:** Easy to understand, good for presentations
- **Cons:** Irregular boundaries, some overlap with postcodes

---

## Creating Complex Multi-Variable Tables

For tables with **multiple row or column variables** (e.g., Sa1 x Age + Sex combinations):

### Example: Age and Sex combinations by Sa1

1. Add **AGEP Age** to Columns
2. Add **SEXP Sex** to Columns (again)
   - This creates a nested column structure: Sex > Age
3. Add **SA1** to Rows (as before)

**Result:** Table with columns like:
- Male > 0-14 years
- Male > 15-24 years
- Female > 0-14 years
- Female > 15-24 years
- etc.

### Important Notes:
- **File size increases multiplicatively** with each variable
- For SA1-level data, **limit to 2-3 variables maximum**
- For complex tables, **use Postcode or Suburb instead of SA1**
- These nested tables require special processing (see `process_nested_files.py`)

---

## Common Issues and Solutions

### ❌ "Table is too large to queue"
**Problem:** Too many cells in the table (SA1 × too many categories)
**Solution:**
- Use Postcode or Suburb instead of SA1
- Reduce the number of column variables
- Split into multiple smaller tables

### ❌ Table status stuck at "Processing"
**Problem:** Server delay or very large table
**Solution:**
- Wait 5-10 minutes
- Refresh the page
- If still stuck after 30 minutes, contact ABS support

### ❌ Download file is empty or corrupted
**Problem:** Issue during download
**Solution:**
- Re-download the file
- Try a different browser
- Check internet connection

### ❌ Column names have special characters
**Expected:** ABS uses commas in column names (e.g., "Melbourne, Vic")
**Not a problem:** The preprocessing scripts handle this automatically

---

## Next Steps

Once you've downloaded all the data files:

1. ✅ Verify all files are in the `Raw/` folder
2. ✅ Check file sizes are reasonable (not 0 KB)
3. ✅ Proceed to **README.md** for preprocessing instructions
4. ✅ Run the 5 preprocessing scripts in order
5. ✅ Launch the Streamlit application

---

## Additional Resources

- **ABS TableBuilder Help:** https://www.abs.gov.au/statistics/microdata-tablebuilder/tablebuilder
- **2021 Census Data:** https://www.abs.gov.au/census
- **ASGS Documentation:** https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3
- **Contact ABS Support:** client.services@abs.gov.au

---

## License

All ABS data is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

When using this data, include attribution:
> "Data sourced from the Australian Bureau of Statistics, 2021 Census of Population and Housing"

More info: https://www.abs.gov.au/ccby

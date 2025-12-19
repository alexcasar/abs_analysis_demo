# Victoria Demographics Visualization & Market Research Tool

Interactive Streamlit application for analyzing Australian Bureau of Statistics (ABS) census data for Victoria, Australia. Includes demographic visualizations, country of origin analysis, and market research tools for business location optimization.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup Instructions](#detailed-setup-instructions)
4. [Application Features](#application-features)
5. [File Structure](#file-structure)
6. [Troubleshooting](#troubleshooting)
7. [Technical Notes](#technical-notes)

---

## Prerequisites

### Software Requirements
- **Python 3.8 or higher**
- pip (Python package manager)

### Python Libraries
Install required packages:
```bash
pip install pandas numpy streamlit plotly scipy geopandas
```

Or using requirements.txt:
```bash
pip install -r requirements.txt
```

### Data Requirements
Your `Raw/` folder must contain:
- **ABS Census CSV files**: `Sa_Age.csv`, `Sa_Country.csv`, `Sa_Income.csv`, `Sa_Hours.csv`, `Sa_Households.csv`, `Sa_CountHealth.csv`, `Sa_TypeHealth.csv`
- **Geographic mapping files**: `Sa_Postcode.csv`, `Postcode_Suburb.csv`
- **Country data**: `Country_Education.csv`, `Country_Income.csv`, `Country_Hours.csv`
- **Shapefile**: `Raw/Locs/SA1_2021_AUST_GDA2020.shp` (and associated .shx, .dbf, .prj files)

---

## Quick Start

If you just want to run the app and all preprocessing is done:

```bash
streamlit run app.py
```

If starting from scratch, follow the [Detailed Setup Instructions](#detailed-setup-instructions) below.

---

## Detailed Setup Instructions

### Step-by-Step Data Preprocessing

**IMPORTANT:** Run these scripts in order. Each script must complete successfully before running the next one.

#### Step 0: Downloading Australian Bureau of Statistics Data
Instructions on ABS_Data.md

#### Step 1: Extract SA1 Locations
Extracts latitude/longitude coordinates from the shapefile.

```bash
python extract_sa1_locations.py
```

**Output:** `Processed/Sa_Location.csv`
**Time:** ~2-5 minutes
**What it does:** Converts geographic shapefile data into CSV with SA1 codes and coordinates for Victoria only.

---

#### Step 2: Create Master Files
Combines all raw CSV files into comprehensive master datasets.

```bash
python create_master_files.py
```

**Outputs:**
- `Processed/Sa_Master.csv` (15,482 records, 510 columns)
- `Processed/Country_Master.csv` (297 records, 66 columns)

**Time:** ~30-60 seconds
**What it does:** Merges location data, postcode/suburb mappings, and all demographic data into master files with prefixed column names.

---

#### Step 3: Create Processed Files
Calculates derived statistics from the master files.

```bash
python create_processed_files.py
```

**Outputs:**
- `Processed/Sa_Master_Processed.csv` - Stats for each SA1 (avg_age, avg_income, population_density, etc.)
- `Processed/Country_Master_Processed.csv` - Stats by country (avg_income, education levels, etc.)

**Time:** ~20-30 seconds
**What it does:** Computes weighted averages, population totals, age groups, hourly wages, and other derived metrics.

---

#### Step 4: Create Aggregated Files
Aggregates SA1 data to postcode and suburb levels.

```bash
python create_aggregated_files.py
```

**Outputs:**
- `Processed/Postcode/Postcode_Master.csv` (634 records, 455 columns)
- `Processed/Postcode/Postcode_Processed.csv` (634 records, 23 columns)
- `Processed/Suburb/Suburb_Master.csv` (628 records, 455 columns)
- `Processed/Suburb/Suburb_Processed.csv` (628 records, 23 columns)

**Time:** ~30-45 seconds
**What it does:** Rolls up SA1-level data to larger geographic areas using weighted averages and summations.

---

#### Step 5: Create Percentage Files
Converts raw counts to per capita percentages.

```bash
python create_pct_files.py
```

**Outputs:**
- `Processed/Sa_Master_Pct.csv` (15,482 records)
- `Processed/Country_Master_Pct.csv` (297 records)
- `Processed/Postcode/Postcode_Master_Pct.csv` (634 records)
- `Processed/Suburb/Suburb_Master_Pct.csv` (628 records)

**Time:** ~45-60 seconds
**What it does:** Calculates percentage distributions (e.g., "15% of population is aged 25-54") enabling fair comparison across areas of different sizes.

---

#### Step 6: Launch the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

**Total preprocessing time: ~5-10 minutes**

---

## Application Features

### 1. 📊 Geographic Demographics
View calculated statistics across Victoria at three aggregation levels.

**Available Metrics:**
- Total Population
- Population Density (people/km²)
- Average Age
- Average Income (annual)
- Average Hours Worked (per week)
- Hourly Wage (calculated)

**Aggregation Levels:** SA1 (15,482 areas) / Postcode (634) / Suburb (628)

---

### 2. 📅 Age Analysis

#### Age Group Distribution Map
- **View Modes:** Raw Counts or Percentage (%)
- **Age Groups:** 0-14, 15-24, 25-54, 55-64, 65+ years
- **Use Percentage Mode** to compare demographics fairly: "20% of this postcode is aged 25-54" vs "5,000 people aged 25-54"
- **All Aggregation Levels:** SA1 / Postcode / Suburb

#### Custom Age Range Filter
- Select any age range (e.g., 18-35)
- View distribution on interactive map
- SA1 level only

#### Age Pyramid
- Visual representation of Victoria's age distribution
- Shows all ages 0-115+

---

### 3. 💰 Income Analysis

**Three Visualizations:**

1. **Income Distribution Map**
   - Average income by geographic area
   - Supports SA1/Postcode/Suburb aggregation

2. **Income vs Age**
   - Scatter plot showing correlation
   - Identify income trends by age

3. **Income Distribution Histogram**
   - See distribution of income levels
   - Aggregated by selected level

---

### 4. 🌏 Country of Origin Analysis

#### Tab 1: Country Statistics
Compare 294 countries by:
- Average Income
- Average Hours Worked
- Hourly Wage
- Education Level (Postgraduate %, Bachelor %)

**Features:**
- Top N countries bar charts
- "Show all countries" option
- Detailed statistics table

#### Tab 2: Geographic Distribution ⭐ NEW
Select any country and view where people from that country live in Victoria.

**View Modes:**
- **Raw Counts:** Actual number of people (e.g., "1,000 people from China")
- **Percentage (%):** % of total population (e.g., "5% of this suburb is from China")

**Why Percentage Matters:**
Raw counts favor large areas. Percentages reveal true concentration patterns:
- Small suburb: 500 people from India (5% of population) = high concentration
- Large suburb: 2,000 people from India (0.5% of population) = low concentration

**All Aggregation Levels:** SA1 / Postcode / Suburb

---

### 5. 🎯 Market Research Tool

Optimize business location decisions using population analysis.

#### Management Tab
- **Add Business Locations:** Name, latitude, longitude
- **Bulk Import:** Upload CSV (format: name,latitude,longitude)
- **Edit/Remove:** Manage existing locations
- **View Catchments:** See which SA1 areas are assigned to each business (nearest-neighbor)

#### Analysis Tab
View detailed catchment statistics for any business:
- Total population served
- Number of SA1 areas in catchment
- Average income, age, hours worked
- **Demographic Breakdown:** Age distribution bar chart showing % in each age group
- Population density insights

#### Find Optimal Location Tab
Identify best locations for new businesses based on multiple criteria.

**Targeting Options:**

🎂 **Age Group Targeting**
- 0-14 years (children)
- 15-24 years (youth)
- 25-54 years (working age)
- 55-64 years (pre-retirement)
- 65+ years (seniors)

🏠 **Household Type Targeting**
- Couples
- Lone parents
- Children under 15
- Multi-family households

🏥 **Health Conditions** (accessibility planning)
- Arthritis
- Asthma
- Mental health conditions
- Mobility issues

**Scoring Algorithm:**
- Population density (40% weight)
- Target demographic match (40% weight)
- Distance from existing businesses - gap filling (20% weight)

**Output:** Top N recommended locations with coordinates, scores, and population details.

---

## File Structure

```
ABS_Data/
├── Raw/                                # INPUT: ABS census data
│   ├── Sa_Age.csv
│   ├── Sa_Country.csv
│   ├── Sa_Income.csv
│   ├── Sa_Hours.csv
│   ├── Sa_Households.csv
│   ├── Sa_CountHealth.csv
│   ├── Sa_TypeHealth.csv
│   ├── Sa_Postcode.csv
│   ├── Postcode_Suburb.csv
│   ├── Country_Education.csv
│   ├── Country_Income.csv
│   ├── Country_Hours.csv
│   └── Locs/
│       └── SA1_2021_AUST_GDA2020.shp
│
├── Processed/                          # OUTPUT: Generated files
│   ├── Sa_Location.csv                 # Step 1 output
│   ├── Sa_Master.csv                   # Step 2 output (raw counts)
│   ├── Sa_Master_Processed.csv         # Step 3 output (calculated stats)
│   ├── Sa_Master_Pct.csv               # Step 5 output (percentages)
│   ├── Country_Master.csv              # Step 2 output
│   ├── Country_Master_Processed.csv    # Step 3 output
│   ├── Country_Master_Pct.csv          # Step 5 output
│   ├── Postcode/
│   │   ├── Postcode_Master.csv         # Step 4 output (raw counts)
│   │   ├── Postcode_Processed.csv      # Step 4 output (stats)
│   │   └── Postcode_Master_Pct.csv     # Step 5 output (percentages)
│   └── Suburb/
│       ├── Suburb_Master.csv           # Step 4 output (raw counts)
│       ├── Suburb_Processed.csv        # Step 4 output (stats)
│       └── Suburb_Master_Pct.csv       # Step 5 output (percentages)
│
├── extract_sa1_locations.py            # STEP 1
├── create_master_files.py              # STEP 2
├── create_processed_files.py           # STEP 3
├── create_aggregated_files.py          # STEP 4
├── create_pct_files.py                 # STEP 5
├── aggregation_utils.py                # Utilities for aggregation
├── market_research_tool.py             # Market research logic
├── app.py                              # STEP 6: Main application
└── README.md                           # This file
```

---

## Troubleshooting

### ❌ Files are locked / Permission denied
**Problem:** Excel or another program has CSV files open.
**Solution:** Close all Excel windows and any programs that might have the CSV files open.

### ❌ Missing columns error
**Problem:** Raw data files missing or incorrectly formatted.
**Solution:**
- Verify all required CSV files are in `Raw/` folder
- Check files match ABS census data format
- Re-download files if necessary

### ❌ Map not displaying
**Problem:** Location data missing or invalid coordinates.
**Solution:**
- Re-run `extract_sa1_locations.py`
- Ensure shapefile is in `Raw/Locs/`
- Check shapefile includes .shp, .shx, .dbf, .prj files

### ❌ KeyError: column not found
**Problem:** Column names don't match between files.
**Solution:** Re-run preprocessing steps 2-5 in order.

### ⚠️ Percentages don't sum to exactly 100%
**Expected Behavior:** Census data includes "Not stated" values, so percentages typically sum to 96-99%.
**If much lower (< 90%):** Re-run `create_pct_files.py`.

### ❌ Streamlit won't start
**Problem:** Missing dependencies or wrong Python version.
**Solution:**
```bash
python --version  # Check version is 3.8+
pip install --upgrade streamlit pandas numpy plotly scipy geopandas
```

### ❌ Country map shows "No data available"
**Problem:** Percentage files not generated or corrupted.
**Solution:** Re-run Step 5: `python create_pct_files.py`

---

## Technical Notes

### Geographic Levels
- **SA1 (Statistical Area Level 1):** Smallest census unit, ~200-800 people, 15,482 in Victoria
- **Postcode:** Australian postal code areas, 634 in Victoria
- **Suburb:** Locality names, 628 in Victoria

### File Types
- **Master files:** Complete raw count data (all demographic columns)
- **Processed files:** Calculated statistics (averages, densities, age groups)
- **Pct files:** Per capita percentages for fair comparison across area sizes

### Coordinate System
- Shapefile: GDA2020 (EPSG:7844)
- Maps: WGS84 (latitude/longitude) for display
- Area calculations: Web Mercator (EPSG:3857)

### Statistical Methods
- **Averages:** Weighted by population/earners/workers
- **Income/hours ranges:** Median of range used
- **Open-ended ranges:** Estimated at 1.25× minimum
- **Percentage aggregation:** Recalculated from counts (not averaged)

### Performance
- Streamlit caching: Data cached in memory after first load
- Spatial indexing: cKDTree for fast nearest-neighbor queries
- Initial load: May take a few seconds for large datasets

---

## Data Sources

**Australian Bureau of Statistics (ABS)**
- 2021 Census of Population and Housing
- TableBuilder custom data extracts
- SA1 Geographic Boundaries (ASGS 2021)

**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
See: https://www.abs.gov.au/ccby

---

## Key Terminology

- **SA1:** Statistical Area Level 1 - smallest geographic census unit
- **Aggregation:** Combining smaller areas into larger ones (SA1 → Postcode → Suburb)
- **Weighted Average:** Average that accounts for different population sizes
- **Per Capita:** Per person (percentage-based for fair comparison)
- **Catchment Area:** Geographic area served by a business location
- **Nearest-Neighbor:** Assignment method where each area goes to closest business

---

## Credits

**Developed using:**
- Python 3.x
- Streamlit (web framework)
- Plotly (interactive visualizations)
- Pandas (data processing)
- GeoPandas (geospatial data)
- SciPy (spatial algorithms)

**Data source:** Australian Bureau of Statistics (ABS)

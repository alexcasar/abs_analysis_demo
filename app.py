"""
Interactive Demographics Visualization and Market Research Tool
Victoria, Australia Census Data Analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial import cKDTree
from market_research_tool import MarketResearchTool
# Page configuration
st.set_page_config(
    page_title="Victoria Demographics & Market Research",
    page_icon="🗺️",
    layout="wide"
)

# Cache data loading
@st.cache_data
def load_data():
    """Load all required data files"""
    sa_master = pd.read_csv("Processed/Sa_Master.csv")
    sa_processed = pd.read_csv("Processed/Sa_Master_Processed.csv")
    country_master = pd.read_csv("Processed/Country_Master.csv")
    country_processed = pd.read_csv("Processed/Country_Master_Processed.csv")

    return sa_master, sa_processed, country_master, country_processed


# Cache pre-aggregated data loading
@st.cache_data
def load_aggregated_data(level):
    """Load pre-aggregated data at the specified level (Processed files with calculated stats)"""
    if level == 'SA1':
        return pd.read_csv("Processed/Sa1_Processed_WithBounds.csv")
    elif level == 'Postcode':
        return pd.read_csv("Processed/Postcode/Postcode_Processed.csv")
    elif level == 'Suburb':
        return pd.read_csv("Processed/Suburb/Suburb_Processed.csv")
    else:
        raise ValueError(f"Unknown aggregation level: {level}")


@st.cache_data
def load_master_data(level):
    """Load pre-aggregated master data at the specified level (Master files with raw counts)"""
    if level == 'SA1':
        # For SA1, need to merge Master with location data
        sa_master = pd.read_csv("Processed/Sa_Master.csv")

        # Check if latitude/longitude already exist
        if 'latitude' not in sa_master.columns:
            sa_processed = pd.read_csv("Processed/Sa_Master_Processed.csv")
            # Merge location columns
            sa_master = sa_master.merge(
                sa_processed[['SA1', 'latitude', 'longitude', 'area_km2']],
                on='SA1',
                how='left'
            )
        return sa_master
    elif level == 'Postcode':
        return pd.read_csv("Processed/Postcode/Postcode_Master.csv")
    elif level == 'Suburb':
        return pd.read_csv("Processed/Suburb/Suburb_Master.csv")
    else:
        raise ValueError(f"Unknown aggregation level: {level}")


@st.cache_data
def load_master_pct_data(level):
    """Load pre-aggregated percentage data at the specified level (Master_Pct files with percentages)"""
    if level == 'SA1':
        return pd.read_csv("Processed/Sa_Master_Pct.csv")
    elif level == 'Postcode':
        return pd.read_csv("Processed/Postcode/Postcode_Master_Pct.csv")
    elif level == 'Suburb':
        return pd.read_csv("Processed/Suburb/Suburb_Master_Pct.csv")
    else:
        raise ValueError(f"Unknown aggregation level: {level}")


def create_choropleth_map(df, color_column, title, color_scale="Viridis", show_boundaries=True):
    """Create a choropleth-style scatter map with marker size based on area"""

    # Prepare hover data based on what columns are available
    hover_cols = []
    if 'id' in df.columns:
        hover_cols.append('id')
    if 'level' in df.columns:
        hover_cols.append('level')
    if 'postcode' in df.columns and 'postcode' not in hover_cols:
        hover_cols.append('postcode')
    if 'suburb' in df.columns and 'suburb' not in hover_cols:
        hover_cols.append('suburb')

    # Calculate marker size based on area for aggregated levels
    df_plot = df.copy()
    if 'area_km2' in df_plot.columns and show_boundaries:
        # Use square root of area for better visual scaling
        df_plot['marker_size'] = np.sqrt(df_plot['area_km2']) * 3  # Scale factor for visibility
        size_col = 'marker_size'
        size_max = 50  # Cap maximum size
    else:
        size_col = None
        size_max = None

    fig = px.scatter_mapbox(
        df_plot,
        lat="latitude",
        lon="longitude",
        color=color_column,
        size=size_col,
        size_max=size_max,
        hover_data=hover_cols,
        color_continuous_scale=color_scale,
        title=title,
        zoom=6,
        height=600
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=-37.8, lon=145)  # Melbourne center
        )
    )

    return fig


def main():
    st.title("🗺️ Victoria Demographics & Market Research Tool")
    st.markdown("---")

    # Load data
    with st.spinner("Loading data..."):
        sa_master, sa_processed, country_master, country_processed = load_data()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Analysis Type",
        ["Geographic Demographics", "Age Analysis", "Income Analysis",
         "Country of Origin Analysis", "Market Research Tool"]
    )

    # ===== GEOGRAPHIC DEMOGRAPHICS =====
    if page == "Geographic Demographics":
        st.header("Geographic Demographics Visualization")

        # Aggregation level and metric selectors
        col_select1, col_select2 = st.columns([1, 2])

        with col_select1:
            agg_level = st.selectbox(
                "Aggregation Level",
                ["SA1", "Postcode", "Suburb"],
                help="SA1: Smallest geographic unit\nPostcode: Aggregate by postcode\nSuburb: Aggregate by suburb",
                key="geo_agg_level"
            )

        with col_select2:
            metric = st.selectbox(
                "Select Metric",
                ["Total Population", "Population Density", "Average Age",
                 "Average Income", "Average Hours Worked", "Hourly Wage"],
                key="geo_metric"
            )

        # Map metric names to column names
        column_map = {
            "Total Population": "total_population",
            "Population Density": "population_density",
            "Average Age": "avg_age",
            "Average Income": "avg_income",
            "Average Hours Worked": "avg_hours_worked",
            "Hourly Wage": "hourly_wage"
        }
        col_name = column_map[metric]

        # Load processed data (calculated statistics)
        df_plot = load_aggregated_data(agg_level)

        df_plot = df_plot.dropna(subset=[col_name, 'latitude', 'longitude'])

        # Show boundaries for postcode/suburb
        show_bounds = agg_level in ['Postcode', 'Suburb']

        fig = create_choropleth_map(
            df_plot,
            col_name,
            f"{metric} across Victoria ({agg_level} level)",
            color_scale="RdYlGn" if "income" in col_name.lower() or "wage" in col_name.lower() else "Viridis",
            show_boundaries=show_bounds
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean", f"{df_plot[col_name].mean():.2f}")
        with col2:
            st.metric("Median", f"{df_plot[col_name].median():.2f}")
        with col3:
            st.metric("Min", f"{df_plot[col_name].min():.2f}")
        with col4:
            st.metric("Max", f"{df_plot[col_name].max():.2f}")

        # Show data count
        st.info(f"Showing {len(df_plot)} {agg_level}{'s' if agg_level != 'SA1' else ' areas'}")

    # ===== AGE ANALYSIS =====
    elif page == "Age Analysis":
        st.header("Age Distribution Analysis")

        analysis_type = st.radio(
            "Select Analysis Type",
            ["Age Group Distribution Map", "Custom Age Range Filter", "Age Pyramid"]
        )

        if analysis_type == "Age Group Distribution Map":
            # Selectors
            col_select1, col_select2, col_select3 = st.columns([1, 1, 2])

            with col_select1:
                agg_level = st.selectbox(
                    "Aggregation Level",
                    ["SA1", "Postcode", "Suburb"],
                    help="SA1: Smallest geographic unit\nPostcode: Aggregate by postcode\nSuburb: Aggregate by suburb",
                    key="age_agg_level"
                )

            with col_select2:
                view_mode = st.selectbox(
                    "View Mode",
                    ["Raw Counts", "Percentage (%)"],
                    help="Raw Counts: Actual number of people\nPercentage: % of total population",
                    key="age_view_mode"
                )

            with col_select3:
                age_group = st.selectbox(
                    "Select Age Group",
                    ["0-14 years", "15-24 years", "25-54 years", "55-64 years", "65+ years"]
                )

            # Define age ranges for each group
            age_ranges = {
                "0-14 years": (0, 14),
                "15-24 years": (15, 24),
                "25-54 years": (25, 54),
                "55-64 years": (55, 64),
                "65+ years": (65, 115)
            }

            if view_mode == "Raw Counts":
                # Use processed data with pre-calculated age group counts
                group_map = {
                    "0-14 years": "pop_0_14",
                    "15-24 years": "pop_15_24",
                    "25-54 years": "pop_25_54",
                    "55-64 years": "pop_55_64",
                    "65+ years": "pop_65_plus"
                }
                col_name = group_map[age_group]
                df_plot = load_aggregated_data(agg_level)
                df_plot = df_plot.dropna(subset=[col_name, 'latitude', 'longitude'])
                title = f"Population aged {age_group} across Victoria ({agg_level} level)"
            else:
                # Calculate percentage from Master_Pct data
                df_pct = load_master_pct_data(agg_level)

                # Sum up individual age percentages for the selected range
                min_age, max_age = age_ranges[age_group]
                age_cols = [f'age_{i}' for i in range(min_age, max_age + 1) if f'age_{i}' in df_pct.columns]

                if age_cols:
                    df_pct[f'pct_{age_group}'] = df_pct[age_cols].sum(axis=1)
                    col_name = f'pct_{age_group}'
                    df_plot = df_pct.dropna(subset=[col_name, 'latitude', 'longitude'])
                    title = f"% Population aged {age_group} across Victoria ({agg_level} level)"
                else:
                    st.error(f"Age data not available for {age_group}")
                    df_plot = pd.DataFrame()

            if len(df_plot) > 0:
                show_bounds = agg_level in ['Postcode', 'Suburb']

                fig = create_choropleth_map(
                    df_plot,
                    col_name,
                    title,
                    show_boundaries=show_bounds
                )

                st.plotly_chart(fig, use_container_width=True)

                # Show statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    if view_mode == "Percentage (%)":
                        st.metric("Average %", f"{df_plot[col_name].mean():.2f}%")
                    else:
                        st.metric("Total Population", f"{df_plot[col_name].sum():,.0f}")
                with col2:
                    st.metric(f"Number of {agg_level}s", f"{len(df_plot):,}")
                with col3:
                    if view_mode == "Percentage (%)":
                        st.metric("Max %", f"{df_plot[col_name].max():.2f}%")
                    else:
                        st.metric("Average per area", f"{df_plot[col_name].mean():,.0f}")

        elif analysis_type == "Custom Age Range Filter":
            st.subheader("Filter by Custom Age Range")

            col1, col2 = st.columns(2)
            with col1:
                min_age = st.number_input("Minimum Age", 0, 115, 18)
            with col2:
                max_age = st.number_input("Maximum Age", 0, 115, 65)

            # Calculate population in selected age range
            age_cols = [f'age_{i}' for i in range(int(min_age), int(max_age) + 1)
                       if f'age_{i}' in sa_master.columns]

            if age_cols:
                sa_filtered = sa_master.copy()
                sa_filtered['selected_age_pop'] = sa_master[age_cols].sum(axis=1)

                # Merge with location data
                df_plot = sa_processed[['SA1', 'latitude', 'longitude', 'postcode', 'suburb']].merge(
                    sa_filtered[['SA1', 'selected_age_pop']],
                    on='SA1'
                ).dropna(subset=['latitude', 'longitude'])

                fig = create_choropleth_map(
                    df_plot,
                    'selected_age_pop',
                    f"Population aged {int(min_age)}-{int(max_age)} across Victoria"
                )

                st.plotly_chart(fig, use_container_width=True)

                st.metric("Total Population in Selected Age Range",
                         f"{df_plot['selected_age_pop'].sum():,.0f}")
            else:
                st.warning("No data available for selected age range")

        else:  # Age Pyramid
            st.subheader("Age Pyramid for Victoria")

            # Aggregate age data across all SA1 areas
            age_cols = [col for col in sa_master.columns if col.startswith('age_')
                       and col != 'age_Total']

            age_data = []
            for col in age_cols:
                age = col.split('_')[1]
                if age.isdigit():
                    age_data.append({
                        'Age': int(age),
                        'Population': sa_master[col].sum()
                    })

            df_age = pd.DataFrame(age_data).sort_values('Age')

            fig = px.bar(
                df_age,
                x='Population',
                y='Age',
                orientation='h',
                title="Age Distribution Pyramid - Victoria",
                height=800
            )

            st.plotly_chart(fig, use_container_width=True)

    # ===== INCOME ANALYSIS =====
    elif page == "Income Analysis":
        st.header("Income Analysis")

        viz_type = st.radio(
            "Select Visualization",
            ["Income Distribution Map", "Income vs Age", "Income Distribution Histogram"]
        )

        if viz_type == "Income Distribution Map":
            # Aggregation level selector
            agg_level = st.selectbox(
                "Aggregation Level",
                ["SA1", "Postcode", "Suburb"],
                help="SA1: Smallest geographic unit\nPostcode: Aggregate by postcode\nSuburb: Aggregate by suburb",
                key="income_map_agg_level"
            )

            # Get data at selected aggregation level
            df_plot = load_aggregated_data(agg_level)
            df_plot = df_plot.dropna(subset=['avg_income', 'latitude', 'longitude'])

            show_bounds = agg_level in ['Postcode', 'Suburb']

            fig = create_choropleth_map(
                df_plot,
                'avg_income',
                f"Average Income across Victoria ({agg_level} level)",
                color_scale="RdYlGn",
                show_boundaries=show_bounds
            )

            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Income", f"${df_plot['avg_income'].mean():,.2f}")
            with col2:
                st.metric("Median Income", f"${df_plot['avg_income'].median():,.2f}")
            with col3:
                st.metric("Std Dev", f"${df_plot['avg_income'].std():,.2f}")

            st.info(f"Showing {len(df_plot)} {agg_level}{'s' if agg_level != 'SA1' else ' areas'}")

        elif viz_type == "Income vs Age":
            # Aggregation level selector
            agg_level = st.selectbox(
                "Aggregation Level",
                ["SA1", "Postcode", "Suburb"],
                help="SA1: Smallest geographic unit\nPostcode: Aggregate by postcode\nSuburb: Aggregate by suburb",
                key="income_scatter_agg_level"
            )

            # Get data at selected aggregation level
            df_plot = load_aggregated_data(agg_level)
            df_plot = df_plot.dropna(subset=['avg_income', 'avg_age'])

            # Prepare hover data
            hover_cols = ['id']
            if 'postcode' in df_plot.columns:
                hover_cols.append('postcode')
            if 'suburb' in df_plot.columns:
                hover_cols.append('suburb')

            fig = px.scatter(
                df_plot,
                x='avg_age',
                y='avg_income',
                color='population_density',
                title=f"Average Income vs Average Age ({agg_level} level)",
                labels={'avg_age': 'Average Age', 'avg_income': 'Average Income ($)',
                       'population_density': 'Population Density'},
                hover_data=hover_cols
            )

            st.plotly_chart(fig, use_container_width=True)
            st.info(f"Showing {len(df_plot)} {agg_level}{'s' if agg_level != 'SA1' else ' areas'}")

        else:  # Histogram
            # Aggregation level selector
            agg_level = st.selectbox(
                "Aggregation Level",
                ["SA1", "Postcode", "Suburb"],
                help="SA1: Smallest geographic unit\nPostcode: Aggregate by postcode\nSuburb: Aggregate by suburb",
                key="income_hist_agg_level"
            )

            # Get data at selected aggregation level
            df_plot = load_aggregated_data(agg_level)
            df_plot = df_plot.dropna(subset=['avg_income'])

            fig = px.histogram(
                df_plot,
                x='avg_income',
                nbins=50,
                title=f"Distribution of Average Income ({agg_level} level)",
                labels={'avg_income': 'Average Income ($)'}
            )

            st.plotly_chart(fig, use_container_width=True)
            st.info(f"Showing {len(df_plot)} {agg_level}{'s' if agg_level != 'SA1' else ' areas'}")

    # ===== COUNTRY OF ORIGIN ANALYSIS =====
    elif page == "Country of Origin Analysis":
        st.header("Country of Origin Analysis")

        tab1, tab2 = st.tabs(["📊 Country Statistics", "🗺️ Geographic Distribution"])

        with tab1:
            # Filter out countries with no data
            country_clean = country_processed.dropna(subset=['avg_income'])

            metric = st.selectbox(
                "Select Metric",
                ["Average Income", "Average Hours Worked", "Hourly Wage",
                 "Education Level (Postgraduate %)", "Education Level (Bachelor %)"]
            )

            column_map = {
                "Average Income": "avg_income",
                "Average Hours Worked": "avg_hours_worked",
                "Hourly Wage": "hourly_wage",
                "Education Level (Postgraduate %)": "postgraduate_pct",
                "Education Level (Bachelor %)": "bachelor_pct"
            }

            col_name = column_map[metric]

            # Option to limit number of countries displayed
            show_all = st.checkbox("Show all countries", value=False)

            df_plot = country_clean.dropna(subset=[col_name]).sort_values(col_name, ascending=False)

            if not show_all:
                num_countries = st.slider("Number of countries to display", 10, 100, 30)
                df_plot = df_plot.head(num_countries)
                title_text = f"Top {num_countries} Countries by {metric}"
            else:
                title_text = f"All Countries by {metric}"

            fig = px.bar(
                df_plot,
                x=col_name,
                y='Country',
                orientation='h',
                title=title_text,
                labels={col_name: metric},
                height=max(800, len(df_plot) * 20)  # Adjust height based on number of countries
            )

            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            st.subheader("Detailed Statistics")
            display_cols = ['Country', 'avg_income', 'avg_hours_worked', 'hourly_wage',
                           'postgraduate_pct', 'bachelor_pct']
            available_cols = [col for col in display_cols if col in country_clean.columns]

            # Show all countries in table if requested
            num_to_show = len(country_clean) if show_all else 50
            st.dataframe(
                country_clean[available_cols].sort_values('avg_income', ascending=False).head(num_to_show),
                use_container_width=True
            )

        with tab2:
            st.subheader("Geographic Distribution of Country of Origin")

            col1, col2, col3 = st.columns(3)

            with col1:
                # Aggregation level selector
                agg_level = st.selectbox(
                    "Aggregation Level",
                    ["SA1", "Postcode", "Suburb"],
                    help="SA1: Smallest geographic unit\nPostcode: Aggregate by postcode\nSuburb: Aggregate by suburb",
                    key="country_map_agg_level"
                )

            with col2:
                # View mode selector (counts vs percentages)
                view_mode = st.selectbox(
                    "View Mode",
                    ["Percentage (%)", "Raw Counts"],
                    help="Percentage: % of population\nRaw Counts: Actual number of people",
                    key="country_map_view_mode"
                )

            # Load appropriate data based on view mode
            if view_mode == "Percentage (%)":
                master_data = load_master_pct_data(agg_level)
                value_suffix = "%"
            else:
                master_data = load_master_data(agg_level)
                value_suffix = "people"

            # Get list of countries from column names
            country_cols = [col for col in master_data.columns if col.startswith('country_')]
            country_names = [col.replace('country_', '') for col in country_cols]

            # Sort countries by total for easier selection (using counts for sorting even in pct mode)
            if view_mode == "Percentage (%)":
                # Load counts just for sorting
                master_counts = load_master_data(agg_level)
                country_totals = {name: master_counts[f'country_{name}'].sum() for name in country_names}
            else:
                country_totals = {name: master_data[f'country_{name}'].sum() for name in country_names}

            country_names_sorted = sorted(country_names, key=lambda x: country_totals[x], reverse=True)

            with col3:
                # Country selector
                selected_country = st.selectbox(
                    "Select Country of Origin",
                    country_names_sorted,
                    help="Countries sorted by total population",
                    key="country_map_country"
                )

            if selected_country:
                col_name = f'country_{selected_country}'

                # Prepare data for mapping
                df_plot = master_data[['latitude', 'longitude', 'area_km2', col_name]].copy()
                df_plot = df_plot.dropna(subset=[col_name, 'latitude', 'longitude'])
                df_plot = df_plot[df_plot[col_name] > 0]  # Only show areas with people from this country

                if len(df_plot) > 0:
                    show_bounds = agg_level in ['Postcode', 'Suburb']

                    title_text = f"{selected_country} - {view_mode} across Victoria ({agg_level} level)"

                    fig = create_choropleth_map(
                        df_plot,
                        col_name,
                        title_text,
                        color_scale="Viridis",
                        show_boundaries=show_bounds
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Summary statistics
                    total_value = df_plot[col_name].sum()
                    num_areas = len(df_plot)
                    avg_per_area = total_value / num_areas if num_areas > 0 else 0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if view_mode == "Percentage (%)":
                            st.metric("Average %", f"{avg_per_area:.2f}%")
                        else:
                            st.metric("Total Population", f"{total_value:,.0f}")
                    with col2:
                        st.metric(f"Number of {agg_level}s", f"{num_areas:,}")
                    with col3:
                        if view_mode == "Percentage (%)":
                            st.metric("Max %", f"{df_plot[col_name].max():.2f}%")
                        else:
                            st.metric(f"Average per {agg_level}", f"{avg_per_area:,.1f}")
                else:
                    st.warning(f"No data available for {selected_country} at {agg_level} level")

    # ===== MARKET RESEARCH TOOL =====
    elif page == "Market Research Tool":
        st.header("🎯 Market Research Tool")
        st.markdown("""
        Analyze business locations and identify optimal spots for new businesses based on population catchment areas.
        """)

        # Initialize session state for the tool
        if 'market_tool' not in st.session_state:
            # Load percentage data for detailed demographic analysis
            sa_master_pct = pd.read_csv("Processed/Sa_Master_Pct.csv")
            st.session_state.market_tool = MarketResearchTool(sa_processed, sa_master_pct)

        tool = st.session_state.market_tool

        # Tabs for different functions
        tab1, tab2, tab3 = st.tabs(["📍 Manage Locations", "📊 Analysis", "🎯 Find Optimal Location"])

        with tab1:
            st.subheader("Business Locations")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Add New Business Location**")
                new_name = st.text_input("Business Name", key="new_biz_name")
                new_lat = st.number_input("Latitude", value=-37.8136, format="%.6f", key="new_lat")
                new_lon = st.number_input("Longitude", value=144.9631, format="%.6f", key="new_lon")

                if st.button("Add Business"):
                    if new_name:
                        tool.add_business(new_name, new_lat, new_lon)
                        st.success(f"Added {new_name}!")
                        st.rerun()
                    else:
                        st.error("Please enter a business name")

                st.markdown("---")
                st.write("**Bulk Import**")
                st.write("Paste locations in format: `name,latitude,longitude` (one per line)")
                bulk_input = st.text_area(
                    "Paste locations",
                    height=100,
                    placeholder="Business 1,-37.8136,144.9631\nBusiness 2,-37.8200,144.9700",
                    key="bulk_import"
                )

                if st.button("Import Locations"):
                    if bulk_input.strip():
                        lines = bulk_input.strip().split('\n')
                        success_count = 0
                        error_count = 0

                        for line in lines:
                            try:
                                parts = [p.strip() for p in line.split(',')]
                                if len(parts) == 3:
                                    name, lat, lon = parts
                                    tool.add_business(name, float(lat), float(lon))
                                    success_count += 1
                                else:
                                    error_count += 1
                            except Exception:
                                error_count += 1

                        if success_count > 0:
                            st.success(f"Imported {success_count} location(s)!")
                        if error_count > 0:
                            st.warning(f"Failed to import {error_count} line(s). Check format.")
                        st.rerun()
                    else:
                        st.error("Please paste location data")

                st.info("💡 **Tip**: Use the map below to find coordinates, or search Google Maps for your location")

            with col2:
                st.write("**Current Businesses**")
                if tool.businesses:
                    for biz in tool.businesses:
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.write(f"**{biz['name']}** - ({biz['lat']:.4f}, {biz['lon']:.4f})")
                        with col_b:
                            if st.button("Remove", key=f"remove_{biz['name']}"):
                                tool.remove_business(biz['name'])
                                st.rerun()
                else:
                    st.write("No businesses added yet")

            # Show catchment map
            if tool.businesses:
                st.subheader("Catchment Area Visualization")
                fig = tool.visualize_catchments()
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add businesses above to see catchment areas")

        with tab2:
            st.subheader("Catchment Analysis")

            if not tool.businesses:
                st.warning("Please add businesses in the 'Manage Locations' tab first")
            else:
                # Select business to analyze
                business_names = [b['name'] for b in tool.businesses]
                selected_business = st.selectbox("Select Business", ["All Businesses"] + business_names)

                biz_name = None if selected_business == "All Businesses" else selected_business

                # Get summary
                summary = tool.get_catchment_summary(biz_name)

                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Population", f"{summary['total_population']:,.0f}")
                with col2:
                    st.metric("Number of SA1 Areas", f"{summary['num_areas']:,}")
                with col3:
                    st.metric("Avg Income", f"${summary['avg_income']:,.0f}")
                with col4:
                    st.metric("Avg Age", f"{summary['avg_age']:.1f}")

                col5, col6 = st.columns(2)
                with col5:
                    st.metric("Avg Distance", f"{summary['avg_distance']:.4f}°")
                with col6:
                    st.metric("Max Distance", f"{summary['max_distance']:.4f}°")

                # Show summary for each business
                st.subheader("Summary by Business")
                summary_data = []
                for biz in tool.businesses:
                    biz_summary = tool.get_catchment_summary(biz['name'])
                    summary_data.append({
                        'Business': biz['name'],
                        'Population': f"{biz_summary['total_population']:,.0f}",
                        'SA1 Areas': biz_summary['num_areas'],
                        'Avg Income': f"${biz_summary['avg_income']:,.0f}",
                        'Avg Age': f"{biz_summary['avg_age']:.1f}",
                        'Avg Distance': f"{biz_summary['avg_distance']:.4f}°"
                    })

                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

                # Demographic breakdown using percentage data
                if biz_name:
                    catchment_data = tool.sa_data[tool.sa_data['assigned_business'] == biz_name]
                else:
                    catchment_data = tool.sa_data

                st.subheader("Demographic Breakdown")

                # Age distribution
                age_groups = {
                    '0-14 years': 'pop_0_14',
                    '15-24 years': 'pop_15_24',
                    '25-54 years': 'pop_25_54',
                    '55-64 years': 'pop_55_64',
                    '65+ years': 'pop_65_plus'
                }

                # Check if percentage columns are available
                has_pct_data = any(col.startswith('age_') and col.endswith('_pct') for col in catchment_data.columns)

                if not has_pct_data:
                    # Calculate age percentages from absolute counts
                    age_data = {}
                    for label, col in age_groups.items():
                        if col in catchment_data.columns:
                            age_data[label] = catchment_data[col].sum()

                    total = sum(age_data.values())
                    if total > 0:
                        age_percentages = {k: (v/total)*100 for k, v in age_data.items()}

                        col_age1, col_age2 = st.columns(2)

                        with col_age1:
                            st.write("**Age Distribution**")
                            fig_age = px.bar(
                                x=list(age_percentages.keys()),
                                y=list(age_percentages.values()),
                                labels={'x': 'Age Group', 'y': 'Percentage (%)'},
                                title="Age Group Distribution"
                            )
                            st.plotly_chart(fig_age, use_container_width=True)

                        with col_age2:
                            st.write("**Age Breakdown**")
                            for label, pct in age_percentages.items():
                                st.write(f"{label}: {pct:.1f}% ({age_data[label]:,.0f} people)")
                else:
                    st.info("Detailed demographic percentage data available - consider expanding analysis features")

        with tab3:
            st.subheader("Find Optimal Location for New Business")

            if tool.businesses:
                st.write("Based on current business locations, find the best spot for a new business.")

                # Basic settings
                col1, col2 = st.columns(2)
                with col1:
                    num_suggestions = st.slider("Number of suggestions", 1, 10, 3)
                with col2:
                    min_distance = st.slider("Minimum distance from existing (degrees)", 0.0, 0.5, 0.05, 0.01)

                # Demographic targeting
                st.subheader("Target Demographics (Optional)")

                with st.expander("🎂 Age Group Targeting", expanded=False):
                    target_age_group = st.selectbox(
                        "Select target age group",
                        ["None", "0-14 years", "15-24 years", "25-54 years", "55-64 years", "65+ years"],
                        key="opt_age_group"
                    )

                with st.expander("🏠 Household Type Targeting", expanded=False):
                    st.write("Target specific household compositions:")
                    household_types = st.multiselect(
                        "Select household types",
                        ["Couples", "Lone parents", "Children under 15", "Multi-family households"],
                        key="opt_households"
                    )

                with st.expander("🏥 Health Conditions (Accessibility)", expanded=False):
                    st.write("Consider areas with specific health condition prevalence:")
                    health_focus = st.multiselect(
                        "Health conditions to consider",
                        ["Arthritis", "Asthma", "Mental health", "Mobility issues"],
                        key="opt_health"
                    )

                if st.button("Find Optimal Locations"):
                    with st.spinner("Analyzing locations..."):
                        target_demo = None
                        if target_age_group != "None":
                            age_map = {
                                "0-14 years": "pop_0_14",
                                "15-24 years": "pop_15_24",
                                "25-54 years": "pop_25_54",
                                "55-64 years": "pop_55_64",
                                "65+ years": "pop_65_plus"
                            }
                            target_demo = {'age_group': age_map[target_age_group]}

                        optimal_locations = tool.find_optimal_location(
                            num_locations=num_suggestions,
                            target_demographics=target_demo,
                            min_distance_from_existing=min_distance
                        )

                        if optimal_locations:
                            st.success(f"Found {len(optimal_locations)} optimal locations!")

                            # Display results
                            for i, loc in enumerate(optimal_locations, 1):
                                with st.expander(f"Option {i}: {loc.get('suburb', 'Unknown')} ({loc['postcode']}) - Score: {loc['score']:.3f}"):
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.write(f"**SA1 Code**: {loc['SA1']}")
                                        st.write(f"**Coordinates**: {loc['latitude']:.4f}, {loc['longitude']:.4f}")
                                        st.write(f"**Postcode**: {loc['postcode']}")
                                        st.write(f"**Suburb**: {loc.get('suburb', 'N/A')}")
                                    with col_b:
                                        st.write(f"**Population**: {loc['population']:.0f}")
                                        st.write(f"**Pop. Density**: {loc['population_density']:.1f} /km²")
                                        st.write(f"**Optimization Score**: {loc['score']:.3f}")

                            # Visualize suggestions on map
                            st.subheader("Suggested Locations on Map")
                            fig = tool.visualize_catchments()

                            # Add suggested locations
                            suggest_lats = [loc['latitude'] for loc in optimal_locations]
                            suggest_lons = [loc['longitude'] for loc in optimal_locations]
                            suggest_labels = [f"Option {i}" for i in range(1, len(optimal_locations) + 1)]

                            fig.add_trace(go.Scattermapbox(
                                lat=suggest_lats,
                                lon=suggest_lons,
                                mode='markers+text',
                                marker=dict(size=15, color='green', symbol='circle'),
                                text=suggest_labels,
                                textposition='top center',
                                name='Suggested Locations',
                                hovertemplate='<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>'
                            ))

                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No suitable locations found with current criteria. Try adjusting parameters.")
            else:
                st.info("Add some existing business locations first to find gaps in the market")
                st.write("Go to the 'Manage Locations' tab to add businesses.")


if __name__ == "__main__":
    main()

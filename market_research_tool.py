"""
Market Research Tool for Business Location Optimization
Uses nearest-neighbor analysis to determine catchment areas and identify gaps
"""

import pandas as pd
import numpy as np
from scipy.spatial import cKDTree, distance
import plotly.graph_objects as go
import plotly.express as px


class MarketResearchTool:
    """
    Tool for analyzing business locations and identifying optimal new locations
    """

    def __init__(self, sa_processed_df, sa_master_pct_df=None):
        """
        Initialize with SA1 processed data

        Args:
            sa_processed_df: DataFrame with SA1 areas including lat/lon and demographics
            sa_master_pct_df: DataFrame with percentage data for detailed analysis (optional)
        """
        self.sa_data = sa_processed_df.dropna(subset=['latitude', 'longitude']).copy()
        self.sa_data['assigned_business'] = None
        self.sa_data['distance_to_business'] = np.inf

        # Store percentage data for detailed demographic analysis
        self.sa_master_pct = sa_master_pct_df

        # Merge percentage data if available
        if self.sa_master_pct is not None:
            # Add some key percentage columns to sa_data for analysis
            pct_cols_to_add = []
            for col in self.sa_master_pct.columns:
                if any(col.startswith(prefix) for prefix in ['age_', 'households_', 'counthealth_', 'typehealth_']):
                    pct_cols_to_add.append(col)

            if pct_cols_to_add and 'SA1' in self.sa_master_pct.columns:
                pct_data = self.sa_master_pct[['SA1'] + pct_cols_to_add]
                self.sa_data = self.sa_data.merge(pct_data, on='SA1', how='left')

        # Create spatial index for fast nearest-neighbor queries
        self.sa_coords = self.sa_data[['latitude', 'longitude']].values
        self.sa_tree = cKDTree(self.sa_coords)

        self.businesses = []  # List of business locations

    def add_business(self, name, lat, lon):
        """Add a business location"""
        business = {
            'name': name,
            'lat': lat,
            'lon': lon,
            'catchment': []
        }
        self.businesses.append(business)
        self._recalculate_catchments()
        return business

    def remove_business(self, name):
        """Remove a business by name"""
        self.businesses = [b for b in self.businesses if b['name'] != name]
        self._recalculate_catchments()

    def _recalculate_catchments(self):
        """Recalculate catchment areas for all businesses"""
        if not self.businesses:
            self.sa_data['assigned_business'] = None
            self.sa_data['distance_to_business'] = np.inf
            for business in self.businesses:
                business['catchment'] = []
            return

        # Reset assignments
        self.sa_data['assigned_business'] = None
        self.sa_data['distance_to_business'] = np.inf

        # For each SA1 area, find the nearest business
        for idx, row in self.sa_data.iterrows():
            sa_coords = (row['latitude'], row['longitude'])
            min_dist = np.inf
            nearest_business = None

            for business in self.businesses:
                biz_coords = (business['lat'], business['lon'])
                dist = distance.euclidean(sa_coords, biz_coords)

                if dist < min_dist:
                    min_dist = dist
                    nearest_business = business['name']

            self.sa_data.loc[idx, 'assigned_business'] = nearest_business
            self.sa_data.loc[idx, 'distance_to_business'] = min_dist

        # Update catchment lists for businesses
        for business in self.businesses:
            business['catchment'] = self.sa_data[
                self.sa_data['assigned_business'] == business['name']
            ]['SA1'].tolist()

    def get_catchment_summary(self, business_name=None, demographic_filters=None):
        """
        Get summary statistics for a business's catchment area

        Args:
            business_name: Name of business (if None, returns summary for all)
            demographic_filters: Dict of filters like {'min_age': 25, 'max_age': 54}

        Returns:
            Dictionary with summary statistics
        """
        if business_name:
            catchment_data = self.sa_data[self.sa_data['assigned_business'] == business_name]
        else:
            catchment_data = self.sa_data.copy()

        # Apply demographic filters if provided
        if demographic_filters:
            if 'min_age' in demographic_filters and 'max_age' in demographic_filters:
                # This would require the full sa_master data with individual age columns
                pass
            if 'min_income' in demographic_filters:
                catchment_data = catchment_data[
                    catchment_data['avg_income'] >= demographic_filters['min_income']
                ]
            if 'max_income' in demographic_filters:
                catchment_data = catchment_data[
                    catchment_data['avg_income'] <= demographic_filters['max_income']
                ]

        summary = {
            'total_population': catchment_data['total_population'].sum(),
            'num_areas': len(catchment_data),
            'avg_income': catchment_data['avg_income'].mean(),
            'avg_age': catchment_data['avg_age'].mean(),
            'avg_distance': catchment_data['distance_to_business'].mean(),
            'max_distance': catchment_data['distance_to_business'].max(),
        }

        return summary

    def find_optimal_location(self, num_locations=1, target_demographics=None,
                            min_distance_from_existing=0.05):
        """
        Find optimal location(s) for new business

        Args:
            num_locations: Number of new locations to suggest
            target_demographics: Dict of target criteria (e.g., {'age_group': 'pop_25_54'})
            min_distance_from_existing: Minimum distance from existing businesses (degrees)

        Returns:
            List of suggested locations with scores
        """
        # Create a grid of potential locations
        # For simplicity, use existing SA1 centroids as candidates

        candidates = self.sa_data.copy()

        # Filter out locations too close to existing businesses
        if self.businesses and min_distance_from_existing > 0:
            for business in self.businesses:
                biz_coords = np.array([[business['lat'], business['lon']]])
                distances = distance.cdist(
                    candidates[['latitude', 'longitude']].values,
                    biz_coords
                ).flatten()
                candidates = candidates[distances >= min_distance_from_existing]

        if len(candidates) == 0:
            return []

        # Score each candidate based on:
        # 1. Population density
        # 2. Target demographics
        # 3. Distance from existing businesses (prefer locations that capture unserved population)

        candidates['score'] = 0.0

        # Population score
        if 'population_density' in candidates.columns:
            pop_normalized = (candidates['population_density'] -
                            candidates['population_density'].min()) / \
                           (candidates['population_density'].max() -
                            candidates['population_density'].min())
            candidates['score'] += pop_normalized * 0.4

        # Target demographic score
        if target_demographics:
            if 'age_group' in target_demographics:
                age_col = target_demographics['age_group']
                if age_col in candidates.columns:
                    age_normalized = (candidates[age_col] - candidates[age_col].min()) / \
                                   (candidates[age_col].max() - candidates[age_col].min())
                    candidates['score'] += age_normalized * 0.4

        # Distance from existing businesses (higher = better for gap-filling)
        if self.businesses:
            dist_normalized = (candidates['distance_to_business'] -
                             candidates['distance_to_business'].min()) / \
                            (candidates['distance_to_business'].max() -
                             candidates['distance_to_business'].min())
            candidates['score'] += dist_normalized * 0.2

        # Sort by score and return top candidates
        top_candidates = candidates.nlargest(num_locations, 'score')

        results = []
        for _, row in top_candidates.iterrows():
            results.append({
                'SA1': row['SA1'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'postcode': row['postcode'],
                'suburb': row['suburb'],
                'score': row['score'],
                'population': row['total_population'],
                'population_density': row['population_density']
            })

        return results

    def visualize_catchments(self):
        """Create a visualization of business catchment areas"""
        if not self.businesses:
            return None

        # Create a color map for businesses
        business_names = [b['name'] for b in self.businesses]
        colors = px.colors.qualitative.Set1[:len(business_names)]
        color_map = dict(zip(business_names, colors))

        fig = go.Figure()

        # Plot catchment areas
        for business_name, color in color_map.items():
            catchment_data = self.sa_data[self.sa_data['assigned_business'] == business_name]

            if len(catchment_data) > 0:
                fig.add_trace(go.Scattermapbox(
                    lat=catchment_data['latitude'],
                    lon=catchment_data['longitude'],
                    mode='markers',
                    marker=dict(size=8, color=color, opacity=0.6),
                    name=f'{business_name} Catchment',
                    text=catchment_data['SA1'],
                    hovertemplate=(
                        '<b>%{text}</b><br>' +
                        'Population: %{customdata[0]:.0f}<br>' +
                        'Distance: %{customdata[1]:.3f}°<br>' +
                        '<extra></extra>'
                    ),
                    customdata=catchment_data[['total_population', 'distance_to_business']].values
                ))

        # Plot business locations
        biz_lats = [b['lat'] for b in self.businesses]
        biz_lons = [b['lon'] for b in self.businesses]
        biz_names = [b['name'] for b in self.businesses]

        fig.add_trace(go.Scattermapbox(
            lat=biz_lats,
            lon=biz_lons,
            mode='markers+text',
            marker=dict(size=20, color='red', symbol='star'),
            text=biz_names,
            textposition='top center',
            name='Business Locations',
            hovertemplate='<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>'
        ))

        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=-37.8, lon=145),
                zoom=8
            ),
            height=700,
            title="Business Catchment Areas",
            showlegend=True
        )

        return fig


# Example usage function
def demo():
    """Demonstrate the market research tool"""
    # Load data
    sa_processed = pd.read_csv("Processed/Sa_Master_Processed.csv")

    # Initialize tool
    tool = MarketResearchTool(sa_processed)

    # Add some example businesses
    tool.add_business("Business A", -37.8136, 144.9631)  # Melbourne CBD
    tool.add_business("Business B", -37.9716, 145.2306)  # Dandenong

    # Get catchment summary
    summary_a = tool.get_catchment_summary("Business A")
    print(f"Business A Catchment: {summary_a}")

    # Find optimal location for new business
    optimal = tool.find_optimal_location(num_locations=3)
    print(f"\nOptimal locations: {optimal}")

    # Visualize
    fig = tool.visualize_catchments()
    if fig:
        fig.show()


if __name__ == "__main__":
    demo()

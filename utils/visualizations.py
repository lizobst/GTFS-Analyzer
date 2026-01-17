import folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def create_route_map(gtfs_data, route_details=None, center_lat=None, center_lon=None):
    """
    Create an interactive Folium map showing routes and stops.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        route_details (dict, optional): Details for a specific route from get_route_details()
        center_lat (float, optional): Latitude for map center
        center_lon (float, optional): Longitude for map center

    Returns:
        folium.Map: Interactive map object
    """

    # Determine map center
    if center_lat is None or center_lon is None:
        if route_details and 'stops' in route_details:
            # Center on route's stops
            center_lat = route_details['stops']['stop_lat'].mean()
            center_lon = route_details['stops']['stop_lon'].mean()
        else:
            # Center on all stops
            center_lat = gtfs_data['stops']['stop_lat'].mean()
            center_lon = gtfs_data['stops']['stop_lon'].mean()

    # Adjust center slightly north to account for map viewport
    center_lat = center_lat + 0.02

    # Create base map
    map_obj = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    if route_details:
        # Single route view
        route_color = '#0066CC'  # Blue

        # Draw route shape if available
        if route_details.get('shape_coords'):
            folium.PolyLine(
                locations=route_details['shape_coords'],
                color=route_color,
                weight=4,
                opacity=0.7,
                popup=f"Route {route_details['short_name']}: {route_details['long_name']}",
                tooltip=f"Route {route_details['short_name']}"
            ).add_to(map_obj)

        # Add stops as markers
        if 'stops' in route_details:
            for idx, stop in route_details['stops'].iterrows():
                popup_text = f"""
                <b>{stop['stop_name']}</b><br>
                Stop ID: {stop['stop_id']}<br>
                Route: {route_details['short_name']} - {route_details['long_name']}
                """

                folium.CircleMarker(
                    location=[stop['stop_lat'], stop['stop_lon']],
                    radius=5,
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=stop['stop_name'],
                    color=route_color,
                    fill=True,
                    fillColor='white',
                    fillOpacity=0.8,
                    weight=2
                ).add_to(map_obj)

    else:
        # System overview - show all stops (simplified)
        # Sample stops to avoid overloading the map
        all_stops = gtfs_data['stops'].sample(min(500, len(gtfs_data['stops'])))

        for idx, stop in all_stops.iterrows():
            folium.CircleMarker(
                location=[stop['stop_lat'], stop['stop_lon']],
                radius=3,
                popup=stop['stop_name'],
                tooltip=stop['stop_name'],
                color='#666666',
                fill=True,
                fillColor='#999999',
                fillOpacity=0.6,
                weight=1
            ).add_to(map_obj)

    return map_obj


def create_headway_distribution(frequency_data):
    """
    Create a histogram of route headways.

    Args:
        frequency_data (DataFrame): Output from calculate_route_frequencies()
                                   Must have 'avg_headway_min' column

    Returns:
        plotly.graph_objects.Figure: Interactive histogram
    """
    fig = px.histogram(
        frequency_data,
        x='avg_headway_min',
        nbins=30,
        title='Distribution of Route Headways',
        labels={'avg_headway_min': 'Average Headway (minutes)', 'count': 'Number of Routes'},
        color_discrete_sequence=['#0066CC']
    )

    fig.update_layout(
        xaxis_title='Average Headway (minutes)',
        yaxis_title='Number of Routes',
        showlegend=False,
        hovermode='x'
    )

    # Add mean line
    mean_headway = frequency_data['avg_headway_min'].mean()
    fig.add_vline(
        x=mean_headway,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_headway:.1f} min"
    )

    fig.update_xaxes(
        title='Average Headway (minutes)',
        showgrid=False  # Add this
    )

    fig.update_yaxes(
        title='Number of Routes',
        showgrid=False  # Add this
    )

    return fig


def create_trips_by_hour_chart(trips_by_hour_data):
    """
    Create a bar chart of trips starting each hour.

    Args:
        trips_by_hour_data (DataFrame): Output from calculate_trips_by_hour()
                                       Must have 'hour' and 'trip_count' columns

    Returns:
        plotly.graph_objects.Figure: Interactive bar chart
    """
    fig = px.bar(
        trips_by_hour_data,
        x='hour',
        y='trip_count',
        title='Trips by Hour of Day',
        labels={'hour': 'Hour of Day', 'trip_count': 'Number of Trips'},
        color='trip_count',
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        xaxis_title='Hour of Day',
        yaxis_title='Number of Trips',
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1
        ),
        showlegend=False,
        hovermode='x'
    )

    # Add peak period shading
    # AM Peak (6-9)
    fig.add_vrect(
        x0=6, x1=9,
        fillcolor="orange", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="AM Peak", annotation_position="top left"
    )

    # PM Peak (15-18)
    fig.add_vrect(
        x0=15, x1=18,
        fillcolor="orange", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="PM Peak", annotation_position="top left"
    )

    fig.update_xaxes(
        title='Hour of Day',
        tickmode='linear',
        tick0=0,
        dtick=1,
        showgrid=False  # Add this
    )

    fig.update_yaxes(
        title='Number of Trips',
        showgrid=False  # Add this
    )

    return fig


def create_system_overview_map(gtfs_data, sample_routes=10):
    """
    Create a map showing multiple routes on the system.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        sample_routes (int): Number of routes to display

    Returns:
        folium.Map: Interactive map with multiple routes
    """
    # Get center based on stop activity (weighted by trips), not just geography
    if 'stop_times' in gtfs_data and 'stops' in gtfs_data:
        # Count trips per stop
        stop_activity = gtfs_data['stop_times'].groupby('stop_id').size().reset_index(name='trip_count')
        stops_with_activity = pd.merge(gtfs_data['stops'], stop_activity, on='stop_id')

        # Filter to top 50% most active stops for centering
        threshold = stops_with_activity['trip_count'].quantile(0.5)
        active_stops = stops_with_activity[stops_with_activity['trip_count'] >= threshold]

        center_lat = active_stops['stop_lat'].mean()
        center_lon = active_stops['stop_lon'].mean()
    else:
        # Fallback to simple mean
        center_lat = gtfs_data['stops']['stop_lat'].mean()
        center_lon = gtfs_data['stops']['stop_lon'].mean()

    # Adjust center slightly north to account for map viewport
    center_lat = center_lat + 0.02

    # Create base map
    map_obj = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # Get sample of routes (or all if sample_routes >= total routes)
    total_routes = len(gtfs_data['routes'])
    if sample_routes >= total_routes:
        sample_route_ids = gtfs_data['routes']['route_id'].tolist()
    else:
        sample_route_ids = gtfs_data['routes']['route_id'].sample(sample_routes).tolist()

    # Use single blue color for all routes
    route_color = '#0066CC'

    if 'shapes' in gtfs_data:
        for idx, route_id in enumerate(sample_route_ids):
            # Get route info
            route_info = gtfs_data['routes'][gtfs_data['routes']['route_id'] == route_id].iloc[0]

            # Get trips for this route
            route_trips = gtfs_data['trips'][gtfs_data['trips']['route_id'] == route_id]

            if len(route_trips) > 0:
                # Get most common shape
                shape_id = route_trips['shape_id'].mode()[0] if 'shape_id' in route_trips.columns else None

                if shape_id and shape_id in gtfs_data['shapes']['shape_id'].values:
                    shape_data = gtfs_data['shapes'][gtfs_data['shapes']['shape_id'] == shape_id]
                    shape_data = shape_data.sort_values('shape_pt_sequence')

                    coords = shape_data[['shape_pt_lat', 'shape_pt_lon']].values.tolist()


                    folium.PolyLine(
                        locations=coords,
                        color=route_color,
                        weight=3,
                        opacity=0.7,
                        popup=f"Route {route_info['route_short_name']}: {route_info['route_long_name']}",
                        tooltip=f"Route {route_info['route_short_name']}"
                    ).add_to(map_obj)

    return map_obj

def create_peak_offpeak_chart(peak_offpeak_data):
    """
        Create a bar chart comparing service levels across time periods.

        Args:
            peak_offpeak_data (DataFrame): Output from calculate_peak_offpeak_metrics()
                                           Must have 'time_block', 'n_trips', 'pct_of_service'

        Returns:
            plotly.graph_objects.Figure: Interactive bar chart
        """
    # Remove NaN rows if any
    data = peak_offpeak_data.dropna(subset=['time_block'])

    fig = go.Figure()

    # Add bars for number of trips
    fig.add_trace(go.Bar(
        x=data['time_block'],
        y=data['n_trips'],
        name='Number of Trips',
        marker_color='#0066CC',
        text=data['n_trips'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Trips: %{y}<br>Routes: %{customdata}<extra></extra>',
        customdata=data['n_routes']
    ))

    fig.update_layout(
        title='Service Distribution by Time Period',
        xaxis_title='Time Period',
        yaxis_title='Number of Trips',
        hovermode='x',
        showlegend=False,
        xaxis={'categoryorder': 'array',
               'categoryarray': ['Pre-Early AM/Other', 'Early AM', 'AM Peak', 'Base', 'PM Peak', 'Evening', 'Late Evening']}
    )

    fig.update_xaxes(
        title='Time Period',
        showgrid=False  # Add this
    )

    fig.update_yaxes(
        title='Number of Trips',
        showgrid=False  # Add this
    )

    fig.update_layout(
        title='Service Distribution by Time Period',
        xaxis_tickangle=-45,
        height=500,  # Increase from 400 to 500
        showlegend=False
    )

    return fig

def create_busiest_stops_chart(stop_metrics, top_n=10):
    """
        Create a horizontal bar chart of the busiest stops.

        Args:
            stop_metrics (DataFrame): Output from calculate_stop_metrics()
                                     Must have 'stop_name', 'n_trips', 'n_routes'
            top_n (int): Number of top stops to display

        Returns:
            plotly.graph_objects.Figure: Interactive bar chart
    """
    # Get top N busiest stops
    top_stops = stop_metrics.head(top_n).copy()

    # Sort for better visualization
    top_stops = top_stops.sort_values('n_trips', ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=top_stops['stop_name'],
        x=top_stops['n_trips'],
        orientation='h',
        marker_color='#0066CC',
        text=top_stops['n_trips'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Trips: %{x}<br>Routes: %{customdata}<extra></extra>',
        customdata=top_stops['n_routes']
    ))

    fig.update_layout(
        title=f'Top {top_n} Busiest Stops',
        xaxis_title='Number of Trips',
        yaxis_title='',
        height=400 + (top_n * 20),
        showlegend=False,
        margin=dict(l=200)
    )

    fig.update_xaxes(
        title='Number of Trips',
        showgrid=False  # Add this
    )

    fig.update_yaxes(
        title='',
        showgrid=False  # Add this
    )

    return fig


def create_route_frequency_ranking(frequency_data, top_n=15):
    """
    Create a table/chart showing most and least frequent routes.

    Args:
        frequency_data (DataFrame): Output from calculate_route_frequencies()
                                   Must have 'route_long_name', 'avg_headway_min'
        top_n (int): Number of routes to show in each category

    Returns:
        plotly.graph_objects.Figure: Interactive table/chart
    """
    # Get most frequent (lowest headway) and sort ascending
    most_frequent = frequency_data.nsmallest(top_n, 'avg_headway_min').copy()
    most_frequent = most_frequent.sort_values('avg_headway_min', ascending=True)

    # Get least frequent (highest headway) and sort ascending
    least_frequent = frequency_data.nlargest(top_n, 'avg_headway_min').copy()
    least_frequent = least_frequent.sort_values('avg_headway_min', ascending=True)

    # Create subplots
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Most Frequent Routes', 'Least Frequent Routes'),
        horizontal_spacing=0.2
    )

    # Most frequent - royal blue
    fig.add_trace(
        go.Bar(
            x=most_frequent['avg_headway_min'],
            y=most_frequent['route_long_name'],
            orientation='h',
            marker_color='#4169E1',  # Royal blue
            name='Most Frequent',
            text=most_frequent['avg_headway_min'].round(1),
            textposition='outside',
            hovertemplate='%{y}<br>Headway: %{x:.1f} min<extra></extra>'
        ),
        row=1, col=1
    )

    # Least frequent - light royal blue
    fig.add_trace(
        go.Bar(
            x=least_frequent['avg_headway_min'],
            y=least_frequent['route_long_name'],
            orientation='h',
            marker_color='#87CEEB',  # Light sky blue (lighter version)
            name='Least Frequent',
            text=least_frequent['avg_headway_min'].round(1),
            textposition='outside',
            hovertemplate='%{y}<br>Headway: %{x:.1f} min<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_xaxes(title_text='Avg Headway (min)', row=1, col=1)
    fig.update_xaxes(title_text='Avg Headway (min)', row=1, col=2)

    # Update y-axes to preserve order (important!)
    fig.update_yaxes(categoryorder='array', categoryarray=most_frequent['route_long_name'].tolist(), row=1, col=1)
    fig.update_yaxes(categoryorder='array', categoryarray=least_frequent['route_long_name'].tolist(), row=1, col=2)

    fig.update_layout(
        title='Route Frequency Comparison',
        showlegend=False,
        height=max(500, 200 + (top_n * 30)),
        margin=dict(l=250)
    )

    fig.update_xaxes(
        title_text='Avg Headway (min)',
        row=1, col=1,
        showgrid=False  # Add this
    )

    fig.update_xaxes(
        title_text='Avg Headway (min)',
        row=1, col=2,
        showgrid=False  # Add this
    )

    fig.update_yaxes(
        categoryorder='array',
        categoryarray=most_frequent['route_long_name'].tolist(),
        row=1, col=1,
        showgrid=False  # Add this
    )

    fig.update_yaxes(
        categoryorder='array',
        categoryarray=least_frequent['route_long_name'].tolist(),
        row=1, col=2,
        showgrid=False  # Add this
    )

    fig.update_layout(
        title='Route Frequency Comparison',
        showlegend=False,
        height=max(600, 200 + (top_n * 30)),  # Increase from 500 to 600
        margin=dict(l=250)
    )

    return fig

def create_stop_heatmap(gtfs_data):
    """
    Create a heatmap showing stop density/concentration.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames

    Returns:
        folium.Map: Interactive heatmap
    """
    from folium.plugins import HeatMap

    # Center on active stops, not all stops
    if 'stop_times' in gtfs_data:
        # Count trips per stop
        stop_activity = gtfs_data['stop_times'].groupby('stop_id').size().reset_index(name='trip_count')
        stops_with_activity = pd.merge(gtfs_data['stops'], stop_activity, on='stop_id')

        # Center on top 50% most active stops
        threshold = stops_with_activity['trip_count'].quantile(0.5)
        active_stops = stops_with_activity[stops_with_activity['trip_count'] >= threshold]

        center_lat = active_stops['stop_lat'].mean()
        center_lon = active_stops['stop_lon'].mean()
    else:
        center_lat = gtfs_data['stops']['stop_lat'].mean()
        center_lon = gtfs_data['stops']['stop_lon'].mean()

    # Adjust center slightly north to account for map viewport
    center_lat = center_lat + 0.02

    # Create base map
    map_obj = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap'
    )

    # Prepare heatmap data: [[lat, lon, weight], ...]
    # Weight could be number of routes at stop or just 1 for each stop
    heat_data = [[row['stop_lat'], row['stop_lon']] for _, row in gtfs_data['stops'].iterrows()]

    # Add heatmap layer
    HeatMap(
        heat_data,
        radius=15,
        blur=25,
        max_zoom=13,
        min_opacity=0.3,
        gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
    ).add_to(map_obj)

    return map_obj





# Test
if __name__ == "__main__":
    from data_loader import load_gtfs_from_url
    from gtfs_parser import load_gtfs_tables, get_active_service
    from utils.metrics_calculator import (calculate_route_frequencies, calculate_trips_by_hour,
                                          get_route_details, calculate_peak_offpeak_metrics,
                                          calculate_stop_metrics)

    # Load GTFS data
    print("Loading GTFS data...")
    url = 'https://www.viainfo.net/BusService/google_transit.zip'
    gtfs_dir = load_gtfs_from_url(url)
    gtfs_data = load_gtfs_tables(gtfs_dir)

    # Get active service
    active_services = get_active_service(gtfs_data, '2025-12-23')
    print(f"Active services: {active_services}")

    # 1. Headway distribution
    print("\nCreating headway distribution chart...")
    frequencies = calculate_route_frequencies(gtfs_data, service_id=active_services[0])
    headway_chart = create_headway_distribution(frequencies)
    headway_chart.write_html('headway_distribution.html')
    print("✓ Headway chart saved")

    # 2. Trips by hour
    print("\nCreating trips by hour chart...")
    trips_by_hour = calculate_trips_by_hour(gtfs_data, service_id=active_services[0])
    hour_chart = create_trips_by_hour_chart(trips_by_hour)
    hour_chart.write_html('trips_by_hour.html')
    print("✓ Trips by hour chart saved")

    # 3. System overview map
    print("\nCreating system overview map...")
    system_map = create_system_overview_map(gtfs_data, sample_routes=15)
    system_map.save('system_overview.html')
    print("✓ System map saved")

    # 4. Route-specific map
    print("\nCreating route 288 map...")
    route_details = get_route_details(gtfs_data, route_id='288', service_id=active_services[0])
    route_map = create_route_map(gtfs_data, route_details=route_details)
    route_map.save('route_288_map.html')
    print("✓ Route 288 map saved")

    # 5. Peak vs off-peak
    print("\nCreating peak/off-peak chart...")
    peak_metrics = calculate_peak_offpeak_metrics(gtfs_data, service_id=active_services[0])
    peak_chart = create_peak_offpeak_chart(peak_metrics)
    peak_chart.write_html('peak_offpeak.html')
    print("✓ Peak/off-peak chart saved")

    # 6. Busiest stops
    print("\nCreating busiest stops chart...")
    stop_metrics = calculate_stop_metrics(gtfs_data, service_id=active_services[0])
    stops_chart = create_busiest_stops_chart(stop_metrics, top_n=15)
    stops_chart.write_html('busiest_stops.html')
    print("✓ Busiest stops chart saved")

    # 7. Route frequency ranking
    print("\nCreating route frequency ranking...")
    freq_ranking = create_route_frequency_ranking(frequencies, top_n=10)
    freq_ranking.write_html('route_frequency_ranking.html')
    print("✓ Route frequency ranking saved")

    # 8. Stop heatmap
    print("\nCreating stop heatmap...")
    heatmap = create_stop_heatmap(gtfs_data)
    heatmap.save('stop_heatmap.html')
    print("✓ Stop heatmap saved")

    print("\n✅ All 8 visualizations created! Open the HTML files in your browser.")
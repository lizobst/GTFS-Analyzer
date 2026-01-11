import pandas as pd
import numpy as np
from datetime import timedelta


def calculate_system_metrics(gtfs_data):
    """
    Calculate high-level system metrics from GTFS data.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames

    Returns:
        dict: Dictionary of metric names and values
              Example: {'total_routes': 50, 'total_stops': 1200, ...}
    """

    metrics = {}

    metrics['total_routes'] = len(gtfs_data['routes'])
    metrics['total_stops'] = len(gtfs_data['stops'])
    metrics['total_trips'] = len(gtfs_data['trips'])

    if 'shapes' in gtfs_data:
        metrics['total_shapes'] = gtfs_data['shapes']['shape_id'].nunique()

    return metrics

def calculate_route_frequencies(gtfs_data, service_id=None):
    """
    Calculate average headways (frequency) for each route.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        service_id (str, optional): Filter to specific service_id (e.g., weekday vs weekend)

    Returns:
        DataFrame: Route information with average headways in minutes
    """
    def time_to_minutes(time_str):
        """Convert HH:MM:SS string to total minutes"""
        h, m, s = map(int, time_str.split(':'))
        return h * 60 + m + s/60

    # Merge tables
    routes_trips = pd.merge(gtfs_data['routes'], gtfs_data['trips'], on='route_id')
    routes_stop_times = pd.merge(routes_trips, gtfs_data['stop_times'], on='trip_id')

    # Filter by service_id if provided
    if service_id is not None:
        routes_stop_times = routes_stop_times[routes_stop_times['service_id'] == service_id]

    # Convert departure time to minutes
    routes_stop_times['departure_mins'] = routes_stop_times['departure_time'].apply(time_to_minutes)

    # Get first stop of each trip
    first_stops = routes_stop_times.loc[
        routes_stop_times.groupby('trip_id')['stop_sequence'].idxmin()
    ]

    # Sort by route and departure time
    first_stops = first_stops.sort_values(['route_id','departure_mins'])

    # Calculate headway - time between consecutive trips on the same route
    first_stops['headway_min'] = first_stops.groupby('route_id')['departure_mins'].diff()

    avg_headway = (
        first_stops
        .groupby(['route_id', 'route_short_name', 'route_long_name'])['headway_min']
        .mean()
        .reset_index(name='avg_headway_min')
    )

    # Sort by frequency - lowest headway = most frequent
    avg_headway = avg_headway.sort_values('avg_headway_min')

    return avg_headway


def calculate_service_hours(gtfs_data, service_id=None):
    """
    Calculate total revenue hours and average trip duration.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        service_id (str, optional): Filter to specific service_id

    Returns:
        dict: Dictionary with 'total_revenue_hours' and 'avg_trip_duration_min'
    """

    def time_to_seconds(time_str):
        """Convert HH:MM:SS string to total seconds"""
        try:
            if pd.isna(time_str) or time_str == '' or time_str is None:
                return None
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except (ValueError, AttributeError):
            return None

    # Merge trips with stop times
    trips_stops = pd.merge(gtfs_data['trips'], gtfs_data['stop_times'], on='trip_id')

    # Filter by service_id if provided
    if service_id is not None:
        trips_stops = trips_stops[trips_stops['service_id'] == service_id]

    # Convert time to seconds
    trips_stops['arr_sec'] = trips_stops['arrival_time'].apply(time_to_seconds)
    trips_stops['dep_sec'] = trips_stops['departure_time'].apply(time_to_seconds)

    # Get first departure and last arrival for each trip
    trip_times = (
        trips_stops
        .sort_values('trip_id')
        .groupby('trip_id')
        .agg(
            start_time=('dep_sec', 'min'),
            end_time=('arr_sec', 'max')
        )
    )

    # Calculate trip duration in minutes
    trip_times['trip_duration_min'] = (
    (trip_times['end_time'] - trip_times['start_time']) / 60
    )

    # Calculate summary metrics
    metrics = {
        'total_revenue_hours': trip_times['trip_duration_min'].sum() / 60,
        'avg_trip_duration_min': trip_times['trip_duration_min'].mean(),
        'total_trips': len(trip_times)
    }

    return metrics


def calculate_stop_metrics(gtfs_data, service_id=None):
    """
    Calculate activity metrics for each stop.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        service_id (str, optional): Filter to specific service_id

    Returns:
        DataFrame: Stop metrics including trips and routes per stop, sorted by activity
    """
    # Merge trips with stop_times
    trips_stop_times = pd.merge(gtfs_data['trips'], gtfs_data['stop_times'], on='trip_id')

    # Filter by service_id if provided
    if service_id is not None:
        trips_stop_times = trips_stop_times[trips_stop_times['service_id'] == service_id]

    # Calculate metrics per stop
    stop_metrics = (
        trips_stop_times
        .groupby('stop_id')
        .agg(
            n_trips=('trip_id', 'nunique'),
            n_routes=('route_id', 'nunique')
        )
        .reset_index()
    )

    # Add stop information
    stop_metrics = pd.merge(
        stop_metrics,
        gtfs_data['stops'][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']],
        on='stop_id'
    )

    # Sort by busiest stops first
    stop_metrics = stop_metrics.sort_values('n_trips', ascending=False)

    return stop_metrics

def calculate_trips_by_hour(gtfs_data, service_id=None):
    """
    Calculate number of trips starting each hour of the day.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        service_id (str, optional): Filter to specific service_id

    Returns:
        DataFrame: Hour of day and trip counts
    """
    # Merge trips with stop_times
    trips_stop_times = pd.merge(gtfs_data['trips'], gtfs_data['stop_times'], on='trip_id')

    # Filter by service_id if provided
    if service_id is not None:
        trips_stop_times = trips_stop_times[trips_stop_times['service_id'] == service_id]

    # Get first stop of each trip
    first_stops = trips_stop_times.loc[
        trips_stop_times.groupby('trip_id')['stop_sequence'].idxmin()
    ]

    # Extract hour from departure time (HH:MM:SS string)
    first_stops['hour'] = first_stops['departure_time'].apply(lambda x: int(x.split(':')[0]))

    # Count trips per hour
    trips_by_hour = (
        first_stops
        .groupby('hour')['trip_id']
        .nunique()
        .reset_index(name='trip_count')
    )
    # Sort by hour chronologically
    trips_by_hour = trips_by_hour.sort_values('hour')

    return trips_by_hour

def calculate_peak_offpeak_metrics(gtfs_data, service_id=None):
    """
    Calculate service metrics comparing peak and off-peak periods.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        service_id (str, optional): Filter to specific service_id

    Returns:
        DataFrame: Metrics by time period
    """

    def get_time_block(time_delta):
        """
        Categorizes a Timedelta object into a defined time block.
        Args:
            time_delta (pd.Timedelta): A duration from midnight (00:00:00).
        Returns:
            str: The name of the time block.
        """
        # Define timedelta boundaries for comparison
        T0400 = timedelta(hours=4)
        T0600 = timedelta(hours=6)
        T0900 = timedelta(hours=9)
        T1500 = timedelta(hours=15)
        T1800 = timedelta(hours=18)
        T2200 = timedelta(hours=22)

        # Early AM
        if T0400 <= time_delta < T0600:
            return 'Early AM'

        # AM Peak
        elif T0600 <= time_delta < T0900:
            return 'AM Peak'

        # Base
        elif T0900 <= time_delta < T1500:
            return 'Base'

        # PM Peak
        elif T1500 <= time_delta < T1800:
            return 'PM Peak'

        # Evening
        elif T1800 <= time_delta < T2200:
            return 'Evening'

        # Late Evening
        elif time_delta >= T2200:
            return 'Late Evening'

        # Times before 04:00:00
        else:
            return 'Pre-Early AM/Other'

    # Merge trips with stop_times
    trips_stop_times = pd.merge(gtfs_data['trips'], gtfs_data['stop_times'], on='trip_id')

    # Filter by service_id if provided
    if service_id is not None:
        trips_stop_times = trips_stop_times[trips_stop_times['service_id'] == service_id]

    # Get first stop of each trip only
    first_stops = trips_stop_times.loc[
        trips_stop_times.groupby('trip_id')['stop_sequence'].idxmin()
    ]

    # Convert time to timedelta
    first_stops['departure_time'] = pd.to_timedelta(first_stops['departure_time'])

    # Add time block
    first_stops['time_block'] = first_stops['departure_time'].apply(get_time_block)

    # Calculate total trips for percentage
    total_trips = first_stops['trip_id'].nunique()

    # Aggregate metrics by time period
    period_metrics = (
        first_stops
        .groupby('time_block')
        .agg(
            n_trips=('trip_id', 'nunique'),
            n_routes=('route_id', 'nunique')
        )
        .reset_index()
    )

    # Calculate percentage of daily service
    period_metrics['pct_of_service'] = (period_metrics['n_trips'] / total_trips * 100).round(2)

    # Sort for readability
    period_order = ['Pre-Early AM/Other', 'Early AM', 'AM Peak', 'Base', 'PM Peak', 'Evening', 'Late Evening']
    period_metrics['time_block'] = pd.Categorical(
        period_metrics['time_block'],
        categories=period_order,
        ordered=True
    )
    period_metrics = period_metrics.sort_values('time_block')

    return period_metrics

def get_route_details(gtfs_data, route_id, service_id=None):
    """
    Get comprehensive details about a single route.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        route_id: The route ID to analyze
        service_id (str, optional): Filter to specific service_id

    Returns:
        dict: Route metrics and details
    """

    def time_to_seconds(time_str):
        """Convert HH:MM:SS string to total seconds"""
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def time_to_minutes(time_str):
        """Convert HH:MM:SS string to total minutes"""
        try:
            if pd.isna(time_str) or time_str == '' or time_str is None:
                return None
            h, m, s = map(int, time_str.split(':'))
            return h * 60 + m + s / 60
        except (ValueError, AttributeError):
            return None

    # Get route basic info
    routes = gtfs_data['routes']
    route_info = routes[routes['route_id'] == route_id]

    if route_info.empty:
        raise ValueError(f"Route {route_id} does not exist")

    row = route_info.iloc[0]

    # Get trips for this route
    trips = gtfs_data['trips']
    filtered_trips = trips[trips['route_id'] == route_id]

    # Filter by service_id if provided
    if service_id is not None:
        filtered_trips = filtered_trips[filtered_trips['service_id'] == service_id]

    # Merge trips with stop_times
    trips_stop_times = pd.merge(filtered_trips, gtfs_data['stop_times'], on='trip_id')
    trips_stops = pd.merge(trips_stop_times, gtfs_data['stops'], on='stop_id')

    # Get unique stops servd by this route in ordered sequence
    stops_list = (
        trips_stops
        .groupby('stop_id')
        .agg({
            'stop_name': 'first',
            'stop_lat': 'first',
            'stop_lon': 'first',
            'stop_sequence': 'min'
        })
        .reset_index()
        .sort_values('stop_sequence')
    )

    # Get first stop of each trip
    first_stops = trips_stops.loc[
        trips_stops.groupby('trip_id')['stop_sequence'].idxmin()
    ]

    # Convert times
    first_stops['departure_mins'] = first_stops['departure_time'].apply(time_to_minutes)
    first_stops = first_stops.sort_values('departure_mins')

    # Calculate headways
    first_stops['headway_min'] = first_stops['departure_mins'].diff()

    # Calculate headways by direction
    direction_headways = []

    for direction in first_stops['direction_id'].unique():
        direction_stops = first_stops[first_stops['direction_id'] == direction]
        direction_stops = direction_stops.sort_values('departure_mins')
        direction_stops['headway_min'] = direction_stops['departure_mins'].diff()

        valid_headways = direction_stops['headway_min'].dropna()
        valid_headways = valid_headways[valid_headways >= 0]

        if len(valid_headways) > 0:
            direction_headways.extend(valid_headways.tolist())


    if direction_headways:
        avg_headway = round(sum(direction_headways) / len(direction_headways), 2)
    else:
        avg_headway = None

    # Get service span
    first_trip = first_stops['departure_time'].min()
    last_trip = first_stops['departure_time'].max()

    # Calculate service span in hours
    first_mins = time_to_minutes(first_trip)
    last_mins = time_to_minutes(last_trip)

    if first_mins is not None and last_mins is not None:
        service_span_hours = (last_mins - first_mins) / 60
    else:
        service_span_hours = None


    # Get shape data if available
    shape_coords = None
    if 'shapes' in gtfs_data and not gtfs_data['shapes'].empty:
        # Get shape_ids used by trips on this route
        shape_ids = filtered_trips['shape_id'].unique()

        if len(shape_ids) > 0:
            main_shape_id = filtered_trips['shape_id'].mode()[0] if len(filtered_trips) > 0 else shape_ids[0]

            shape_data = gtfs_data['shapes'][gtfs_data['shapes']['shape_id'] == main_shape_id]
            shape_data = shape_data.sort_values('shape_pt_sequence')

            # Format as list of lat lon pairs for Folium
            shape_coords = shape_data[['shape_pt_lat', 'shape_pt_lon']].values.tolist()

    # Package results
    metrics = {
            "route_id": route_id,
            "short_name": row.get("route_short_name"),
            "long_name": row.get("route_long_name"),
            "route_type": row.get("route_type"),
            "num_stops": trips_stops['stop_id'].nunique(),
            "num_trips": filtered_trips['trip_id'].nunique(),
            "avg_headway_min": round(avg_headway, 2) if pd.notna(avg_headway) else None,
            "first_trip": first_trip,
            "last_trip": last_trip,
            "service_span_hours": round(service_span_hours, 2) if service_span_hours is not None else None,  # Fixed
            "stops": stops_list,  # DataFrame with all stops
            "departure_times": first_stops['departure_time'].tolist(),  # List of all departure times
            "shape_coords": shape_coords,
    }

    return metrics




if __name__ == "__main__":
    from data_loader import load_gtfs_from_url
    from gtfs_parser import load_gtfs_tables, get_active_service

    url = 'https://www.viainfo.net/BusService/google_transit.zip'
    gtfs_dir = load_gtfs_from_url(url)
    gtfs_data = load_gtfs_tables(gtfs_dir)

    # Get frequencies for all service
    frequencies = calculate_route_frequencies(gtfs_data)
    print("\nTop 10 most frequent routes:")
    print(frequencies.head(10))

    # Or filter to a specific service
    active_service = get_active_service(gtfs_data, '2025-12-22')
    if active_service:
        freq_sunday = calculate_route_frequencies(gtfs_data, active_service[0])
        print(f"\nSunday frequencies (service {active_service[0]}):")
        print(freq_sunday.head(10))

    service_hours = calculate_service_hours(gtfs_data, service_id=active_service[0])
    for key, value in service_hours.items():
        print(f" {key}: {value:.2f}")

    stop_metrics = calculate_stop_metrics(gtfs_data, service_id=active_service[0])

    print("\nTop 10 Busiest Stops:")
    print(stop_metrics[['stop_name', 'n_trips', 'n_routes']].head(10))

    print("\nTransfer Hubs (5+ routes):")
    hubs = stop_metrics[stop_metrics['n_routes'] >= 5]
    print(hubs[['stop_name', 'n_routes', 'n_trips']].head(10))

    trips_by_hour = calculate_trips_by_hour(gtfs_data, service_id=active_service[0])

    print("\nTrips by Hour of Day:")
    print(trips_by_hour)

    # Identify peak hours
    peak = trips_by_hour[trips_by_hour['trip_count'] > trips_by_hour['trip_count'].mean()]
    print(f"\nPeak hours (above average): {peak['hour'].tolist()}")

    peak_metrics = calculate_peak_offpeak_metrics(gtfs_data, service_id=active_service[0])

    print("\nPeak vs Off-Peak Metrics:")
    print(peak_metrics)

    # Highlight the differences
    print(f"\nAM Peak has {peak_metrics[peak_metrics['time_block'] == 'AM Peak']['n_trips'].values[0]} trips")
    print(f"Base period has {peak_metrics[peak_metrics['time_block'] == 'Base']['n_trips'].values[0]} trips")
    print(peak_metrics)

    weekday_services = get_active_service(gtfs_data, '2025-12-22')  # Monday
    route_details = get_route_details(gtfs_data, route_id='88', service_id=weekday_services[0])
    print(f"Route: {route_details['short_name']} - {route_details['long_name']}")
    print(f"Stops: {route_details['num_stops']}")
    print(f"Trips: {route_details['num_trips']}")
    print(f"Average Headway: {route_details['avg_headway_min']} minutes")
    print(f"Service: {route_details['first_trip']} to {route_details['last_trip']}")
    print(f"\nStops served:")
    print(route_details['stops'][['stop_name', 'stop_lat', 'stop_lon']])

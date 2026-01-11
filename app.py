import streamlit as st
from utils.data_loader import load_gtfs_from_url
from utils.gtfs_parser import load_gtfs_tables, get_active_service
from utils.metrics_calculator import *
from utils.visualizations import *
import pandas as pd

st.set_page_config(page_title="GTFS Analyzer", layout="wide")


# Add caching functions
@st.cache_data(show_spinner=False)
def load_and_parse_gtfs(url):
    """Load and parse GTFS data with caching"""
    gtfs_dir = load_gtfs_from_url(url)
    gtfs_data = load_gtfs_tables(gtfs_dir)
    return gtfs_data


st.title("GTFS Transit Data Analyzer")
st.markdown("Analyze any GTFS feed by entering the URL")

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")

    # URL input
    gtfs_url = st.text_input(
        "GTFS Feed URL",
        value="https://www.viainfo.net/BusService/google_transit.zip",
        help="Enter the direct URL to a GTFS .zip file"
    )

    analyze_button = st.button("Analyze Feed", type="primary")

# Store data in session state
if 'gtfs_data' not in st.session_state:
    st.session_state.gtfs_data = None
    st.session_state.gtfs_url = None

# Main content
if analyze_button and gtfs_url:
    try:
        with st.spinner("Loading GTFS data..."):
            st.session_state.gtfs_data = load_and_parse_gtfs(gtfs_url)
            st.session_state.gtfs_url = gtfs_url
        st.success("GTFS data loaded successfully!")
        st.rerun()  # Force reload to prevent crash
    except Exception as e:
        st.error(f"Error loading GTFS data: {str(e)}")
        st.exception(e)

if st.session_state.gtfs_data is not None:
    gtfs_data = st.session_state.gtfs_data

    try:
        # Date selector for service
        analysis_date = st.sidebar.date_input("Analysis Date", value=pd.Timestamp.today())
        active_services = get_active_service(gtfs_data, analysis_date.strftime('%Y-%m-%d'))

        if not active_services:
            st.warning("No active service found for this date. Using all service.")
            service_id = None
        else:
            service_id = active_services[0]
            st.sidebar.info(f"Active service: {service_id}")

        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "System Map", "Route Details", "Analytics"])

        with tab1:
            st.header("System Overview")

            # System metrics
            metrics = calculate_system_metrics(gtfs_data)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Routes", f"{metrics['total_routes']:,}")
            with col2:
                st.metric("Total Stops", f"{metrics['total_stops']:,}")
            with col3:
                st.metric("Total Trips", f"{metrics['total_trips']:,}")
            with col4:
                if 'total_shapes' in metrics:
                    st.metric("Route Patterns", f"{metrics['total_shapes']:,}")

            # Service hours
            service_hours = calculate_service_hours(gtfs_data, service_id)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Daily Revenue Hours", f"{service_hours['total_revenue_hours']:,.0f}")
            with col2:
                st.metric("Avg Trip Duration", f"{service_hours['avg_trip_duration_min']:.1f} min")

            st.divider()

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Service by Time of Day")
                trips_by_hour = calculate_trips_by_hour(gtfs_data, service_id)
                fig = create_trips_by_hour_chart(trips_by_hour)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Peak vs Off-Peak")
                peak_metrics = calculate_peak_offpeak_metrics(gtfs_data, service_id)
                fig = create_peak_offpeak_chart(peak_metrics)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.header("System Maps")

            map_type = st.radio("Map Type", ["Routes Overview", "Stop Heatmap"], horizontal=True)

            if map_type == "Routes Overview":
                col1, col2 = st.columns([3, 1])
                with col1:
                    num_routes = st.slider("Number of routes to display", 5, 100, 15)
                with col2:
                    show_all = st.checkbox("Show all routes")

                if show_all:
                    total_routes = len(gtfs_data['routes'])
                    st.info(f"Displaying all {total_routes} routes (may take a moment to load)")
                    num_routes = total_routes

                with st.spinner("Generating map..."):
                    system_map = create_system_overview_map(gtfs_data, sample_routes=num_routes)
                    st.components.v1.html(system_map._repr_html_(), height=600)
            else:
                with st.spinner("Generating heatmap..."):
                    heatmap = create_stop_heatmap(gtfs_data)
                    st.components.v1.html(heatmap._repr_html_(), height=600)

        with tab3:
            st.header("Route Details")

            # Route selector
            routes_list = gtfs_data['routes'][['route_id', 'route_short_name', 'route_long_name']].copy()

            # Remove duplicate route_ids, keeping first occurrence
            routes_list = routes_list.drop_duplicates(subset='route_id', keep='first')

            routes_list['display'] = routes_list['route_short_name'].astype(str) + ' - ' + routes_list[
                'route_long_name']

            # Remove duplicate display names too (in case different route_ids have same name)
            routes_list = routes_list.drop_duplicates(subset='display', keep='last')

            # Sort by route number (convert to numeric if possible, otherwise alphabetic)
            try:
                routes_list['sort_key'] = pd.to_numeric(routes_list['route_short_name'], errors='coerce')
                routes_list = routes_list.sort_values('sort_key')
            except:
                routes_list = routes_list.sort_values('route_short_name')

            selected_route_display = st.selectbox(
                "Select a route",
                options=routes_list['display'].tolist(),
                key='route_selector'
            )

            if selected_route_display:
                selected_route_id = routes_list[routes_list['display'] == selected_route_display]['route_id'].iloc[0]

                with st.spinner("Loading route details..."):
                    # Get route details
                    route_details = get_route_details(gtfs_data, selected_route_id, service_id)

                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Stops", route_details['num_stops'])
                    with col2:
                        st.metric("Daily Trips", route_details['num_trips'])
                    with col3:
                        st.metric("Avg Headway", f"{route_details['avg_headway_min']:.1f} min" if route_details[
                            'avg_headway_min'] else "N/A")
                    with col4:
                        st.metric("Service Span", f"{route_details['service_span_hours']:.1f} hrs" if route_details[
                            'service_span_hours'] else "N/A")

                    st.info(
                        f"**{route_details['long_name']}** • Service: {route_details['first_trip']} - {route_details['last_trip']}")

                    # Route map
                    st.subheader("Route Map")
                    route_map = create_route_map(gtfs_data, route_details=route_details)
                    st.components.v1.html(route_map._repr_html_(), height=500)

                    # Stops table
                    st.subheader("Stops")
                    st.dataframe(
                        route_details['stops'][['stop_name', 'stop_lat', 'stop_lon']],
                        use_container_width=True,
                        hide_index=True
                    )

        with tab4:
            st.header("System Analytics")

            # Calculate metrics once
            frequencies = calculate_route_frequencies(gtfs_data, service_id)
            stop_metrics = calculate_stop_metrics(gtfs_data, service_id)

            # Stack charts vertically
            st.subheader("Route Frequency Distribution")
            fig = create_headway_distribution(frequencies)
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            st.subheader("Route Frequency Comparison")
            fig = create_route_frequency_ranking(frequencies, top_n=10)
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            st.subheader("Busiest Stops")
            # Remove duplicates by keeping first occurrence
            stop_metrics_unique = stop_metrics.drop_duplicates(subset=['stop_name'], keep='first')
            fig = create_busiest_stops_chart(stop_metrics_unique, top_n=15)
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            st.subheader("Top Routes by Frequency")
            st.dataframe(
                frequencies.head(10)[['route_short_name', 'route_long_name', 'avg_headway_min']],
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)

else:
    st.info("Enter a GTFS feed URL in the sidebar and click 'Analyze Feed' to get started")

    st.markdown("""
    ### Example GTFS Feeds
    - **VIA San Antonio**: https://www.viainfo.net/BusService/google_transit.zip
    - Find more at [Mobility Database](https://database.mobilitydata.org/)
    """)
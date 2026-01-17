import streamlit as st
from utils.data_loader import load_gtfs_from_url
from utils.gtfs_parser import load_gtfs_tables, get_active_service
from utils.metrics_calculator import *
from utils.visualizations import *
import pandas as pd
from utils.ai_chat import GTFSChatbot
import os

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

        # Pre-calculate metrics for use across tabs
        route_frequencies = calculate_route_frequencies(gtfs_data, service_id)
        trips_by_hour = calculate_trips_by_hour(gtfs_data, service_id)

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

            # NOW add the chat section AFTER all the charts
            st.markdown("---")
            st.header("Ask Questions About the Data")

            # Initialize chatbot in session state (so it persists)
            if 'chatbot' not in st.session_state and gtfs_data is not None:
                st.session_state.chatbot = GTFSChatbot(
                    api_key=os.environ.get("ANTHROPIC_API_KEY", "YOUR_KEY_HERE"),
                    gtfs_data=gtfs_data,
                    route_frequencies=route_frequencies
                )

            # Initialize chat history
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []

            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input
            if prompt := st.chat_input("Ask a question about the transit data..."):
                # Add user message to history
                st.session_state.chat_history.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        response = st.session_state.chatbot.ask(prompt)

                        if response['success']:
                            st.markdown(response['answer'])
                            # Code is hidden by default, user can expand if curious
                            if response['code']:
                                with st.expander("🔍 See how this was calculated"):
                                    st.code(response['code'], language='python')
                        else:
                            st.error(response['answer'])

                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response['answer']
                })

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
                    st.components.v1.html(system_map._repr_html_(), height=900)
            else:
                with st.spinner("Generating heatmap..."):
                    heatmap = create_stop_heatmap(gtfs_data)
                    st.components.v1.html(heatmap._repr_html_(), height=900)

        with tab3:
            st.header("Route Details")

            # Route selector
            routes_list = gtfs_data['routes'][['route_id', 'route_short_name', 'route_long_name']].copy()

            # Filter to routes active on selected date/service
            if service_id is not None:
                # Get all route_ids active for this service
                active_route_ids = gtfs_data['trips'][
                    gtfs_data['trips']['service_id'] == service_id
                    ]['route_id'].unique()
                routes_list = routes_list[routes_list['route_id'].isin(active_route_ids)]

            routes_list['display'] = routes_list['route_short_name'].astype(str) + ' - ' + routes_list[
                'route_long_name']

            # For dates on/after 1-12-25, prioritize service_id starting with 336
            from datetime import datetime

            cutoff_date = datetime(2025, 1, 12).date()

            if analysis_date >= cutoff_date:
                # Add service_id info to help dedupe
                routes_with_service = pd.merge(
                    routes_list,
                    gtfs_data['trips'][['route_id', 'service_id']].drop_duplicates(),
                    on='route_id'
                )

                # Prefer routes with service_id starting with 336
                routes_with_service['is_new_service'] = routes_with_service['service_id'].astype(str).str.startswith(
                    '336')
                routes_with_service = routes_with_service.sort_values('is_new_service', ascending=False)
                routes_list = routes_with_service.drop_duplicates(subset='display', keep='first')
            else:
                # Before cutoff, just remove duplicates normally
                routes_list = routes_list.drop_duplicates(subset='display', keep='first')

            # Sort by route number
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
                    st.components.v1.html(route_map._repr_html_(), height=800)


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

            # Top routes
            st.subheader("Top Routes by Frequency")

            # Rename columns for display
            freq_display = frequencies.head(10)[['route_short_name', 'route_long_name', 'avg_headway_min']].copy()
            freq_display.columns = ['Route', 'Route Name', 'Avg Headway (min)']

            st.dataframe(
                freq_display,
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
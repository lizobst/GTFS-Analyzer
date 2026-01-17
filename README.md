# GTFS Transit Data Analyzer

A data-driven web application that transforms raw GTFS (General Transit Feed Specification) feeds into actionable transit insights. Built to support transit planning, operations analysis, and academic research on service reliability and bus bunching patterns.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gtfs-analyzer.streamlit.app/)
<img width="1824" height="853" alt="image" src="https://github.com/user-attachments/assets/276a1a41-8d79-47d2-b004-c801bc5dae01" />

## Purpose & Applications

This tool was developed as part of research on bus bunching and service reliability in public transit systems. It enables:

### For Transit Agencies
- **Service Planning**: Identify routes with irregular headways that may experience bunching
- **Resource Allocation**: Pinpoint high-traffic stops and routes requiring additional service
- **Performance Monitoring**: Track service span, frequency, and coverage metrics across the network

### For Researchers & Analysts
- **Baseline Analysis**: Establish scheduled service patterns before analyzing real-time performance
- **Comparative Studies**: Quickly analyze and compare GTFS feeds from multiple transit agencies
- **Bus Bunching Research**: Identify routes with tight scheduled headways (< 10 min) where bunching is most problematic
- **Service Equity**: Analyze service distribution across time periods and geographic areas

### For Data Scientists
- **Reproducible Analysis**: Modular Python architecture for extending with custom metrics
- **Data Validation**: Automated GTFS feed validation and quality checks
- **Visualization Pipeline**: Reusable functions for transit data visualization

## Key Insights Enabled

- **Frequency Analysis**: Identify which routes have the tightest headways (most prone to bunching when delays occur)
- **Service Patterns**: Understand how service levels vary throughout the day and across different route types
- **Network Coverage**: Visualize geographic distribution of stops and identify service gaps
- **Transfer Hubs**: Locate key stops where multiple routes intersect
- **Temporal Patterns**: Compare peak vs off-peak service allocation

## Features

### System Overview
- Key metrics: total routes, stops, trips, and service patterns
- Daily revenue hours and average trip duration
- Service distribution by time of day
- Peak vs off-peak service analysis with visual breakdowns

### Interactive Maps
- System-wide route visualization (customizable route display)
- Individual route mapping with all stop locations
- Stop density heatmap showing service concentration
- Interactive popups with route and stop details

### Route Details
- Comprehensive metrics for each route including:
  - Average headway (critical for identifying bunching risk)
  - Service span and operating hours
  - Number of stops and trip count
- Complete stop listings with coordinates
- Route-specific map visualization with shape data

### Analytics Dashboard
- **Headway Distribution**: Histogram showing frequency patterns across all routes
- **Route Frequency Comparison**: Side-by-side view of most and least frequent routes
- **Busiest Stops**: Ranked list of highest-traffic locations
- **Temporal Analysis**: Service patterns throughout the day with peak period highlighting

## Technical Implementation

**Data Pipeline:**
1. **Download & Validation**: Automated GTFS feed retrieval with required file validation
2. **ETL Processing**: Parse CSV files into structured Pandas DataFrames
3. **Metric Calculation**: Custom algorithms for headway, service hours, and coverage metrics
4. **Visualization**: Interactive Folium maps and Plotly charts

**Key Technical Features:**
- Caching with `@st.cache_data` for performance optimization
- Error handling for incomplete or malformed GTFS feeds
- Session state management for smooth user experience
- Responsive design that adapts to different screen sizes
- Support for GTFS feeds with optional files (shapes, frequencies, etc.)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/gtfs-analyzer.git
cd gtfs-analyzer
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Analyzing a Transit System

1. Enter a GTFS feed URL in the sidebar (direct link to .zip file)
2. Click "Analyze Feed"
3. Select a date to analyze service for that specific day
4. Explore different tabs:
   - **Overview**: System-wide statistics and service patterns
   - **System Map**: Geographic visualization of routes and stops
   - **Route Details**: In-depth analysis of individual routes
   - **Analytics**: Frequency patterns, stop activity, and comparative metrics

### Example GTFS Feeds

- **VIA San Antonio**: https://www.viainfo.net/BusService/google_transit.zip
- **Find More**: [Mobility Database](https://database.mobilitydata.org/) contains 2,000+ feeds worldwide

## Project Structure
```
gtfs-analyzer/
├── app.py                      # Main Streamlit application
├── utils/
│   ├── data_loader.py         # GTFS download, extraction, and validation
│   ├── gtfs_parser.py         # Parse GTFS files into DataFrames
│   ├── metrics_calculator.py  # Transit metrics and statistical analysis
│   └── visualizations.py      # Interactive maps and charts
├── requirements.txt            # Python dependencies
└── README.md
```

## Metrics Explained

- **Headway**: Time between consecutive buses on the same route. Lower headways (< 10 min) indicate frequent service but higher risk of bunching when delays occur.
- **Revenue Hours**: Total hours buses spend in active service, a key metric for operational costs and resource allocation.
- **Service Span**: Hours between first and last trip of the day, indicating the breadth of service availability.
- **Peak vs Off-Peak**: Service levels during rush hours (6-9 AM, 3-6 PM) compared to midday and evening periods.
- **Stop Activity**: Number of trips and routes serving each stop, identifying transfer hubs and high-demand locations.

## Research Context

This tool was developed as part of thesis research on bus bunching - the phenomenon where buses on the same route cluster together instead of maintaining even spacing. By analyzing scheduled headways and service patterns, this tool helps identify:

- Routes most susceptible to bunching (high-frequency routes with < 10 min headways)
- Time periods when bunching is most likely (peak hours with tight scheduling)
- Network characteristics that contribute to service reliability issues

The insights from this static GTFS analysis serve as a baseline for comparing against real-time vehicle position data to measure actual bunching occurrence.

## Technologies Used

- **Python**: Core programming language
- **Streamlit**: Interactive web application framework
- **Pandas**: Data manipulation and analysis
- **Folium**: Interactive mapping with Leaflet.js
- **Plotly**: Interactive charts and visualizations
- **GTFS Specification**: Industry-standard transit data format

## Skills Demonstrated

- **Data Engineering**: ETL pipeline development, data validation, error handling
- **Statistical Analysis**: Headway calculations, temporal pattern analysis, aggregation
- **Data Visualization**: Interactive dashboards, geographic mapping, statistical charts
- **Software Development**: Modular architecture, caching strategies, user experience design
- **Domain Knowledge**: Transit operations, GTFS specification, service planning concepts

## Future Enhancements

- [ ] Real-time GTFS-RT integration for live vehicle tracking
- [ ] Bus bunching detection algorithms using real-time data
- [ ] Historical trend analysis across multiple dates
- [ ] Export functionality for metrics and visualizations
- [ ] Advanced filtering (by route type, time windows, service_id)


## Author

**Liz** - Data Analytics Student, UT San Antonio  

*Built as part of a larger project on bus bunching and service reliability in public transit systems.* 


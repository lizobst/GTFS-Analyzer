# GTFS Transit Data Analyzer

A web-based analytics platform that transforms complex GTFS (General Transit Feed Specification) transit data into actionable insights through automated metrics, interactive visualizations, and conversational AI. Designed for transit planners, researchers, and community advocates, this tool eliminates technical barriers to understanding transit system performance, turning days of analysis into minutes of insight.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gtfs-analyzer.streamlit.app/)
<img width="1824" height="853" alt="image" src="https://github.com/user-attachments/assets/276a1a41-8d79-47d2-b004-c801bc5dae01" />

## Problem Statement

Transit agencies publish schedule data in GTFS (General Transit Feed Specification) format—a standardized, open-source dataset used by agencies worldwide. However, extracting meaningful insights from these files requires technical expertise in data analysis and specialized knowledge of the GTFS structure. This creates barriers for:

- Transit planners needing quick operational insights
- City officials making data-driven policy decisions
- Researchers and students analyzing transit systems
- Community advocates seeking to understand local service

**The gap:** No accessible tool exists for non-technical stakeholders to quickly analyze transit performance without writing code or purchasing expensive software.

## Solution

A web-based analytics platform that automates GTFS analysis and makes transit data accessible through:

- **One-click data loading** - Simply paste a GTFS feed URL
- **Automated metrics calculation** - System-level and route-level performance indicators
- **Interactive visualizations** - Maps, charts, and frequency analysis
- **AI-powered chat interface** - Ask questions in plain English, get instant answers

**Business Value:**
- Reduces analysis time from hours to minutes
- Democratizes data access for non-technical stakeholders
- Enables rapid decision-making with real-time insights
- Scales across any transit system using standardized GTFS format

## Key Features

### Automated Analytics
- **System Overview:** Total routes, stops, trips, and service hours
- **Route Performance:** Frequency analysis and headway calculations
- **Service Patterns:** Peak vs. off-peak service distribution
- **Time-based Analysis:** Trip patterns throughout the day

### Interactive Visualizations

<p align="left">
  <img src="https://github.com/user-attachments/assets/003c25b6-c5ce-4aae-996d-d9e34145fc3c" width="80%" />
</p>


- Geographic route mapping with stop locations
- Service frequency heatmaps
- Temporal service distribution charts
- Route-level performance comparisons

### Conversational AI Interface
<p align="left">
  <img src="https://github.com/user-attachments/assets/effb80cf-8402-4435-b4d7-45b2abdbe685" width="90%" />
</p>

Built with Anthropic's Claude API to enable natural language queries:

**Example Questions:**
- "What route has the best frequency?"
- "What's the busiest stop?"
- "Which routes operate during peak hours?"
- "What's the average wait time system-wide?"

**Impact:** Non-technical users can extract insights without SQL knowledge or data science skills.

## Technical Architecture

See [Technical Documentation.pdf](Technical%20Documentation.pdf) for detailed implementation details.

## Real-World Application: VIA San Antonio Analysis

Applied this tool to VIA Metropolitan Transit as part of bus bunching research. Analysis completed in **25 seconds** versus the typical **2-3 days** of manual work.

### What the Data Revealed
<p align="left">
  <img src="https://github.com/user-attachments/assets/60adc974-d416-42e5-8bcd-e19d6f5c7aae" width="90%" />
</p>

**High-Frequency Routes:**
- Identified 15 routes operating on <10 minute headways
- Routes 10, 20, and 103 average 3-minute headways during peak periods
- These tight schedules create high susceptibility to bus bunching when delays occur
- **Insight:** These routes should be priority targets for real-time monitoring and operational interventions

**Network Topology:**
- Downtown Transit Center handles 427 trips/day across 12 routes
- Secondary hubs at University Station (384 trips, 11 routes) and Medical Center (356 trips, 8 routes)
- **Insight:** Delays at these locations propagate across multiple routes—infrastructure improvements here have system-wide impact

**Service Distribution:**
- VIA maintains consistent 290-310 trips/hour from 6 AM to 6 PM
- Unlike many systems with dramatic peak/off-peak differences
- **Insight:** Flat service distribution suggests different operational characteristics and potential reliability patterns compared to commuter-focused systems

**Geographic Patterns:**
<p align="left">
  <img src="https://github.com/user-attachments/assets/785b034f-6d53-409a-a2aa-7ee7dcdcf41f" width="80%" />
</p>

- Service highly concentrated in urban core
- Clear coverage gaps in suburban areas
- Stop density correlates with population density
- **Insight:** Identifies underserved areas and potential expansion opportunities

### The Bigger Picture

This static schedule analysis answers critical "where to look" questions:

- **Where will problems occur?** High-frequency routes with tight headways
- **Where do problems spread?** Major transfer hubs
- **When does service matter most?** Peak periods with highest trip counts
- **Who is affected?** Geographic analysis shows service equity patterns

By establishing baseline patterns from static schedules, subsequent analysis of real-time data can:

1. Focus on high-risk routes identified through frequency analysis
2. Monitor critical transfer points where delays propagate
3. Compare actual operations against scheduled patterns
4. Quantify reliability issues with statistical rigor

This tool transforms schedule data from a compliance document into a strategic planning resource.

## Getting Started

Visit the [live application](https://gtfs-analyzer.streamlit.app/) to start analyzing transit data immediately.

[GTFS Analyzer 0.webm](https://github.com/user-attachments/assets/d0a4951b-834b-4cff-b589-8360c582e432)


<br>

## Author

**Liz Obst** - Data Analytics Student, UT San Antonio  

*Built as part of a larger project on bus bunching and service reliability in public transit systems.* 


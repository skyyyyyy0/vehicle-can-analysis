# Vehicle CAN Telemetry Analytics Pipeline

![Dashboard Overview](./outputs/screenshots/dashboard_overview/01_full_dashboard.png)

## Overview

This project analyzes raw vehicle CAN telemetry data extracted from MF4 files.

The pipeline processes CAN signals using Python, AWS S3, Athena SQL, and Tableau to identify driving-state behavior, signal transitions, anomaly patterns, and session-level telemetry characteristics.

This project simulates a real-world telemetry analytics workflow:

```text
MF4 Files
→ Python Signal Processing
→ CSV Export
→ AWS S3 Storage
→ Athena SQL Analysis
→ Tableau Dashboard Visualization
```

## Problem Statement

Raw CAN telemetry data is difficult to interpret because signal definitions are often unavailable or undocumented.

The goal of this project was to investigate whether meaningful operational telemetry behavior could be inferred directly from raw MF4 CAN data using byte-level signal analysis, transition-based segmentation, anomaly detection, cloud SQL analytics, and dashboard visualization.

---

## Objectives

- Parse and analyze raw MF4 CAN telemetry files
- Extract CAN signal data into structured CSV format
- Investigate byte-level CAN signal behavior
- Compare driving vs idle telemetry patterns
- Detect extreme Byte 4 transition events
- Validate signal behavior across multiple MF4 sessions
- Build a cloud-based analytics pipeline using AWS Athena and Tableau

---

## Tech Stack

### Data Processing

- Python
- pandas
- numpy
- asammdf

### Cloud & SQL

- AWS S3
- AWS Athena
- SQL

### Visualization

- Tableau

---

## Pipeline Architecture

```text
Raw MF4 Telemetry Files
        ↓
Python MF4 Parsing
        ↓
CAN Signal Extraction
        ↓
CSV Processing
        ↓
AWS S3 Upload
        ↓
Athena SQL Query Layer
        ↓
Tableau Dashboard
        ↓
Signal Insight & KPI Reporting
```

---

## Key Analysis Areas

### 1. CAN Signal Exploration

- Extracted CAN data from MF4 files
- Parsed timestamp, CAN ID, and byte-level values
- Selected CAN ID 111 as the main candidate signal
- Analyzed Byte 4 and Byte 5 behavior patterns

### 2. Driving vs Idle Segmentation

![Driving vs Idle Comparison](./outputs/screenshots/session_behavior/05_driving_state_distribution.png)

- Created a heuristic segmentation method using Byte 4 transition magnitude
- Compared signal behavior between driving and idle states
- Found that driving states produced much larger transition magnitudes than idle states

### 3. Multi-file Validation

![Session Comparison & Extreme Transition Events](./outputs/screenshots/kpi_analysis/03_behavior_and_extreme_events.png)

- Processed multiple MF4 files
- Extracted CAN ID 111 across all validation datasets
- Compared Byte 4 transition behavior across sessions
- Classified sessions into stable, mixed, and dynamic behavior groups

### 4. Anomaly Detection

<img src="./outputs/screenshots/anomaly_detection/07_anomaly_detection_panel.png" width="700"/>

- Used Byte 4 transition magnitude to identify extreme transition events
- Defined high-magnitude transitions as anomaly candidates
- Visualized anomaly concentration regions in Tableau

---

## Tableau Dashboard Features

The final Tableau dashboard includes:

- KPI Summary Panel
- Driving vs Idle Transition Comparison
- Driving State Distribution
- Session Behavior Comparison
- Extreme Transition Event Visualization
- Anomaly Detection Panel
- Interactive filters for session and driving state analysis

---

## KPI Metrics

![KPI Summary](./outputs/screenshots/kpi_analysis/02_kpi_and_transition_analysis.png)

The dashboard includes the following KPIs:

- Total CAN Records
- Dynamic Transition Count
- Driving Ratio
- Anomaly Event Count

---

## Key Findings

- Idle records accounted for a large portion of the dataset, but signal changes were minimal during idle states.
- Driving records showed significantly higher Byte 4 transition magnitudes.
- Extreme Byte 4 transitions were concentrated in specific telemetry regions.
- Multi-file validation showed that dynamic transition behavior appeared repeatedly across multiple MF4 sessions.
- The signal behavior could be separated into stable, mixed, and dynamic session patterns.

---

## Project Structure

```text
project/
│
├── data/
│
├── notebooks/
│
├── src/
│   ├── multi_file_validation.py
│   ├── prepare_tableau_data.py
│   └── validation_visualization.py
│
├── notes/
│   ├── signal_analysis.md
│   ├── multi_file_validation_findings.md
│   └── telemetry_analysis_summary.md
│
├── outputs/
│   ├── athena_queries/
│   ├── athena_query_outputs/
│   ├── python_analysis/
│   │   ├── figures/
│   │   ├── statistics/
│   │   └── validation/
│   ├── raw_exports/
│   ├── screenshots/
│   │   ├── athena/
│   │   ├── dashboard_overview/
│   │   ├── kpi_analysis/
│   │   ├── session_behavior/
│   │   └── anomaly_detection/
│   └── tableau/
│       ├── workbook/
│       ├── exports/
│       └── assets/
│
└── README.md
```

---

## Athena SQL Queries

Reusable Athena SQL queries were created for:

- Signal frequency analysis
- Byte 4 trend analysis
- Driving vs idle comparison
- Anomaly detection
- Session-level summary analysis

Example query files:

```text
outputs/athena_queries/
├── 01_signal_frequency.sql
├── 02_byte4_trend.sql
├── 03_driving_idle.sql
├── 04_anomaly_detection.sql
└── 05_session_summary.sql
```

---

## Dashboard Screenshots

Dashboard screenshots are organized under:

```text
outputs/screenshots/
```

Recommended dashboard images include:

```text
01_full_dashboard_overview.png
02_kpi_summary_panel.png
03_driving_vs_idle_comparison.png
04_session_behavior_comparison.png
05_driving_state_distribution.png
06_extreme_transition_events.png
07_anomaly_detection_panel.png
```

---

## Future Improvements

- Add real-time CAN stream ingestion
- Automate anomaly alert generation
- Add machine learning-based signal classification
- Expand validation across more MF4 sessions
- Build a production-style monitoring dashboard
- Add predictive telemetry behavior modeling

---

## Status

- MF4 parsing pipeline complete
- Python preprocessing complete
- Multi-file validation complete
- AWS S3 storage complete
- Athena SQL analytics complete
- Tableau dashboard complete
- Portfolio-ready documentation in progress

# Pipeline Summary

This project focused on building an end-to-end telemetry analytics pipeline using raw MF4 CAN data.

Raw MF4 telemetry files were parsed using Python and converted into structured CSV datasets for downstream analytics. The processed telemetry data was uploaded to AWS S3 and queried using Athena SQL for signal trend analysis, driving-state segmentation, and anomaly detection.

The project primarily focused on Byte 4 CAN signal behavior, including:

- signal transition analysis
- driving vs idle comparison
- anomaly event detection
- multi-session telemetry validation

The analyzed datasets were visualized using Tableau dashboards containing KPI panels, transition monitoring charts, session behavior comparisons, and anomaly detection visualizations.

The final pipeline architecture:

MF4 → Python → CSV → AWS S3 → Athena → Tableau

This project simulates a real-world telemetry analytics workflow combining cloud-based analytics, signal validation, SQL querying, and dashboard reporting.

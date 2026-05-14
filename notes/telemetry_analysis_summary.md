# Telemetry Analysis Summary

## Project Overview

This project focused on building an end-to-end telemetry analysis workflow using raw MF4 vehicle CAN data.

The analysis pipeline included:

- MF4 parsing with Python
- Cloud-based storage using Amazon S3
- Athena SQL analysis
- Signal exploration and segmentation
- Byte-level interpretation
- Tableau dashboard preparation

The primary objective was to identify and interpret meaningful behavioral patterns directly from raw CAN telemetry data without DBC definitions.

---

# Candidate Signal Selection

## Selected Signal

- CAN ID: 111

## Selection Criteria

CAN ID 111 was selected based on the following characteristics:

- High transmission frequency
- Strong byte-level variability
- Repeated temporal transition patterns
- Clear dynamic versus stable behavior

The analysis primarily focused on:

- `byte_4`
- `byte_5`
- `byte_7`

---

# Signal Exploration Findings

## byte_4

`byte_4` showed the highest variability within CAN ID 111.

Observed characteristics:

- Frequent transitions between low and high values
- Dynamic operational behavior
- Repeated state-like switching patterns
- Clear distinction between stable and unstable sections

The signal behavior appeared more consistent with operational state transitions rather than smooth continuous sensor measurements.

---

## byte_5

`byte_5` also showed strong dynamic behavior.

However:

- Correlation with `byte_4` remained weak
- Transition timing differed from `byte_4`
- The signal appeared behaviorally independent

This suggests that `byte_5` may represent a separate operational field within the CAN frame.

---

## byte_7

`byte_7` remained relatively stable throughout the dataset.

Observed characteristics:

- Low standard deviation
- Minimal dynamic variation
- Weak correlation with surrounding bytes

This behavior suggests that `byte_7` may function as:

- A status flag
- A control field
- A checksum-related component
- A stable identifier field

---

# Driving vs Idle Segmentation

A heuristic segmentation approach was applied using `byte_4_diff`.

## Segmentation Logic

- Low variation → idle-like behavior
- High variation → driving-like behavior

This segmentation method successfully separated:

- Stable operational sections
- Dynamic transition sections
- Repeated switching behavior

The resulting patterns suggest that `byte_4` may reflect changes in vehicle operational activity.

---

# Correlation Analysis

Correlation analysis was performed across all byte fields within CAN ID 111.

## Key Findings

- Most byte relationships remained weak
- `byte_4` and `byte_5` showed low correlation despite both being highly dynamic
- Multiple bytes appeared to operate independently

These findings suggest that CAN ID 111 likely contains multiple signal components with different operational roles.

---

# Behavioral Interpretation

The observed signal behavior may be associated with:

- Driving-state transitions
- Operational load changes
- Engine or control-state activity
- Dynamic vehicle behavior

Although the exact CAN signal definitions remain unknown, meaningful behavioral patterns were successfully inferred directly from raw telemetry data.

---

# Project Outcome

This project successfully demonstrated:

- MF4 telemetry parsing and processing
- CAN signal exploration without DBC definitions
- Athena-based telemetry querying
- Heuristic driving-state segmentation
- Byte-level behavioral interpretation
- Dashboard-ready dataset preparation for Tableau

The next phase of the project will focus on:

- Multi-file validation
- Athena dashboard optimization
- Tableau visualization
- Insight reporting and portfolio presentation

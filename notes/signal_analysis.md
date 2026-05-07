# CAN Signal Analysis Notes

## Candidate Signal

- CAN ID: 111

---

## Byte-Level Findings

### byte_4

- High standard deviation
- Continuous fluctuation over time
- Frequent transitions between low and high values
- Likely dynamic operational signal

### byte_5

- Strong variability
- Dynamic behavior independent from byte_4
- Possible secondary operational signal

### byte_7

- Low variation
- Mostly stable throughout the dataset
- Possibly static flag or checksum-related field

---

## Visualization Insight

The `byte_4` signal showed repeated rapid fluctuations across timestamps, suggesting dynamic vehicle-state behavior rather than smooth continuous sensor measurements.

The signal frequently transitioned between stable plateau regions and highly dynamic sections.

---

## Initial Hypothesis

CAN ID 111 `byte_4` may be related to:

- Driving activity
- Engine load changes
- Operational state transitions
- Efficiency-related vehicle behavior

---

## Final Candidate Selection

### Selected CAN ID

- CAN ID: 111

### Selection Reason

- High transmission frequency
- Dynamic byte-level variability
- Strong fluctuation in `byte_4` and `byte_5`
- Repeated temporal signal behavior
- Clear transition patterns during segmentation analysis

### Conclusion

CAN ID 111 was selected as the primary candidate signal for further behavioral analysis and telemetry interpretation.

---

## Byte Variability Verification

### High Variability Bytes

- `byte_4` showed the highest standard deviation
- `byte_5` also showed strong variability

### Low Variability Bytes

- `byte_7` remained relatively stable

### Interpretation

The high variability of `byte_4` and `byte_5` suggests that these bytes may contain dynamic operational signals, while `byte_7` may represent a stable control or checksum-related field.

---

# Driving vs Idle Segmentation

## Segmentation Method

A heuristic threshold was applied using `byte_4_diff`.

### Logic

- Low variation → idle
- High variation → driving

This segmentation approach was used to estimate dynamic versus stable operational sections within the signal.

---

## Segmentation Findings

The segmentation analysis revealed:

- Frequent transition behavior during dynamic sections
- Stable plateau behavior during inferred idle periods
- Repeated switching between low and high signal states

These patterns suggest that `byte_4` may reflect dynamic operational activity rather than static sensor behavior.

---

# Correlation Analysis

Correlation analysis was performed across all byte fields within CAN ID 111.

## Key Findings

- Most byte correlations remained weak and close to zero
- `byte_4` and `byte_5` showed low correlation despite both being highly dynamic
- Multiple bytes appeared to behave independently

### Interpretation

These findings suggest that CAN ID 111 likely contains multiple independent signal fields with different operational roles.

---

# Pattern Interpretation

## Dynamic Bytes

### byte_4

- Highly dynamic
- Frequent state-like transitions
- Strong operational transition behavior

### byte_5

- Dynamic but behaviorally independent from `byte_4`
- Different transition timing patterns

## Stable Byte

### byte_7

- Relatively stable across timestamps
- Minimal variability
- Possible status flag or checksum-related field

---

# Real-world Interpretation

The observed signal behavior may be associated with:

- Driving-state transitions
- Operational load changes
- Engine or control-state activity
- Dynamic vehicle behavior

Although the exact CAN definitions are unknown, meaningful behavioral patterns were successfully inferred directly from raw telemetry data.

---

# Project Outcome

This analysis demonstrated:

- MF4 telemetry parsing and processing
- Byte-level CAN signal exploration
- Heuristic driving-state segmentation
- Behavioral signal interpretation without DBC definitions
- Preparation for scalable dashboard visualization workflows

The next phase of the project will focus on:

- Multi-file validation
- Athena-based dashboard queries
- Tableau visualization
- Portfolio presentation and insight reporting

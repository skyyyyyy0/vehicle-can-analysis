# CAN Signal Analysis Notes

## Candidate Signal

### Selected CAN ID

- CAN ID: 111

CAN ID 111 was selected as the primary candidate signal for behavioral telemetry analysis due to its high transmission frequency, strong temporal variability, and repeated dynamic transition behavior across multiple MF4 datasets.

---

# Analysis Objective

The goal of this analysis phase was to investigate raw CAN telemetry behavior directly from MF4 datasets without relying on OEM DBC decoding information.

The analysis focused on:

- byte-level signal variability
- transition-based behavior analysis
- heuristic driving-state segmentation
- anomaly detection
- operational telemetry interpretation

---

# Byte-Level Findings

## byte_4

### Observed Characteristics

- High standard deviation
- Continuous fluctuation over time
- Frequent transitions between low and high values
- Repeated abrupt transition behavior
- Elevated rolling variability

### Interpretation

The observed behavior suggests that `byte_4` represents a highly dynamic operational signal rather than a static telemetry field.

The signal repeatedly transitioned between:

- stable plateau regions
- high-activity dynamic regions

This pattern suggests possible association with:

- driving activity
- operational state changes
- engine-load-related behavior
- telemetry state transitions

---

## byte_5

### Observed Characteristics

- Strong variability
- Dynamic behavior independent from `byte_4`
- Repeated transition activity
- Different fluctuation timing compared to `byte_4`

### Interpretation

Although `byte_5` also demonstrated dynamic telemetry behavior, its transition timing patterns differed from `byte_4`.

This suggests that CAN ID 111 may contain multiple operationally independent signal fields rather than a single correlated telemetry channel.

---

## byte_7

### Observed Characteristics

- Low variation
- Mostly stable across timestamps
- Minimal transition activity

### Interpretation

The low variability of `byte_7` suggests that it may represent:

- a stable control field
- a status-related flag
- checksum-like behavior
- a relatively static telemetry field

---

# Byte Variability Verification

## High Variability Bytes

The analysis identified:

- `byte_4` as the highest variability field
- `byte_5` as another strongly dynamic field

These bytes demonstrated:

- elevated transition magnitude
- repeated fluctuation
- dynamic operational behavior

---

## Low Variability Bytes

`byte_7` remained relatively stable throughout the telemetry datasets and showed minimal variability.

---

## Variability Interpretation

The variability analysis suggests that CAN ID 111 contains a mixture of:

- dynamic operational telemetry fields
- relatively stable telemetry fields

This supports the hypothesis that multiple independent operational behaviors may coexist within the same CAN frame.

---

# Visualization Insights

Visualization analysis revealed that the `byte_4` signal repeatedly alternated between:

- stable telemetry plateaus
- abrupt high-transition regions

The signal behavior appeared significantly more dynamic than smooth continuous sensor measurements.

Repeated abrupt transitions were especially visible during telemetry regions associated with elevated rolling standard deviation and increased anomaly density.

The visual patterns strongly suggested state-transition-like telemetry behavior.

---

# Driving vs Idle Segmentation

## Segmentation Method

A heuristic threshold was applied using `byte_4_diff` transition magnitude.

### Segmentation Logic

- low variation → idle-like telemetry state
- high variation → driving-like telemetry state

This approach was used to estimate stable versus dynamic operational behavior directly from transition intensity.

---

## Segmentation Findings

The segmentation analysis revealed:

- frequent transition behavior during dynamic sections
- stable plateau behavior during inferred idle periods
- repeated switching between low and high activity states

Driving-like regions consistently showed:

- elevated transition magnitude
- increased rolling variability
- higher anomaly density
- increased signal fluctuation

Idle-like regions consistently showed:

- low transition activity
- stable telemetry behavior
- minimal fluctuation
- reduced anomaly frequency

---

## Segmentation Interpretation

The segmentation results suggest that transition-based telemetry analysis may provide a useful heuristic method for differentiating operational telemetry states.

The repeated appearance of these patterns across multiple MF4 datasets further supports the consistency of the segmentation logic.

---

# Correlation Analysis

Correlation analysis was performed across all byte fields within CAN ID 111.

## Key Findings

- Most byte correlations remained weak and close to zero
- `byte_4` and `byte_5` showed low correlation despite both being highly dynamic
- Multiple bytes appeared to behave independently

---

## Correlation Interpretation

These findings suggest that CAN ID 111 likely contains multiple independent signal fields with different operational roles.

The low correlation between dynamic bytes further supports the interpretation that:

- different bytes may encode unrelated operational signals
- multiple telemetry behaviors coexist within the same CAN frame

---

# Stable vs Dynamic Session Interpretation

Multi-file validation revealed three primary telemetry behavior categories:

| Session Type | Count |
| ------------ | ----- |
| Dynamic      | 3     |
| Mixed        | 3     |
| Stable       | 2     |

---

## Stable Sessions

Stable sessions showed:

- low transition magnitude
- low rolling variability
- minimal anomaly activity
- relatively consistent signal behavior

These sessions likely represent:

- idle-like operational states
- low-activity telemetry conditions
- steady-state vehicle behavior

---

## Dynamic Sessions

Dynamic sessions showed:

- high transition magnitude
- frequent abrupt signal changes
- elevated rolling standard deviation
- repeated anomaly clusters

These sessions likely represent:

- active operational behavior
- vehicle state transitions
- increased telemetry activity
- dynamic driving conditions

---

## Mixed Sessions

Mixed sessions contained both:

- stable telemetry regions
- short dynamic transition bursts

These datasets suggest intermittent operational state changes or alternating activity conditions.

---

# Anomaly Detection Findings

## Anomaly Detection Approach

Anomaly detection was performed using Byte 4 transition magnitude (`byte_4_diff`) as the primary telemetry instability indicator.

High transition events were treated as anomaly candidates when abrupt signal changes exceeded normal transition behavior.

---

## Observed Anomaly Characteristics

The analysis revealed several recurring anomaly behaviors:

- abrupt Byte 4 transitions
- elevated rolling variability
- clustered anomaly activity
- repeated rapid fluctuation patterns

Several telemetry regions produced transition magnitudes approaching the maximum possible signal difference.

---

## Dynamic Region Association

Anomaly activity consistently appeared more frequently within dynamic telemetry regions.

These regions also demonstrated:

- elevated signal variability
- increased transition density
- repeated operational state-like changes

This suggests that anomaly activity may be associated with periods of elevated telemetry activity or operational transitions.

---

## Cross-file Repeatability

Similar anomaly patterns appeared repeatedly across multiple MF4 datasets.

The repeated appearance of abrupt transition clusters suggests that the detected behavior was not isolated random noise.

Instead, the anomaly patterns likely represent recurring telemetry characteristics observable across multiple sessions.

---

## Monitoring Interpretation

The anomaly analysis demonstrated how transition-based telemetry monitoring may support:

- telemetry validation workflows
- anomaly-focused dashboard visualization
- operational state tracking
- dynamic telemetry monitoring

The results also demonstrated how abrupt transition analytics can help isolate unstable telemetry regions within large CAN datasets.

---

# Operational Interpretation

The overall telemetry analysis suggests that transition-based CAN signal behavior may reflect changes in vehicle operational activity.

Stable telemetry regions were associated with:

- low variability
- idle-like behavior
- reduced transition density

Dynamic telemetry regions were associated with:

- elevated signal activity
- abrupt transition events
- increased telemetry instability

These findings suggest that transition-based telemetry analytics may provide useful heuristic insight into operational vehicle behavior even without formal DBC decoding information.

---

# Validation Limitations

This project focused on exploratory telemetry analytics using reverse-engineered CAN signal behavior.

The exact semantic meaning of CAN ID 111 and Byte 4 was not formally decoded from OEM DBC specifications.

As a result:

- interpretations remain heuristic-based
- operational assumptions were inferred from observed telemetry behavior
- additional DBC metadata would improve interpretation accuracy

The segmentation and anomaly detection logic should therefore be interpreted as exploratory telemetry analytics rather than production-grade vehicle-state classification.

---

# Project Outcome

This project demonstrated:

- MF4 telemetry parsing and preprocessing
- byte-level CAN signal exploration
- transition-based behavioral analytics
- heuristic driving-state segmentation
- anomaly-focused telemetry monitoring
- cross-file validation workflows
- Athena SQL telemetry querying
- Tableau dashboard analytics visualization

The project also demonstrated how Python processing, cloud-based SQL analytics, and dashboard visualization can be combined into a telemetry-focused analytics workflow for CAN signal interpretation and telemetry monitoring.

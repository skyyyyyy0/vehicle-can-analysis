# Pattern Interpretation Analysis

## Objective

The purpose of this analysis was to interpret the behavioral characteristics of each byte within CAN ID 111 and identify potentially meaningful signal patterns.

The analysis focused on identifying:

- Dynamic signal bytes
- Stable bytes
- Possible sensor-like fields
- Possible flag or checksum-like fields

---

## Dominant Dynamic Bytes

Standard deviation analysis was performed on all byte fields.

### Standard Deviation Result

| Byte   | Std Dev |
| ------ | ------- |
| byte_4 | 120.01  |
| byte_5 | 106.51  |
| byte_0 | 87.27   |
| byte_6 | 78.29   |
| byte_2 | 68.15   |
| byte_3 | 64.46   |
| byte_1 | 42.13   |
| byte_7 | 9.81    |

The results showed that `byte_4` and `byte_5` were the most dynamic fields within CAN ID 111.

In contrast, `byte_7` showed very low variability and remained relatively stable throughout the dataset.

---

## Correlation Analysis

Correlation analysis was performed to determine whether multiple bytes moved together as related signals.

The correlation matrix showed that most byte relationships were weak and close to zero.

Example observations:

- `byte_4` vs `byte_5` correlation ≈ 0.07
- Most other byte correlations remained between -0.15 and 0.22

This suggests that the byte fields likely represent independent signal components rather than a single continuous measurement.

---

## Byte Behavior Comparison

Visualization analysis revealed several distinct behavior patterns.

### byte_4

- Extremely dynamic
- Frequent transitions between low and high values
- Repeated switching near 0 and 255
- Strong transition-like behavior

### byte_5

- Also highly dynamic
- Different transition timing compared to byte_4
- Appears independent despite similar variability

### byte_7

- Mostly stable near a constant range
- Occasional spikes
- Much lower variability compared to other bytes

---

## Signal Interpretation

Based on the observed patterns, the following interpretations were proposed.

| Byte   | Possible Interpretation                      |
| ------ | -------------------------------------------- |
| byte_4 | Dynamic transition / activity-related signal |
| byte_5 | Independent dynamic control-like signal      |
| byte_7 | Stable flag / checksum / state-related field |

The dynamic bytes did not behave like smooth continuous sensors such as temperature or speed signals.

Instead, the signals appeared more similar to operational state transitions or mode-switching behavior.

---

## Final Insight

The analysis suggests that CAN ID 111 contains multiple independent signal fields with different behavioral roles.

`byte_4` and `byte_5` showed strong dynamic transition behavior, while `byte_7` remained relatively stable throughout the recording.

These findings indicate that CAN ID 111 may represent a mixed control/state frame rather than a single continuous sensor measurement.

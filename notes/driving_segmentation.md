# Driving vs Idle Segmentation Analysis

## Objective

The goal of this analysis was to determine whether CAN ID 111 showed different behavioral patterns during potentially stable and dynamic driving conditions.

---

## Signal Selection

CAN ID 111 was selected based on:

- High occurrence frequency
- Significant byte-level variability
- Repeated transition patterns observed in byte_4

The analysis focused on `byte_4`.

---

## Heuristic Segmentation Method

To estimate driving activity, the absolute difference between consecutive `byte_4` values was calculated.

```python
byte_4_diff = abs(current_value - previous_value)
```

A heuristic threshold was then applied:

- `byte_4_diff <= 10` → idle
- `byte_4_diff > 10` → driving

This approach was used as a simple behavioral segmentation method.

---

## Segmentation Result

### Driving vs Idle Count

- Driving: 1016
- Idle: 583

The signal showed a reasonable separation between stable and dynamic sections.

---

## Statistical Observation

The analysis showed that:

- `byte_4` values alone did not clearly separate driving and idle states
- However, rapid transitions in `byte_4_diff` appeared more frequently during dynamic sections

Both states showed large overall variance, suggesting that the signal may behave more like a transition/state signal rather than a continuous sensor measurement.

---

## Visualization Insight

The visualization revealed:

- Stable plateau regions near 0 and 250
- Frequent transitions between these regions
- Dynamic transition sections were more commonly classified as driving

This suggests that the signal may reflect changing operational states or vehicle activity transitions.

---

## Final Insight

CAN ID 111 showed distinct transition behavior in `byte_4`, where rapid changes were associated with potentially dynamic vehicle activity. The signal appears to contain meaningful behavioral patterns that may be useful for driving state inference or efficiency-related analysis.

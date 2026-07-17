# IMU Vehicle-State Classification Error Analysis

## 1. Purpose

This document analyzes the misclassified one-second windows produced by the IMU-based Moving/Idle classification rule.

The objectives are to:

- Identify where the classification errors occurred
- Determine whether the errors were related to data-quality issues
- Examine likely causes of False Positives and False Negatives
- Document the limitations of using IMU activity as a vehicle-state proxy
- Recommend improvements for future validation

The analysis uses the officially decoded IMU feature `angular_rate_magnitude_mean`.

Ground-truth labels were derived independently from J1939 Vehicle Speed and Engine RPM.

---

## 2. Classification Setup

### 2.1 Primary Feature

```text
angular_rate_magnitude_mean
```

### 2.2 Selected Threshold

```text
2.290542511310978
```

The threshold was selected exclusively from the Development block by maximizing Macro F1.

It was frozen before evaluation and was not adjusted after reviewing the Validation results.

### 2.3 Prediction Rule

```text
IMU Activity >= 2.2905 → Predicted Moving
IMU Activity < 2.2905  → Predicted Idle
```

### 2.4 Ground-Truth Rules

```text
Moving: Speed >= 5 km/h AND RPM >= 500
Idle:   Speed < 1 km/h AND RPM >= 500
```

Windows labeled `ambiguous` or `engine_off_candidate` were excluded from the binary evaluation.

Because an Ignition signal was unavailable, Engine-Off status was not treated as a confirmed ground-truth class.

---

## 3. Overall Error Results

| Evaluation Block          | Windows |  TP |  TN |  FP |  FN | Error Rate |
| ------------------------- | ------: | --: | --: | --: | --: | ---------: |
| Development               |      34 |  20 |  10 |   4 |   0 |     11.76% |
| Within-Session Validation |      15 |   4 |   9 |   0 |   2 |     13.33% |
| Idle Stress Test          |      60 |   0 |  60 |   0 |   0 |      0.00% |
| Transition Diagnostic     |      11 |   0 |  11 |   0 |   0 |      0.00% |

### Error Summary

A total of six misclassified one-second windows were identified:

- Four False Positives
- Two False Negatives
- All six errors occurred in `FILE_001`
- No False Positives occurred in the Idle Stress Test
- No False Positives occurred in the Transition Diagnostic block

---

## 4. False Positive Analysis

A False Positive occurs when the ground-truth state is Idle, but IMU activity exceeds the selected threshold and the model predicts Moving.

### 4.1 Observed Pattern

| Item                      | Observation                               |
| ------------------------- | ----------------------------------------- |
| False Positive windows    | 4                                         |
| Ground-truth speed        | 0 km/h                                    |
| IMU activity range        | Approximately 3.40–6.53                   |
| Neighboring speed values  | Frequently around 4.1–4.6 km/h            |
| RPM changes               | Approximately 100–164 RPM in some windows |
| IMU records per window    | 5                                         |
| IMU valid ratio           | 100%                                      |
| Insufficient-sample flags | None                                      |

### 4.2 Interpretation

The False Positives appear to be associated primarily with low-speed start/stop transitions rather than missing or invalid data.

Although the aggregated one-second ground-truth speed was 0 km/h, neighboring windows frequently contained low-speed movement. The IMU may therefore have captured vehicle-body rotation, vibration, or residual motion during a short transition that the aggregated speed value labeled as Idle.

This pattern is consistent with a one-second window-boundary effect. Speed and IMU signals are collected at different frequencies, so short movements may not be represented identically after aggregation.

RPM changes may also have contributed to elevated IMU activity in some windows. However, possible door activity, external impacts, and other physical events cannot be confirmed because corresponding event sensors were unavailable.

### 4.3 Plausible Contributing Factors

- Start/stop activity near a one-second window boundary
- Low-speed movement mixed with a zero-speed period
- Engine vibration or RPM changes while stationary
- Different sampling frequencies across IMU, Speed, and RPM
- A short temporal delay between vehicle movement and IMU response

> These factors are diagnostic hypotheses and should not be interpreted as confirmed causal explanations.

---

## 5. False Negative Analysis

A False Negative occurs when the ground-truth state is Moving, but IMU activity remains below the selected threshold and the model predicts Idle.

### 5.1 Observed Pattern

| Item                      | Observation                            |
| ------------------------- | -------------------------------------- |
| False Negative windows    | 2                                      |
| Ground-truth speed        | Approximately 6.71–6.77 km/h           |
| IMU activity values       | Approximately 1.32 and 2.16            |
| Selected threshold        | Approximately 2.29                     |
| Closest threshold margin  | Approximately 0.13 below the threshold |
| RPM behavior              | Relatively stable                      |
| IMU records per window    | 5                                      |
| IMU valid ratio           | 100%                                   |
| Speed records per window  | Approximately 10                       |
| RPM records per window    | Approximately 50                       |
| Insufficient-sample flags | None                                   |

### 5.2 Interpretation

The False Negatives were not caused by missing values or insufficient sampling.

The vehicle was moving above the 5 km/h ground-truth boundary, but the decoded IMU activity remained low. This pattern is consistent with smooth, low-speed movement that produced limited rotational activity.

One of the two errors occurred close to the selected threshold and can be interpreted as a threshold-boundary case. The other showed substantially lower IMU activity, demonstrating that vehicle movement does not always produce strong rotational motion.

### 5.3 Plausible Contributing Factors

- Smooth and steady low-speed movement
- Straight-line movement with limited body rotation
- A feature value close to the classification threshold
- Short IMU activity being averaged within the one-second window
- The structural difference between rotational activity and vehicle speed

> This result demonstrates that IMU activity is related to vehicle movement but is not equivalent to vehicle speed.

---

## 6. Data-Quality Assessment

The six misclassified windows were evaluated for possible data-quality problems.

| Quality Check         | Result                              |
| --------------------- | ----------------------------------- |
| IMU valid ratio       | 100% for every error window         |
| IMU record count      | 5 records per window                |
| Speed record count    | Approximately 10 records per window |
| RPM record count      | Approximately 50 records per window |
| Timestamp alignment   | Valid                               |
| Duplicate join keys   | 0                                   |
| Python–SQL comparison | All 41 checks passed                |

### Assessment

The errors were more consistent with feature limitations and temporal aggregation effects than with:

- Missing data
- Invalid measurements
- Insufficient sampling
- Timestamp errors
- Duplicate records
- Implementation errors

The Python and Athena SQL implementations produced identical counts and metrics within the required tolerance of `0.000001`.

---

## 7. Recommended Improvements

### 7.1 Consecutive-Window Confirmation

Instead of changing the predicted state after a single threshold crossing, require the condition to remain true for two or three consecutive windows.

This approach may reduce isolated False Positives around start/stop transitions.

However, it may also delay the detection of actual state changes and must therefore be validated.

### 7.2 Rolling Features

Evaluate a two- or three-second rolling mean or median to reduce the influence of temporary IMU spikes.

Potential rolling features include:

- Two-second rolling mean
- Three-second rolling mean
- Two-second rolling median
- Three-second rolling median

A longer window may improve prediction stability but could delay the detection of actual movement. The window length should therefore be selected using validation data rather than chosen arbitrarily.

### 7.3 Multi-Feature Classification

The current classification rule uses only `angular_rate_magnitude_mean`.

Future analysis could combine it with:

- `angular_rate_magnitude_max`
- `angular_rate_magnitude_std`
- `acceleration_deviation_mean`
- `acceleration_deviation_max`

Using multiple IMU features may improve the distinction between:

- Smooth vehicle movement
- Stationary engine vibration
- Temporary physical impacts
- Start/stop transitions

### 7.4 Independent-Session Validation

The current results are based on one anonymized vehicle and one observed session.

The same frozen threshold should be evaluated on:

- Additional sessions from the same vehicle
- Different routes and operating conditions
- Additional vehicles
- Sessions containing longer Moving periods
- Sessions containing longer Idle periods
- Sessions with more frequent state transitions

Independent-session validation is required before making any claim about generalization.

---

## 8. Final Conclusion

The officially decoded IMU activity feature demonstrated a meaningful association with Moving and Idle states within the observed session.

### Within-Session Validation Results

| Metric              | Result |
| ------------------- | -----: |
| Accuracy            | 0.8667 |
| Macro F1            | 0.8500 |
| Balanced Accuracy   | 0.8333 |
| False Positive Rate | 0.0000 |

The model also classified all 60 Idle Stress Test windows as Idle. This indicates strong specificity within the observed idle-only segment, but it does not establish performance across independent sessions or vehicles.

The False Positives were concentrated around low-speed start/stop periods. The False Negatives occurred during smooth, low-speed movement with limited IMU activity.

These errors demonstrate that rotational IMU activity can support vehicle-activity monitoring but cannot independently confirm the true vehicle state under every operating condition.

### Final Interpretation

> Decoded IMU activity is a validated vehicle-activity proxy within the observed session, not a definitive vehicle-state signal.

Additional vehicles and independent sessions are required to determine whether the selected feature and frozen threshold generalize beyond the current dataset.

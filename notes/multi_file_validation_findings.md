# Multi-file Validation Findings

## Objective

The goal of this phase was to validate whether the previously discovered CAN ID 111 signal behavior remained consistent across multiple MF4 datasets before moving into Tableau dashboard development.

The validation process focused on:

- byte_4 transition behavior
- signal variability consistency
- driving vs idle segmentation
- recurring dynamic transition patterns
- stable vs dynamic session classification

---

# Validation Workflow

The following validation pipeline was performed across all MF4 datasets:

1. Load multiple MF4 files
2. Extract CAN ID 111 records
3. Parse byte_0 ~ byte_7 signal data
4. Calculate byte_4 transition differences
5. Detect dynamic transition patterns
6. Perform driving vs idle segmentation
7. Compare signal behavior across files
8. Generate cross-file validation visualizations

---

# Dataset Summary

A total of 8 MF4 validation datasets were processed.

The validation dataset included:

- stable sessions
- mixed sessions
- highly dynamic sessions

This allowed cross-session comparison of CAN signal behavior under different activity conditions.

---

# Key Findings

## 1. Cross-file byte_4 transition behavior

The analysis showed that byte_4 transition behavior appeared repeatedly across multiple MF4 datasets.

Several files demonstrated high transition activity:

- 00000004-69B82BA9.MF4
- 00000001-69B44F7F.MF4
- 00000002-69B8295A.MF4

These datasets produced:

- high mean byte_4 transition differences
- frequent abrupt signal changes
- high dynamic transition ratios

---

## 2. Stable vs dynamic sessions

The validation process identified three distinct session behavior categories:

| Session Type | Count |
| ------------ | ----- |
| Dynamic      | 3     |
| Mixed        | 3     |
| Stable       | 2     |

### Dynamic sessions

Dynamic sessions contained:

- frequent abrupt transitions
- higher signal variability
- larger byte_4 transition values

### Stable sessions

Stable sessions showed:

- minimal transition activity
- mostly idle behavior
- low signal variability

### Mixed sessions

Mixed sessions contained both:

- stable segments
- dynamic transition periods

---

## 3. Driving vs idle segmentation consistency

The driving vs idle segmentation logic generalized successfully across all MF4 datasets.

The segmentation process used byte_4 transition differences to identify:

- driving sections
- idle sections

The results showed that:

- files with high transition activity also produced higher driving ratios
- stable files remained mostly idle
- mixed files contained both driving and idle periods

This indicated that the segmentation heuristic remained consistent across multiple datasets.

---

## 4. Recurring dynamic transition patterns

Recurring dynamic transition patterns were observed across multiple MF4 files.

Several datasets repeatedly produced abrupt byte_4 changes approaching the maximum possible transition value.

This suggests that the detected signal behavior was not isolated to a single dataset and may represent meaningful CAN signal activity rather than random noise.

---

# Visualization Outputs

The following validation visualizations were generated:

- Dynamic transition ratio comparison
- Mean byte_4 transition difference comparison
- Session behavior distribution

Visualization files were saved under:

```text
outputs/screenshots/
```

Generated files:

```text
validation_dynamic_transition_ratio.png
validation_byte_4_diff_mean.png
validation_session_behavior_distribution.png
```

---

# Output Files

The following validation outputs were generated:

```text
outputs/multi_file_can_id_111.csv
outputs/multi_file_validation_summary.csv
```

These files contain:

- aggregated CAN ID 111 records
- transition statistics
- segmentation results
- session classifications
- cross-file validation metrics

---

# Conclusion

The multi-file validation phase confirmed that CAN ID 111 exhibited repeatable signal behaviors across multiple MF4 datasets.

Although transition intensity varied by session, the core signal characteristics remained observable across files.

The validation process also demonstrated that:

- the transition detection logic generalized successfully
- segmentation behavior remained consistent
- dynamic transition patterns repeatedly appeared across datasets

These findings established a validated foundation for the next phase of Tableau dashboard development and cross-file CAN signal analytics.

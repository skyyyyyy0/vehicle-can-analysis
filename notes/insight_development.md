## Insight 1 — Dynamic Transition Behavior in byte_4

The analysis revealed that `byte_4` within CAN ID 111 showed repeated high-frequency transitions between low and high values.

During the driving vs idle segmentation process, dynamic sections consistently produced larger `byte_4_diff` values, while stable sections showed relatively small changes.

This suggests that `byte_4` may reflect dynamic vehicle activity or operational state transitions rather than a smooth continuous sensor measurement.

The repeated transition behavior may be associated with changes in driving conditions, engine load, or vehicle operational modes.

---

## Insight 2 — Independent Signal Structure Within CAN ID 111

Correlation analysis showed that most byte relationships within CAN ID 111 were weak and close to zero.

Although `byte_4` and `byte_5` both displayed highly dynamic behavior, their correlation remained very low, suggesting that they may represent independent signal components.

This indicates that CAN ID 111 likely contains multiple operational fields with different behavioral roles rather than a single continuous measurement.

The observed structure resembles a mixed control/state frame commonly seen in telemetry and embedded vehicle communication systems.

---

## Insight 3 — Stable Behavior of byte_7

Unlike the highly dynamic behavior observed in `byte_4` and `byte_5`, `byte_7` remained relatively stable throughout the dataset.

The byte showed very low standard deviation and weak correlation with other fields, indicating limited dynamic interaction with surrounding signals.

This behavior suggests that `byte_7` may function as a stable operational field such as a status flag, identifier, or checksum-related component within the CAN frame structure.

The contrast between highly dynamic and highly stable bytes further supports the interpretation that CAN ID 111 contains multiple independent signal roles.

---

## Insight 4 — Consistent Transition-Based Segmentation Across Multiple Datasets

The transition-based segmentation heuristic remained consistent across multiple MF4 validation datasets.

Files with elevated transition activity consistently produced:

- higher driving ratios
- increased signal variability
- more dynamic telemetry regions

Stable sessions remained dominated by low-transition idle-like behavior.

This consistency suggests that transition-magnitude-based segmentation may provide a useful heuristic for identifying operational telemetry states across different driving sessions.

The repeated appearance of stable and dynamic segmentation patterns across multiple files further supports the repeatability of the observed telemetry behavior.

---

## Insight 5 — Anomaly Clustering and Telemetry Monitoring Relevance

Anomaly detection analysis revealed that extreme Byte 4 transition events frequently appeared in clustered telemetry regions rather than isolated random points.

These anomaly clusters were strongly associated with:

- elevated rolling variability
- dynamic operational regions
- repeated abrupt signal transitions

The repeated appearance of anomaly clusters across multiple MF4 sessions suggests that the detected behavior may represent recurring telemetry-state transition activity rather than isolated signal noise.

This demonstrates how transition-based telemetry analytics may support:

- anomaly-focused monitoring workflows
- telemetry validation systems
- operational state tracking
- dashboard-based telemetry monitoring

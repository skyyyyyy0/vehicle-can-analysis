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

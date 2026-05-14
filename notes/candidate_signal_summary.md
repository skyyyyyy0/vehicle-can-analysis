# Candidate Signal Summary

## Final Selected Signal

- CAN ID: 111
- Primary byte analyzed: byte_4
- Supporting bytes analyzed: byte_5, byte_7

---

## Why CAN ID 111 Was Selected

CAN ID 111 was selected as the main candidate signal because it showed:

- High transmission frequency
- Strong byte-level variability
- Repeated transition behavior over time
- Clear differences between stable and dynamic sections

---

## Key Signal Behavior

The analysis showed that `byte_4` frequently transitioned between low and high values.

This behavior suggests that `byte_4` may represent a dynamic operational signal rather than a smooth continuous sensor value.

`byte_5` also showed strong variability, but its behavior appeared mostly independent from `byte_4`.

`byte_7` remained relatively stable and may represent a status flag, identifier, or checksum-related field.

---

## Driving vs Idle Interpretation

A heuristic threshold was applied using `byte_4_diff`.

- Low variation was interpreted as idle-like behavior
- High variation was interpreted as driving-like behavior

This helped separate stable and dynamic signal sections for further analysis.

---

## Final Interpretation

CAN ID 111 appears to contain multiple signal fields with different roles.

The strongest finding is that `byte_4` and `byte_5` show dynamic transition behavior, while `byte_7` remains stable.

This suggests that CAN ID 111 may represent a mixed operational or control-state frame rather than a single continuous sensor signal.

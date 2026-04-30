# CAN Signal Analysis Notes

## Candidate Signal

- CAN ID: 111

---

## Byte-Level Findings

### byte_4

- High standard deviation
- Continuous fluctuation over time
- Likely dynamic signal

### byte_7

- Low variation
- Possibly static flag or checksum

---

## Visualization Insight

The byte_4 signal showed rapid fluctuations across timestamps, suggesting dynamic vehicle-state behavior.

---

## Hypothesis

CAN ID 111 byte_4 may be related to driving activity, engine load, or efficiency-related behavior.

---

## Final Candidate Selection

### Selected CAN ID

- CAN ID: 111

### Selection Reason

- High transmission frequency
- Dynamic byte-level variability
- Strong fluctuation in byte_4 and byte_5
- Repeated temporal signal behavior

### Conclusion

CAN ID 111 was selected as the primary candidate signal for further reverse engineering and behavioral analysis.

---

## Byte Variability Verification

### High Variability Bytes

- byte_4 showed the highest standard deviation
- byte_5 also showed strong variability

### Low Variability Bytes

- byte_7 remained relatively stable

### Interpretation

The high variability of byte_4 and byte_5 suggests that these bytes may contain dynamic vehicle operational signals, while byte_7 may represent a static control or checksum-related field.

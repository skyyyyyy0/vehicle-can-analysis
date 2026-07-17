# IMU Ground-Truth Validation Findings

## 1. Objective

Validate whether officially decoded IMU activity can distinguish Moving and Idle vehicle states using J1939 Vehicle Speed and Engine RPM as ground truth.

---

## 2. Validation Scope

- Vehicle: 1 anonymized vehicle
- Session: 1 continuous session
- Binary analysis windows: 120
- Primary feature: `angular_rate_magnitude_mean`
- Selected threshold: `2.2905`
- Split method: Chronological block split
- Random row splitting was not used

---

## 3. Final Results

### Development Performance

- Windows: 34
- Macro F1: `0.8712`
- Balanced Accuracy: `0.8571`
- Moving Recall: `1.0000`

### Within-Session Validation Performance

- Windows: 15
- Accuracy: `0.8667`
- Macro F1: `0.8500`
- Balanced Accuracy: `0.8333`
- False Positive Rate: `0.0000`
- TP / TN / FP / FN: `4 / 9 / 0 / 2`

### Idle Stress Test

- Idle windows: 60
- Correctly classified: 60
- False Positives: 0
- Specificity: `1.0000`

### Python–SQL Validation

- Comparison checks: 41
- Passed checks: 41
- Count difference: 0
- Metric difference: Within `0.000001`

---

## 4. Error Findings

- Four Development False Positives occurred near low-speed start/stop periods.
- Two Validation False Negatives occurred during smooth low-speed movement.
- All error windows had complete and valid IMU, Speed, and RPM records.
- The errors were more consistent with window-boundary and feature limitations than with missing data.

---

## 5. Interpretation

Decoded IMU activity demonstrated a meaningful association with vehicle movement within the observed session.

However, smooth low-speed movement did not always generate sufficient IMU activity, while start/stop transitions occasionally produced elevated activity during zero-speed windows.

Therefore, IMU activity is useful as a vehicle-activity proxy but should not be treated as a definitive Moving/Idle signal.

---

## 6. Limitations

- Only one vehicle was analyzed.
- Only one continuous session was available.
- Validation was performed within the same session.
- Independent-session generalization was not tested.
- Ignition data was unavailable.
- Engine-Off status could not be independently confirmed.
- Door activity and external impacts could not be verified.

---

## 7. Final Conclusion

> Decoded IMU activity showed a meaningful association with vehicle movement within the observed session. However, because validation was limited to one vehicle and one session, the signal should be treated as a vehicle-activity proxy rather than a definitive Moving/Idle indicator.

---

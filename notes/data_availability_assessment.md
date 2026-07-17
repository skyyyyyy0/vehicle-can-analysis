# Ground-Truth Data Availability Assessment

**Assessment Date:** July 14, 2026  
**Vehicle ID:** VEH_01  
**Session ID:** SES_00000074  
**Purpose:** Determine whether independent vehicle-state signals are available to validate CAN ID 111 Byte 4 transition patterns.

## 1. Background

The original analysis interpreted CAN ID 111 Byte 4 transition patterns as driving and idle behavior. However, this interpretation was not validated against independently decoded vehicle-state signals.

This assessment examines the availability of Vehicle Speed, Engine RPM, Ignition, timestamps, and session identifiers required for ground-truth validation.

## 2. Initial GNSS Assessment

The device configuration included a GNSS Speed definition associated with CAN ID 107 (`0x06B`). However, the initial MF4 files contained only CAN IDs 101 and 111.

GNSS Status decoding produced the following results:

- GNSS Fix Type: No Fix
- Maximum satellite count: 0
- CAN ID 107 GNSS Speed frames: Not present
- Valid GNSS Speed records: 0

Therefore, GNSS Speed could not be used as ground truth.

## 3. J1939 Signal Discovery

Additional MF4 sessions were inspected by extracting the complete CAN ID inventory.

The following J1939 signals were discovered in session `SES_00000074`:

| Signal                    |      PGN | SPN | Byte Position |     Scale | Unit  | Approximate Frequency |
| ------------------------- | -------: | --: | ------------- | --------: | ----- | --------------------: |
| Wheel-Based Vehicle Speed | `0xFEF1` |  84 | Bytes 2–3     |     1/256 | km/h  |                 10 Hz |
| Engine Speed              | `0xF004` | 190 | Bytes 4–5     |     0.125 | RPM   |                 50 Hz |
| CAN ID 111 Byte 4         |  `0x06F` | N/A | Byte index 4  | Raw value | 0–255 |                  5 Hz |

Multi-byte J1939 values were decoded using little-endian byte order.

## 4. Identifier and Timestamp Availability

| Required Field | Status        | Implementation                     |
| -------------- | ------------- | ---------------------------------- |
| Vehicle ID     | Available     | Anonymized as `VEH_01`             |
| Session ID     | Available     | `SES_00000074`                     |
| Source File ID | Available     | Original MF4 filename retained     |
| Timestamp      | Available     | Converted to UTC datetime          |
| Vehicle Speed  | Available     | Decoded from PGN `0xFEF1`          |
| Engine RPM     | Available     | Decoded from PGN `0xF004`          |
| Ignition       | Not available | No confirmed Ignition signal found |

CAN ID 111, Vehicle Speed, and Engine RPM were recorded in the same MF4 files with overlapping measurement periods.

For example, file `00007172-69EA7237.MF4` contained:

- CAN ID 111: 17:30:00.097–17:30:59.894 UTC
- Vehicle Speed: 17:30:00.029–17:30:59.954 UTC
- Engine RPM: 17:30:00.009–17:30:59.993 UTC

This confirms that the signals can be aligned using a one-second timestamp window.

## 5. File-Level Assessment

| Source File             |   Speed Range |       RPM Range | Ground-Truth Use              |
| ----------------------- | ------------: | --------------: | ----------------------------- |
| `00007171-69EA7231.MF4` |  0–10.98 km/h | 703.88–1,336.25 | Moving and Idle validation    |
| `00007172-69EA7237.MF4` |        0 km/h |   744.00–760.38 | Idle validation               |
| `00007173-69EA723B.MF4` |        0 km/h |        0–754.50 | Idle and Engine-Off candidate |
| `00007174-69EA723D.MF4` | Not available |   Not available | Excluded                      |
| `00007201-69EA7259.MF4` | Not available |   Not available | Excluded                      |

## 6. Ground-Truth Label Scope

The following validation labels can be supported:

- **Moving:** Vehicle Speed ≥ 5 km/h and Engine RPM ≥ 500
- **Idle:** Vehicle Speed < 1 km/h and Engine RPM ≥ 500
- **Ambiguous:** Vehicle Speed between 1 and 5 km/h or incomplete state information
- **Engine-Off Candidate:** Vehicle Speed < 1 km/h and Engine RPM ≤ 100

Because an Ignition signal is unavailable, Engine-Off cannot be independently confirmed. Therefore, it is labeled as `engine_off_candidate` and excluded from the primary Moving-versus-Idle accuracy evaluation.

## 7. Final Decision

Ground-truth validation can proceed for the primary Moving-versus-Idle classification.

The validation dataset will be created by:

1. Aggregating CAN ID 111 Byte 4 transition features into one-second windows.
2. Aggregating Vehicle Speed and Engine RPM into the same one-second windows.
3. Joining records by Vehicle ID, Session ID, Source File, and UTC timestamp.
4. Excluding ambiguous and unmatched periods from the primary evaluation.
5. Reporting timestamp match coverage and class distribution.

## 8. Limitations

- Ignition status is unavailable.
- GNSS Speed is unavailable because the inspected GNSS records had no valid fix.
- The current validation data represents one anonymized vehicle.
- Moving observations are less frequent than Idle observations.
- Engine-Off remains an inferred candidate state rather than confirmed ground truth.

## Assessment Result

**Status: Sufficient for Moving-versus-Idle validation**

Vehicle Speed and Engine RPM are available within the same files and time ranges as CAN ID 111 Byte 4. The project can proceed to one-second timestamp alignment and threshold validation.

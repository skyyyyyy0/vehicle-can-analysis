from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


INPUT_DIR = Path("data/raw/VEH_01/candidate_sessions")
OUTPUT_FILE = Path("outputs/reports/gnss_candidate_session_summary.csv")

GNSS_STATUS_ID = 101  # 0x065
GNSS_SPEED_ID = 107   # 0x06B


def payload_to_bytes(payload):
    return bytes(np.asarray(payload, dtype=np.uint8).reshape(-1))


def inspect_mf4(file_path):
    mdf = MDF(str(file_path))

    can_ids = set()
    status_records = 0
    valid_fix_records = 0
    max_satellites = 0

    speed_records = 0
    valid_speed_records = 0
    moving_speed_records = 0
    max_speed_kmh = 0.0

    try:
        for group_index, channel_index in mdf.channels_db.get(
            "CAN_DataFrame", []
        ):
            signal = mdf.get(
                "CAN_DataFrame",
                group=group_index,
                index=channel_index,
            )
            samples = signal.samples
            fields = samples.dtype.names or ()

            id_field = next(
                (name for name in fields if name.endswith(".ID")),
                None,
            )
            data_field = next(
                (name for name in fields if "DataBytes" in name),
                None,
            )

            if id_field is None or data_field is None:
                continue

            ids = samples[id_field].astype("uint32") & 0x1FFFFFFF
            can_ids.update(int(value) for value in np.unique(ids))

            # GNSS Status: Fix Type 및 위성 수 확인
            for payload in samples[data_field][ids == GNSS_STATUS_ID]:
                data = payload_to_bytes(payload)
                if not data:
                    continue

                status_records += 1
                fix_type = data[0] & 0b111
                satellites = (data[0] >> 3) & 0b11111

                if fix_type in {2, 3, 4}:
                    valid_fix_records += 1

                max_satellites = max(max_satellites, satellites)

            # GNSS Speed: SpeedValid 및 속도 확인
            for payload in samples[data_field][ids == GNSS_SPEED_ID]:
                data = payload_to_bytes(payload)
                if len(data) < 5:
                    continue

                speed_records += 1
                raw = int.from_bytes(data[:5], byteorder="little")
                speed_valid = raw & 0b1
                speed_mps = ((raw >> 1) & ((1 << 20) - 1)) * 0.001
                speed_kmh = speed_mps * 3.6

                if speed_valid == 1:
                    valid_speed_records += 1
                    max_speed_kmh = max(max_speed_kmh, speed_kmh)

                    if speed_kmh >= 5:
                        moving_speed_records += 1

        return {
            "session_id": file_path.parent.name,
            "source_file": file_path.name,
            "mf4_start_time_utc": mdf.header.start_time.isoformat(),
            "can_ids_hex": ", ".join(
                f"0x{can_id:03X}" for can_id in sorted(can_ids)
            ),
            "gnss_status_records": status_records,
            "valid_fix_records": valid_fix_records,
            "max_satellites": max_satellites,
            "gnss_speed_records": speed_records,
            "valid_speed_records": valid_speed_records,
            "moving_speed_records": moving_speed_records,
            "max_speed_kmh": round(max_speed_kmh, 2),
            "usable_ground_truth": valid_speed_records > 0,
        }
    finally:
        mdf.close()


files = sorted(INPUT_DIR.rglob("*.MF4"))
results = [inspect_mf4(file_path) for file_path in files]

summary = pd.DataFrame(results)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT_FILE, index=False)

print(summary.to_string(index=False))
print(f"\nSaved to: {OUTPUT_FILE}")
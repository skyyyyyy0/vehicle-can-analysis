from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


INPUT_DIR = Path(
    "data/raw/VEH_01/candidate_sessions/SES_00000074"
)
OUTPUT_FILE = Path(
    "data/processed/can_byte4_processed.csv"
)

VALID_FILES = {
    "00007171-69EA7231.MF4",
    "00007172-69EA7237.MF4",
    "00007173-69EA723B.MF4",
}

TARGET_CAN_ID = 111
VEHICLE_ID = "VEH_01"
SESSION_ID = "SES_00000074"


def payload_to_bytes(payload):
    return bytes(np.asarray(payload, dtype=np.uint8).reshape(-1))


records = []

for file_path in sorted(INPUT_DIR.rglob("*.MF4")):
    if file_path.name not in VALID_FILES:
        continue

    mdf = MDF(str(file_path))
    start_time = pd.Timestamp(mdf.header.start_time)

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
            target_mask = ids == TARGET_CAN_ID

            timestamps = signal.timestamps[target_mask]
            payloads = samples[data_field][target_mask]

            for time_offset, payload in zip(timestamps, payloads):
                data = payload_to_bytes(payload)

                if len(data) < 5:
                    continue

                timestamp = (
                    start_time
                    + pd.to_timedelta(float(time_offset), unit="s")
                )

                records.append({
                    "vehicle_id": VEHICLE_ID,
                    "session_id": SESSION_ID,
                    "source_file": file_path.name,
                    "timestamp": timestamp,
                    "byte_4": int(data[4]),
                })

    finally:
        mdf.close()


can_byte4 = pd.DataFrame(records)

can_byte4 = can_byte4.sort_values(
    ["source_file", "timestamp"]
).reset_index(drop=True)

# uint8 오류 방지
can_byte4["byte_4"] = can_byte4["byte_4"].astype("int16")

# 파일 경계를 넘지 않도록 차분
can_byte4["byte_4_diff"] = (
    can_byte4
    .groupby(
        ["vehicle_id", "session_id", "source_file"]
    )["byte_4"]
    .diff()
    .abs()
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
can_byte4.to_csv(OUTPUT_FILE, index=False)

summary = (
    can_byte4.groupby("source_file")
    .agg(
        record_count=("byte_4", "size"),
        byte_4_min=("byte_4", "min"),
        byte_4_max=("byte_4", "max"),
        diff_max=("byte_4_diff", "max"),
        first_timestamp=("timestamp", "min"),
        last_timestamp=("timestamp", "max"),
    )
)

print(summary.to_string())
print(f"\nSaved to: {OUTPUT_FILE}")
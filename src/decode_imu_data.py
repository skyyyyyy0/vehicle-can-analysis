from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


INPUT_DIR = Path(
    "data/raw/VEH_01/candidate_sessions/SES_00000074"
)

OUTPUT_FILE = Path(
    "data/processed/imu_signals_processed.csv"
)

SUMMARY_FILE = Path(
    "outputs/validation/imu_signal_summary.csv"
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
    return bytes(
        np.asarray(
            payload,
            dtype=np.uint8,
        ).reshape(-1)
    )


def extract_bits(raw_payload, start_bit, length):
    mask = (1 << length) - 1
    return (raw_payload >> start_bit) & mask


def decode_physical(
    raw_payload,
    start_bit,
    length,
    factor,
    offset,
):
    raw_value = extract_bits(
        raw_payload,
        start_bit,
        length,
    )
    return raw_value * factor + offset


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
                (
                    name
                    for name in fields
                    if name.endswith(".ID")
                ),
                None,
            )

            data_field = next(
                (
                    name
                    for name in fields
                    if "DataBytes" in name
                ),
                None,
            )

            if id_field is None or data_field is None:
                continue

            ids = (
                samples[id_field].astype("uint32")
                & 0x1FFFFFFF
            )

            target_mask = ids == TARGET_CAN_ID

            timestamps = signal.timestamps[target_mask]
            payloads = samples[data_field][target_mask]

            for time_offset, payload in zip(
                timestamps,
                payloads,
            ):
                data = payload_to_bytes(payload)

                if len(data) < 8:
                    continue

                raw_payload = int.from_bytes(
                    data[:8],
                    byteorder="little",
                    signed=False,
                )

                timestamp = (
                    start_time
                    + pd.to_timedelta(
                        float(time_offset),
                        unit="s",
                    )
                )

                imu_valid = extract_bits(
                    raw_payload,
                    start_bit=0,
                    length=1,
                )

                if imu_valid == 1:
                    acceleration_x = decode_physical(
                        raw_payload, 1, 10, 0.125, -64
                    )
                    acceleration_y = decode_physical(
                        raw_payload, 11, 10, 0.125, -64
                    )
                    acceleration_z = decode_physical(
                        raw_payload, 21, 10, 0.125, -64
                    )

                    angular_rate_x = decode_physical(
                        raw_payload, 31, 11, 0.25, -256
                    )
                    angular_rate_y = decode_physical(
                        raw_payload, 42, 11, 0.25, -256
                    )
                    angular_rate_z = decode_physical(
                        raw_payload, 53, 11, 0.25, -256
                    )

                else:
                    acceleration_x = np.nan
                    acceleration_y = np.nan
                    acceleration_z = np.nan
                    angular_rate_x = np.nan
                    angular_rate_y = np.nan
                    angular_rate_z = np.nan

                records.append({
                    "vehicle_id": VEHICLE_ID,
                    "session_id": SESSION_ID,
                    "source_file": file_path.name,
                    "timestamp": timestamp,
                    "imu_valid": int(imu_valid),
                    "acceleration_x": acceleration_x,
                    "acceleration_y": acceleration_y,
                    "acceleration_z": acceleration_z,
                    "angular_rate_x": angular_rate_x,
                    "angular_rate_y": angular_rate_y,
                    "angular_rate_z": angular_rate_z,
                })

    finally:
        mdf.close()


imu_data = pd.DataFrame(records)

if imu_data.empty:
    raise ValueError(
        "No CAN ID 111 IMU records were decoded."
    )

imu_data = imu_data.sort_values(
    [
        "vehicle_id",
        "session_id",
        "source_file",
        "timestamp",
    ]
).reset_index(drop=True)


# IMU 벡터 크기 계산
imu_data["acceleration_magnitude"] = np.sqrt(
    imu_data["acceleration_x"] ** 2
    + imu_data["acceleration_y"] ** 2
    + imu_data["acceleration_z"] ** 2
)

imu_data["angular_rate_magnitude"] = np.sqrt(
    imu_data["angular_rate_x"] ** 2
    + imu_data["angular_rate_y"] ** 2
    + imu_data["angular_rate_z"] ** 2
)


# 결과 저장
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)

imu_data.to_csv(OUTPUT_FILE, index=False)


# 파일별 요약
summary = (
    imu_data
    .groupby(
        ["vehicle_id", "session_id", "source_file"],
        as_index=False,
    )
    .agg(
        record_count=("imu_valid", "size"),
        valid_record_count=("imu_valid", "sum"),
        imu_valid_ratio=("imu_valid", "mean"),
        acceleration_magnitude_mean=(
            "acceleration_magnitude",
            "mean",
        ),
        acceleration_magnitude_max=(
            "acceleration_magnitude",
            "max",
        ),
        angular_rate_magnitude_mean=(
            "angular_rate_magnitude",
            "mean",
        ),
        angular_rate_magnitude_max=(
            "angular_rate_magnitude",
            "max",
        ),
        first_timestamp=("timestamp", "min"),
        last_timestamp=("timestamp", "max"),
    )
)

summary["imu_valid_ratio_pct"] = (
    summary["imu_valid_ratio"] * 100
).round(2)

summary.to_csv(SUMMARY_FILE, index=False)


# 유효한 IMU 신호 범위
valid_data = imu_data.loc[
    imu_data["imu_valid"] == 1
]

signal_columns = [
    "acceleration_x",
    "acceleration_y",
    "acceleration_z",
    "angular_rate_x",
    "angular_rate_y",
    "angular_rate_z",
    "acceleration_magnitude",
    "angular_rate_magnitude",
]

print("\nIMU file summary:")
print(
    summary[
        [
            "source_file",
            "record_count",
            "valid_record_count",
            "imu_valid_ratio_pct",
            "acceleration_magnitude_mean",
            "acceleration_magnitude_max",
            "angular_rate_magnitude_mean",
            "angular_rate_magnitude_max",
        ]
    ].to_string(index=False)
)

print("\nValid IMU signal ranges:")
print(
    valid_data[signal_columns]
    .agg(["min", "max"])
    .round(4)
    .to_string()
)

print(f"\nSaved to: {OUTPUT_FILE}")
print(f"Saved to: {SUMMARY_FILE}")
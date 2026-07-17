from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


INPUT_DIR = Path(
    "data/raw/VEH_01/candidate_sessions/SES_00000074"
)

RAW_OUTPUT = Path(
    "data/processed/j1939_ground_truth_raw.csv"
)
PROCESSED_OUTPUT = Path(
    "data/processed/ground_truth_processed.csv"
)
LABEL_OUTPUT = Path(
    "outputs/validation/ground_truth_label_distribution.csv"
)

VALID_FILES = {
    "00007171-69EA7231.MF4",
    "00007172-69EA7237.MF4",
    "00007173-69EA723B.MF4",
}

SPEED_PGN = 0xFEF1
RPM_PGN = 0xF004

VEHICLE_ID = "VEH_01"
SESSION_ID = "SES_00000074"


def get_pgn(can_id):
    pf = (can_id >> 16) & 0xFF
    pgn = (can_id >> 8) & 0x3FFFF

    if pf < 240:
        pgn &= 0x3FF00

    return pgn


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

            for can_id, time_offset, payload in zip(
                ids,
                signal.timestamps,
                samples[data_field],
            ):
                pgn = get_pgn(int(can_id))

                if pgn not in {SPEED_PGN, RPM_PGN}:
                    continue

                data = payload_to_bytes(payload)

                if len(data) < 5:
                    continue

                timestamp = (
                    start_time
                    + pd.to_timedelta(float(time_offset), unit="s")
                )

                if pgn == SPEED_PGN:
                    raw = int.from_bytes(data[1:3], "little")

                    if raw <= 0xFAFF:
                        records.append({
                            "vehicle_id": VEHICLE_ID,
                            "session_id": SESSION_ID,
                            "source_file": file_path.name,
                            "timestamp": timestamp,
                            "signal_name": "vehicle_speed_kmh",
                            "value": raw / 256,
                        })

                elif pgn == RPM_PGN:
                    raw = int.from_bytes(data[3:5], "little")

                    if raw <= 0xFAFF:
                        records.append({
                            "vehicle_id": VEHICLE_ID,
                            "session_id": SESSION_ID,
                            "source_file": file_path.name,
                            "timestamp": timestamp,
                            "signal_name": "engine_rpm",
                            "value": raw * 0.125,
                        })

    finally:
        mdf.close()


raw_data = pd.DataFrame(records)
raw_data = raw_data.sort_values(
    ["source_file", "timestamp", "signal_name"]
)
raw_data.to_csv(RAW_OUTPUT, index=False)

raw_data["timestamp_1s"] = (
    pd.to_datetime(raw_data["timestamp"], utc=True)
    .dt.floor("s")
)

group_columns = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
]

# 각 1초 구간의 중앙값
median_values = (
    raw_data
    .pivot_table(
        index=group_columns,
        columns="signal_name",
        values="value",
        aggfunc="median",
    )
    .reset_index()
)

# 각 1초 구간의 원본 레코드 수
record_counts = (
    raw_data
    .groupby(group_columns + ["signal_name"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
    .rename(columns={
        "vehicle_speed_kmh": "speed_record_count",
        "engine_rpm": "rpm_record_count",
    })
)

ground_truth = median_values.merge(
    record_counts,
    on=group_columns,
    how="left",
)

# Byte 4를 사용하지 않고 실제 Speed·RPM만으로 라벨 생성
conditions = [
    (
        (ground_truth["vehicle_speed_kmh"] >= 5)
        & (ground_truth["engine_rpm"] >= 500)
    ),
    (
        (ground_truth["vehicle_speed_kmh"] < 1)
        & (ground_truth["engine_rpm"] >= 500)
    ),
    (
        (ground_truth["vehicle_speed_kmh"] < 1)
        & (ground_truth["engine_rpm"] <= 100)
    ),
]

labels = [
    "moving",
    "idle",
    "engine_off_candidate",
]

ground_truth["ground_truth_state"] = np.select(
    conditions,
    labels,
    default="ambiguous",
)

ground_truth = ground_truth.sort_values(
    ["source_file", "timestamp_1s"]
)

PROCESSED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
LABEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

ground_truth.to_csv(PROCESSED_OUTPUT, index=False)

label_distribution = (
    ground_truth
    .groupby(["source_file", "ground_truth_state"])
    .size()
    .reset_index(name="second_count")
)

label_distribution.to_csv(LABEL_OUTPUT, index=False)

print("\nGround-Truth label distribution:")
print(
    label_distribution
    .pivot(
        index="source_file",
        columns="ground_truth_state",
        values="second_count",
    )
    .fillna(0)
    .astype(int)
    .to_string()
)

print(f"\nSaved to: {PROCESSED_OUTPUT}")
print(f"Saved to: {LABEL_OUTPUT}")
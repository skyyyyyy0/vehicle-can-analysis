from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


INPUT_FILE = Path(
    "data/raw/VEH_01/candidate_sessions/"
    "SES_00000074/00007172-69EA7237.MF4"
)

OUTPUT_FILE = Path(
    "data/processed/j1939_ground_truth_raw.csv"
)

VEHICLE_ID = "VEH_01"
SESSION_ID = "SES_00000074"

VEHICLE_SPEED_PGN = 0xFEF1
ENGINE_SPEED_PGN = 0xF004


def get_pgn(can_id):
    pf = (can_id >> 16) & 0xFF
    pgn = (can_id >> 8) & 0x3FFFF

    if pf < 240:
        pgn &= 0x3FF00

    return pgn


def payload_to_bytes(payload):
    return bytes(np.asarray(payload, dtype=np.uint8).reshape(-1))


records = []
mdf = MDF(str(INPUT_FILE))
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
            can_id = int(can_id)
            pgn = get_pgn(can_id)

            if pgn not in {VEHICLE_SPEED_PGN, ENGINE_SPEED_PGN}:
                continue

            data = payload_to_bytes(payload)

            if len(data) < 5:
                continue

            timestamp = (
                start_time
                + pd.to_timedelta(float(time_offset), unit="s")
            )

            # PGN FEF1, SPN 84: Byte 2~3, 1/256 km/h
            if pgn == VEHICLE_SPEED_PGN:
                raw_value = int.from_bytes(
                    data[1:3],
                    byteorder="little",
                )

                if raw_value <= 0xFAFF:
                    records.append({
                        "vehicle_id": VEHICLE_ID,
                        "session_id": SESSION_ID,
                        "timestamp": timestamp,
                        "signal_name": "vehicle_speed_kmh",
                        "value": raw_value / 256,
                        "source_can_id": f"0x{can_id:08X}",
                    })

            # PGN F004, SPN 190: Byte 4~5, 0.125 RPM
            elif pgn == ENGINE_SPEED_PGN:
                raw_value = int.from_bytes(
                    data[3:5],
                    byteorder="little",
                )

                if raw_value <= 0xFAFF:
                    records.append({
                        "vehicle_id": VEHICLE_ID,
                        "session_id": SESSION_ID,
                        "timestamp": timestamp,
                        "signal_name": "engine_rpm",
                        "value": raw_value * 0.125,
                        "source_can_id": f"0x{can_id:08X}",
                    })

finally:
    mdf.close()


ground_truth = pd.DataFrame(records)
ground_truth = ground_truth.sort_values(
    ["timestamp", "signal_name"]
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
ground_truth.to_csv(OUTPUT_FILE, index=False)

summary = (
    ground_truth.groupby("signal_name")["value"]
    .agg(["count", "min", "median", "mean", "max"])
    .round(2)
)

print(summary)
print("\nTimestamp range:")
print(ground_truth.groupby("signal_name")["timestamp"].agg(["min", "max"]))
print(f"\nSaved to: {OUTPUT_FILE}")
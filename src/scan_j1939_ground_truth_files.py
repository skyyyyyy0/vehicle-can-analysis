from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


INPUT_DIR = Path(
    "data/raw/VEH_01/candidate_sessions/SES_00000074"
)
OUTPUT_FILE = Path(
    "outputs/reports/j1939_ground_truth_file_summary.csv"
)

SPEED_PGN = 0xFEF1
RPM_PGN = 0xF004


def get_pgn(can_id):
    pf = (can_id >> 16) & 0xFF
    pgn = (can_id >> 8) & 0x3FFFF

    if pf < 240:
        pgn &= 0x3FF00

    return pgn


def payload_to_bytes(payload):
    return bytes(np.asarray(payload, dtype=np.uint8).reshape(-1))


def inspect_file(file_path):
    speeds = []
    rpms = []
    mdf = MDF(str(file_path))

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

            for can_id, payload in zip(ids, samples[data_field]):
                pgn = get_pgn(int(can_id))

                if pgn not in {SPEED_PGN, RPM_PGN}:
                    continue

                data = payload_to_bytes(payload)

                if len(data) < 5:
                    continue

                if pgn == SPEED_PGN:
                    raw = int.from_bytes(data[1:3], "little")

                    if raw <= 0xFAFF:
                        speeds.append(raw / 256)

                elif pgn == RPM_PGN:
                    raw = int.from_bytes(data[3:5], "little")

                    if raw <= 0xFAFF:
                        rpms.append(raw * 0.125)

        moving_count = sum(speed >= 5 for speed in speeds)
        stationary_count = sum(speed < 1 for speed in speeds)

        return {
            "source_file": file_path.name,
            "mf4_start_time": mdf.header.start_time.isoformat(),
            "speed_records": len(speeds),
            "speed_min_kmh": round(min(speeds), 2) if speeds else None,
            "speed_mean_kmh": round(np.mean(speeds), 2) if speeds else None,
            "speed_max_kmh": round(max(speeds), 2) if speeds else None,
            "moving_records": moving_count,
            "stationary_records": stationary_count,
            "rpm_records": len(rpms),
            "rpm_min": round(min(rpms), 2) if rpms else None,
            "rpm_mean": round(np.mean(rpms), 2) if rpms else None,
            "rpm_max": round(max(rpms), 2) if rpms else None,
            "usable_moving_file": moving_count > 0,
        }

    finally:
        mdf.close()


files = sorted(INPUT_DIR.rglob("*.MF4"))
results = [inspect_file(file_path) for file_path in files]

summary = pd.DataFrame(results)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT_FILE, index=False)

print(summary.to_string(index=False))
print(f"\nSaved to: {OUTPUT_FILE}")
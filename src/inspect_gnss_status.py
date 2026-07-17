from datetime import timedelta
from pathlib import Path

import pandas as pd
from asammdf import MDF


DATA_DIR = Path("data/raw/VEH_01/SES_20260313_175941")
OUTPUT_PATH = Path("data/processed/gnss_status.csv")

GNSS_STATUS_ID = 0x065

FIX_TYPES = {
    0: "No fix",
    1: "Dead reckoning only",
    2: "2D fix",
    3: "3D fix",
    4: "GNSS + dead reckoning",
    5: "Time only fix",
}


def main() -> None:
    rows = []

    mf4_files = sorted(
        file
        for file in DATA_DIR.iterdir()
        if file.suffix.lower() == ".mf4"
    )

    for file_path in mf4_files:
        mdf = MDF(str(file_path))
        file_start = mdf.header.start_time

        for group_index, channel_index in mdf.channels_db.get(
            "CAN_DataFrame", []
        ):
            signal = mdf.get(
                "CAN_DataFrame",
                group=group_index,
                index=channel_index,
            )

            samples = signal.samples
            mask = samples["CAN_DataFrame.ID"] == GNSS_STATUS_ID

            timestamps = signal.timestamps[mask]
            data_bytes = samples["CAN_DataFrame.DataBytes"][mask]

            for timestamp, byte_values in zip(timestamps, data_bytes):
                raw_value = int(byte_values[0])

                fix_type = raw_value & 0b111
                satellites = (raw_value >> 3) & 0b11111

                rows.append(
                    {
                        "source_file": file_path.name,
                        "timestamp_utc": file_start + timedelta(
                            seconds=float(timestamp)
                        ),
                        "fix_type": fix_type,
                        "fix_description": FIX_TYPES.get(
                            fix_type, "Unknown"
                        ),
                        "satellites": satellites,
                    }
                )

        mdf.close()

    result = pd.DataFrame(rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print("\nGNSS Fix Type:")
    print(result["fix_description"].value_counts())

    print("\nSatellite Summary:")
    print(result["satellites"].describe())

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
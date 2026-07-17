from datetime import timedelta
from pathlib import Path

import pandas as pd
from asammdf import MDF


DATA_DIR = Path("data/raw/VEH_01/SES_20260313_175941")
OUTPUT_PATH = Path(
    "data/processed/gnss_speed_raw_frames.csv"
)

GNSS_SPEED_CAN_ID = 0x06B


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

        locations = mdf.channels_db.get("CAN_DataFrame", [])

        for group_index, channel_index in locations:
            signal = mdf.get(
                "CAN_DataFrame",
                group=group_index,
                index=channel_index,
            )

            samples = signal.samples
            can_ids = samples["CAN_DataFrame.ID"]

            mask = can_ids == GNSS_SPEED_CAN_ID

            if not mask.any():
                continue

            timestamps = signal.timestamps[mask]
            data_bytes = samples["CAN_DataFrame.DataBytes"][mask]

            for timestamp, byte_values in zip(
                timestamps,
                data_bytes,
            ):
                absolute_time = file_start + timedelta(
                    seconds=float(timestamp)
                )

                row = {
                    "source_file": file_path.name,
                    "group_index": group_index,
                    "relative_timestamp": float(timestamp),
                    "timestamp_utc": absolute_time,
                    "can_id": int(GNSS_SPEED_CAN_ID),
                }

                for index in range(5):
                    row[f"byte_{index}"] = int(
                        byte_values[index]
                    )

                rows.append(row)

        mdf.close()

    if not rows:
        print("No CAN ID 107 GnssSpeed frames found.")
        return

    result = pd.DataFrame(rows).sort_values(
        ["timestamp_utc", "source_file"]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print("\nGnssSpeed frame count:")
    print(
        result.groupby(
            ["source_file", "group_index"]
        ).size()
    )

    print("\nSample:")
    print(result.head(10).to_string(index=False))

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
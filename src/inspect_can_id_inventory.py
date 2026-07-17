from pathlib import Path

import numpy as np
import pandas as pd
from asammdf import MDF


DATA_DIR = Path("data/raw/VEH_01/SES_20260313_175941")
OUTPUT_PATH = Path("outputs/reports/can_id_inventory.csv")


def main() -> None:
    rows = []

    mf4_files = sorted(
        file
        for file in DATA_DIR.iterdir()
        if file.suffix.lower() == ".mf4"
    )

    for file_path in mf4_files:
        mdf = MDF(str(file_path))
        locations = mdf.channels_db.get("CAN_DataFrame", [])

        for group_index, channel_index in locations:
            signal = mdf.get(
                "CAN_DataFrame",
                group=group_index,
                index=channel_index,
            )

            can_ids = signal.samples["CAN_DataFrame.ID"]
            unique_ids, counts = np.unique(
                can_ids,
                return_counts=True,
            )

            for can_id, count in zip(unique_ids, counts):
                rows.append(
                    {
                        "source_file": file_path.name,
                        "group_index": group_index,
                        "can_id_decimal": int(can_id),
                        "can_id_hex": f"0x{int(can_id):03X}",
                        "record_count": int(count),
                    }
                )

        mdf.close()

    result = pd.DataFrame(rows).sort_values(
        ["source_file", "group_index", "can_id_decimal"]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(result.to_string(index=False))
    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
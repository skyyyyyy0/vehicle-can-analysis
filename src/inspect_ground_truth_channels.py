from datetime import timedelta
from pathlib import Path

from asammdf import MDF


DATA_DIR = Path("data/raw/VEH_01/SES_20260313_175941")
OUTPUT_PATH = Path(
    "outputs/reports/ground_truth_channel_inventory.txt"
)

KEYWORDS = [
    "speed",
    "velocity",
    "rpm",
    "engine",
    "ignition",
    "gps",
    "latitude",
    "longitude",
    "wheel",
]


def main() -> None:
    mf4_files = sorted(
        file
        for file in DATA_DIR.iterdir()
        if file.suffix.lower() == ".mf4"
    )

    if not mf4_files:
        raise FileNotFoundError(f"No MF4 files found in {DATA_DIR}")

    report_lines = []

    for file_path in mf4_files:
        mdf = MDF(str(file_path))
        start_time = mdf.header.start_time

        report_lines.append(f"\nFILE: {file_path.name}")
        report_lines.append(f"MF4 start time: {start_time}")

        candidate_count = 0

        for channel_name, locations in sorted(mdf.channels_db.items()):
            channel_lower = channel_name.lower()

            if not any(keyword in channel_lower for keyword in KEYWORDS):
                continue

            group_index, channel_index = locations[0]

            try:
                signal = mdf.get(
                    channel_name,
                    group=group_index,
                    index=channel_index,
                )

                timestamps = signal.timestamps
                record_count = len(timestamps)

                if record_count > 0:
                    absolute_start = start_time + timedelta(
                        seconds=float(timestamps[0])
                    )
                    absolute_end = start_time + timedelta(
                        seconds=float(timestamps[-1])
                    )
                else:
                    absolute_start = None
                    absolute_end = None

                report_lines.append(
                    f"- Channel: {channel_name}"
                    f" | Unit: {signal.unit or 'N/A'}"
                    f" | Records: {record_count}"
                    f" | Start: {absolute_start}"
                    f" | End: {absolute_end}"
                )

                candidate_count += 1

            except Exception as error:
                report_lines.append(
                    f"- Could not read {channel_name}: {error}"
                )

        if candidate_count == 0:
            report_lines.append(
                "- No Speed/RPM/Ignition/GPS candidate channels found."
            )

        mdf.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("\n".join(report_lines))
    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
"""
MF4 CAN telemetry parsing and initial signal exploration.

This script:
- Searches for MF4 telemetry files in the data directory
- Extracts CAN_DataFrame from the first available MF4 file
- Converts raw CAN records into a structured DataFrame
- Splits CAN DataBytes into byte_0 through byte_7 columns
- Saves the processed CAN dataset as CSV
- Performs initial CAN ID 111 signal exploration and visualization
"""

from pathlib import Path
from asammdf import MDF
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("data")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def get_mf4_files(data_dir: Path) -> list[Path]:
    """Find all MF4 files in the data directory."""
    return list(data_dir.rglob("*.MF4")) + list(data_dir.rglob("*.mf4"))


def extract_dataframe(file_path: Path) -> pd.DataFrame:
    """Extract CAN_DataFrame and convert it into an analyzable DataFrame."""

    print(f"\nProcessing: {file_path.name}")

    mdf = MDF(str(file_path))
    signal = mdf.get("CAN_DataFrame", group=0, index=1)

    timestamps = signal.timestamps
    samples = signal.samples

    # Build initial CAN telemetry DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "can_id": samples["CAN_DataFrame.ID"],
        "data_bytes": list(samples["CAN_DataFrame.DataBytes"]),
    })

    print("\nDataFrame created successfully.")
    print(df.head())

    # Split raw DataBytes into byte_0 through byte_7 columns
    byte_df = pd.DataFrame(
        df["data_bytes"].tolist(),
        columns=[f"byte_{i}" for i in range(8)]
    )

    # Merge byte columns into the main DataFrame
    df = pd.concat([df.drop(columns=["data_bytes"]), byte_df], axis=1)

    print("\nByte split completed.")
    print(df.head())

    # Save processed CAN telemetry dataset
    output_path = OUTPUT_DIR / "can_data.csv"
    df.to_csv(output_path, index=False)

    print(f"\nData saved to: {output_path}")

    # Filter selected candidate signal for exploratory analysis
    df_111 = df[df["can_id"] == 111].copy()

    # =========================================
    # Stable vs unstable section analysis
    # =========================================

    df_111["byte_4_rolling_std"] = (
        df_111["byte_4"]
        .rolling(window=20)
        .std()
    )

    threshold = df_111["byte_4_rolling_std"].median()

    df_111["signal_state"] = df_111["byte_4_rolling_std"].apply(
        lambda x: "unstable" if x > threshold else "stable"
    )

    # Plot rolling standard deviation for Byte 4
    plt.figure(figsize=(12, 6))
    plt.plot(df_111["timestamp"], df_111["byte_4_rolling_std"])

    plt.axhline(threshold, linestyle="--", label="Stable/Unstable Threshold")

    plt.title("CAN ID 111 - Byte 4 Rolling Standard Deviation")
    plt.xlabel("Timestamp")
    plt.ylabel("Rolling Std of Byte 4")

    plt.grid(True)
    plt.legend()

    plt.savefig(OUTPUT_DIR / "byte_4_rolling_std_analysis.png")

    print("\nVisualization saved: outputs/byte_4_rolling_std_analysis.png")

    plt.show()

    print("\nStable vs unstable sections:")
    print(df_111["signal_state"].value_counts())

    # =========================================
    # Detect spike sections
    # =========================================

    spike_threshold = threshold * 1.03

    spikes = df_111[
        df_111["byte_4_rolling_std"] > spike_threshold
    ]

    print("\nDetected spike sections:")
    print(
        spikes[
            ["timestamp", "byte_4", "byte_4_rolling_std"]
        ].head(20)
    )

    # =========================================
    # Plot Byte 4 over time
    # =========================================

    plt.figure(figsize=(12, 6))

    plt.plot(
        df_111["timestamp"],
        df_111["byte_4"]
    )

    plt.title("CAN ID 111 - Byte 4 over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Byte 4 Value")

    plt.grid(True)

    plt.savefig(
        OUTPUT_DIR / "byte_4_stability_analysis.png"
    )

    print(
        "\nVisualization saved: outputs/byte_4_stability_analysis.png"
    )

    plt.show()

    # =========================================
    # Plot Byte 5 over time
    # =========================================

    plt.figure(figsize=(12, 6))

    plt.plot(
        df_111["timestamp"],
        df_111["byte_5"]
    )

    plt.title("CAN ID 111 - Byte 5 over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Byte 5 Value")

    plt.grid(True)

    plt.savefig(
        OUTPUT_DIR / "byte_5_pattern_analysis.png"
    )

    print(
        "\nVisualization saved: outputs/byte_5_pattern_analysis.png"
    )

    plt.show()

    return df


def main() -> None:
    """Run the MF4 parsing and initial exploration workflow."""

    print(f"Searching in: {DATA_DIR.resolve()}")

    mf4_files = get_mf4_files(DATA_DIR)

    if not mf4_files:
        print("No MF4 files found.")
        return

    first_file = mf4_files[0]

    extract_dataframe(first_file)


if __name__ == "__main__":
    main()
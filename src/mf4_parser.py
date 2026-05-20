from pathlib import Path
from asammdf import MDF
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = Path("data")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def get_mf4_files(data_dir: Path):
    """Find all MF4 files in the data directory."""
    return list(data_dir.rglob("*.MF4")) + list(data_dir.rglob("*.mf4"))


def extract_dataframe(file_path: Path):
    """Extract CAN_DataFrame and convert it into an analyzable DataFrame."""
    
    print(f"\nProcessing: {file_path.name}")

    mdf = MDF(str(file_path))
    signal = mdf.get("CAN_DataFrame", group=0, index=1)

    timestamps = signal.timestamps
    samples = signal.samples

    # Build initial DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "can_id": samples["CAN_DataFrame.ID"],
        "data_bytes": list(samples["CAN_DataFrame.DataBytes"]),
    })

    print("\nDataFrame created successfully.")
    print(df.head())

    # Split data_bytes into byte_0 ~ byte_7
    byte_df = pd.DataFrame(
        df["data_bytes"].tolist(),
        columns=[f"byte_{i}" for i in range(8)]
    )

    # Merge byte columns into main DataFrame
    df = pd.concat([df.drop(columns=["data_bytes"]), byte_df], axis=1)

    print("\nByte split completed.")
    print(df.head())

    # Save CSV
    output_path = OUTPUT_DIR / "can_data.csv"
    df.to_csv(output_path, index=False)

    print(f"\nData saved to: {output_path}")

    # Filter CAN ID 111
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
    # Plot rolling standard deviation for byte_4
    plt.figure(figsize=(12, 6))
    plt.plot(df_111["timestamp"], df_111["byte_4_rolling_std"])

    plt.axhline(threshold, linestyle="--", label="Stable/Unstable Threshold")

    plt.title("CAN ID 111 - byte_4 Rolling Standard Deviation")
    plt.xlabel("Timestamp")
    plt.ylabel("Rolling Std of byte_4")

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
    # Plot byte_4 over time
    # =========================================

    plt.figure(figsize=(12, 6))

    plt.plot(
        df_111["timestamp"],
        df_111["byte_4"]
    )

    plt.title("CAN ID 111 - byte_4 over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("byte_4 Value")

    plt.grid(True)

    plt.savefig(
        OUTPUT_DIR / "byte_4_stability_analysis.png"
    )

    print(
        "\nVisualization saved: outputs/byte_4_stability_analysis.png"
    )

    plt.show()

    # =========================================
    # Plot byte_5 over time
    # =========================================

    plt.figure(figsize=(12, 6))

    plt.plot(
        df_111["timestamp"],
        df_111["byte_5"]
    )

    plt.title("CAN ID 111 - byte_5 over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("byte_5 Value")

    plt.grid(True)

    plt.savefig(
        OUTPUT_DIR / "byte_5_pattern_analysis.png"
    )

    print(
        "\nVisualization saved: outputs/byte_5_pattern_analysis.png"
    )

    plt.show()

    return df


def main():

    print(f"Searching in: {DATA_DIR.resolve()}")

    mf4_files = get_mf4_files(DATA_DIR)

    if not mf4_files:
        print("No MF4 files found.")
        return

    first_file = mf4_files[0]

    extract_dataframe(first_file)


if __name__ == "__main__":
    main()
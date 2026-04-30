from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# =========================================
# Path setup
# =========================================

OUTPUT_DIR = Path("outputs")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"

CSV_PATH = OUTPUT_DIR / "can_data.csv"

OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)


def load_can_data(csv_path: Path) -> pd.DataFrame:
    """Load processed CAN data from CSV."""

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    print("\nCAN data loaded successfully.")
    print(df.head())

    return df


def segment_driving_idle(df: pd.DataFrame) -> pd.DataFrame:
    """Segment CAN ID 111 into driving / idle using byte_4 changes."""

    df_111 = df[df["can_id"] == 111].copy()

    print("\nCAN ID 111 data:")
    print(df_111.head())

    print("\nShape of CAN ID 111 data:")
    print(df_111.shape)

    # Calculate change in byte_4
    df_111["byte_4_diff"] = df_111["byte_4"].diff().abs()

    print("\nCAN ID 111 with byte_4 difference:")
    print(
        df_111[
            ["timestamp", "can_id", "byte_4", "byte_4_diff"]
        ].head(10)
    )

    print("\nbyte_4_diff summary:")
    print(df_111["byte_4_diff"].describe())

    # Heuristic threshold
    threshold = 10

    df_111["driving_state"] = df_111["byte_4_diff"].apply(
        lambda x: "driving" if x > threshold else "idle"
    )

    print("\nDriving vs Idle count:")
    print(df_111["driving_state"].value_counts())

    print("\nSample segmented data:")
    print(
        df_111[
            ["timestamp", "byte_4", "byte_4_diff", "driving_state"]
        ].head(20)
    )

    print("\nStatistics by driving state:")
    print(df_111.groupby("driving_state")["byte_4"].describe())

    return df_111


def plot_driving_idle(df_111: pd.DataFrame) -> None:
    """Save driving vs idle plot into outputs/screenshots."""

    driving_df = df_111[df_111["driving_state"] == "driving"]
    idle_df = df_111[df_111["driving_state"] == "idle"]

    plt.figure(figsize=(14, 6))

    plt.scatter(
        idle_df["timestamp"],
        idle_df["byte_4"],
        label="Idle",
        alpha=0.6
    )

    plt.scatter(
        driving_df["timestamp"],
        driving_df["byte_4"],
        label="Driving",
        alpha=0.6
    )

    plt.title("CAN ID 111 - byte_4 Driving vs Idle Segmentation")
    plt.xlabel("Timestamp")
    plt.ylabel("byte_4 Value")

    plt.grid(True)
    plt.legend()

    output_path = SCREENSHOT_DIR / "driving_vs_idle_segmentation.png"

    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    print(f"\nVisualization saved: {output_path}")

    plt.show()


def save_segmented_data(df_111: pd.DataFrame) -> None:
    """Save segmented CAN ID 111 data into outputs."""

    output_path = OUTPUT_DIR / "can_id_111_driving_segmentation.csv"

    df_111.to_csv(output_path, index=False)

    print(f"\nSegmented data saved: {output_path}")


def main() -> None:
    df = load_can_data(CSV_PATH)

    df_111 = segment_driving_idle(df)

    plot_driving_idle(df_111)

    save_segmented_data(df_111)


if __name__ == "__main__":
    main()
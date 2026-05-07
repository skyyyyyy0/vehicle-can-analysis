from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("outputs")
CSV_PATH = OUTPUT_DIR / "can_data.csv"


def load_can_data(csv_path: Path) -> pd.DataFrame:
    """Load processed CAN data from CSV."""

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    print("\nCAN data loaded successfully.")
    print(df.head())

    return df


def main() -> None:
    df = load_can_data(CSV_PATH)

    df_111 = df[df["can_id"] == 111].copy()

    print("\nCAN ID 111 data:")
    print(df_111.head())

    print("\nShape of CAN ID 111 data:")
    print(df_111.shape)

    # Analyze byte variability
    byte_columns = [f"byte_{i}" for i in range(8)]

    byte_std = df_111[byte_columns].std()

    print("\nByte standard deviation analysis:")
    print(byte_std.sort_values(ascending=False))
    
    # Analyze byte correlation
    correlation_matrix = df_111[byte_columns].corr()

    print("\nByte correlation matrix:")
    print(correlation_matrix)
    

    # Plot and compare byte behavior patterns
    plt.figure(figsize=(14, 6))

    plt.plot(
        df_111["timestamp"],
        df_111["byte_4"],
        label="byte_4",
        alpha=0.8
    )

    plt.plot(
        df_111["timestamp"],
        df_111["byte_5"],
        label="byte_5",
        alpha=0.7
    )

    plt.plot(
        df_111["timestamp"],
        df_111["byte_7"],
        label="byte_7",
        alpha=0.7
    )

    plt.title("CAN ID 111 - Byte Behavior Comparison")
    plt.xlabel("Timestamp")
    plt.ylabel("Byte Value")

    plt.legend()
    plt.grid(True)

    plt.savefig(
        OUTPUT_DIR / "screenshots" / "byte_behavior_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    print(
        "\nVisualization saved: outputs/screenshots/byte_behavior_comparison.png"
    )

    plt.show()


if __name__ == "__main__":
    main()
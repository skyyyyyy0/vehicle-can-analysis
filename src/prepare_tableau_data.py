from pathlib import Path
import pandas as pd


OUTPUT_DIR = Path("outputs")
CSV_PATH = OUTPUT_DIR / "can_data.csv"
TABLEAU_OUTPUT_PATH = OUTPUT_DIR / "tableau_ready_signal.csv"

OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    # Load processed CAN data
    df = pd.read_csv(CSV_PATH)

    # Filter selected CAN signal
    df_111 = df[df["can_id"] == 111].copy()

    # Calculate byte_4 change
    df_111["byte_4_diff"] = df_111["byte_4"].diff().abs()

    # Define driving / idle segmentation
    threshold = 10

    df_111["driving_state"] = df_111["byte_4_diff"].apply(
        lambda x: "driving" if x > threshold else "idle"
    )

    # Select Tableau-ready columns
    tableau_df = df_111[
        [
            "timestamp",
            "can_id",
            "byte_4",
            "byte_5",
            "byte_7",
            "byte_4_diff",
            "driving_state",
        ]
    ].copy()

    # Save Tableau-ready CSV
    tableau_df.to_csv(TABLEAU_OUTPUT_PATH, index=False)

    print("\nTableau-ready CSV created successfully.")
    print(f"Saved to: {TABLEAU_OUTPUT_PATH}")
    print("\nPreview:")
    print(tableau_df.head())


if __name__ == "__main__":
    main()
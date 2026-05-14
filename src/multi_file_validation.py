from pathlib import Path
from asammdf import MDF
import pandas as pd

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

VALIDATION_OUTPUT = OUTPUT_DIR / "multi_file_can_id_111.csv"
VALIDATION_SUMMARY_OUTPUT = OUTPUT_DIR / "multi_file_validation_summary.csv"


def get_mf4_files(data_dir: Path):
    return list(data_dir.rglob("*.MF4")) + list(data_dir.rglob("*.mf4"))


def extract_can_id_111(file_path: Path) -> pd.DataFrame:
    print(f"\nProcessing: {file_path.name}")

    mdf = MDF(str(file_path))
    signal = mdf.get("CAN_DataFrame", group=0, index=1)

    df = pd.DataFrame({
        "timestamp": signal.timestamps,
        "can_id": signal.samples["CAN_DataFrame.ID"],
        "data_bytes": list(signal.samples["CAN_DataFrame.DataBytes"]),
    })

    byte_df = pd.DataFrame(
        df["data_bytes"].tolist(),
        columns=[f"byte_{i}" for i in range(8)]
    )

    df = pd.concat([df.drop(columns=["data_bytes"]), byte_df], axis=1)

    df_111 = df[df["can_id"] == 111].copy()
    df_111["file_name"] = file_path.name

    print(f"CAN ID 111 rows: {len(df_111)}")

    return df_111


def classify_session(dynamic_ratio: float) -> str:
    if dynamic_ratio < 0.05:
        return "stable"
    elif dynamic_ratio < 0.25:
        return "mixed"
    else:
        return "dynamic"


def main():
    mf4_files = get_mf4_files(DATA_DIR)

    validation_files = [
        file for file in mf4_files
        if file.name.lower() != "sample.mf4"
    ]

    print(f"Total MF4 files found: {len(mf4_files)}")
    print(f"Validation MF4 files: {len(validation_files)}")

    all_data = []

    for file_path in validation_files:
        try:
            df_111 = extract_can_id_111(file_path)
            all_data.append(df_111)
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

    if not all_data:
        print("No CAN ID 111 data extracted.")
        return

    validation_df = pd.concat(all_data, ignore_index=True)

    validation_df = validation_df.sort_values(
        by=["file_name", "timestamp"]
    ).copy()

    validation_df["byte_4_diff"] = (
        validation_df
        .groupby("file_name")["byte_4"]
        .diff()
        .abs()
    )
    validation_df["byte_4_diff"] = validation_df["byte_4_diff"].fillna(0)

    DRIVING_THRESHOLD = 20

    validation_df["driving_state"] = (
        validation_df["byte_4_diff"] > DRIVING_THRESHOLD
    ).map({
        True: "driving",
        False: "idle"
    })

    validation_df["dynamic_pattern"] = (
        validation_df["byte_4_diff"] > DRIVING_THRESHOLD
    )

    # Summary 1: Driving / idle
    state_summary = (
        validation_df
        .groupby(["file_name", "driving_state"])
        .size()
        .unstack(fill_value=0)
    )

    if "driving" not in state_summary.columns:
        state_summary["driving"] = 0

    if "idle" not in state_summary.columns:
        state_summary["idle"] = 0

    state_summary["total"] = state_summary["driving"] + state_summary["idle"]
    state_summary["driving_ratio"] = state_summary["driving"] / state_summary["total"]
    state_summary["idle_ratio"] = state_summary["idle"] / state_summary["total"]

    # Summary 2: byte_4 transition stats
    transition_summary = (
        validation_df
        .groupby("file_name")["byte_4_diff"]
        .agg(
            byte_4_diff_mean="mean",
            byte_4_diff_median="median",
            byte_4_diff_max="max"
        )
    )

    # Summary 3: dynamic pattern
    dynamic_summary = (
        validation_df
        .groupby("file_name")["dynamic_pattern"]
        .agg(
            dynamic_transition_count="sum",
            total_records="count"
        )
    )

    dynamic_summary["dynamic_transition_ratio"] = (
        dynamic_summary["dynamic_transition_count"] /
        dynamic_summary["total_records"]
    )

    # Summary 4: byte variability
    byte_columns = [f"byte_{i}" for i in range(8)]

    variability_stats = (
        validation_df
        .groupby("file_name")[byte_columns]
        .std()
    )

    variability_stats = variability_stats.add_suffix("_std")

    # Final validation summary
    validation_summary = (
        state_summary
        .join(transition_summary)
        .join(dynamic_summary[["dynamic_transition_count", "dynamic_transition_ratio"]])
        .join(variability_stats)
    )

    validation_summary["session_behavior"] = (
        validation_summary["dynamic_transition_ratio"]
        .apply(classify_session)
    )

    print("\nMulti-file validation summary:")
    print(validation_summary)

    validation_df.to_csv(VALIDATION_OUTPUT, index=False)
    validation_summary.to_csv(VALIDATION_SUMMARY_OUTPUT)

    print("\nMulti-file CAN ID 111 dataset created.")
    print(f"Saved to: {VALIDATION_OUTPUT}")

    print("\nValidation summary created.")
    print(f"Saved to: {VALIDATION_SUMMARY_OUTPUT}")

    print("\nSession behavior counts:")
    print(validation_summary["session_behavior"].value_counts())


if __name__ == "__main__":
    main()
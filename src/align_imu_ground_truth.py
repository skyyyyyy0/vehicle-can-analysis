from pathlib import Path

import numpy as np
import pandas as pd


IMU_INPUT = Path(
    "data/processed/imu_signals_processed.csv"
)
GROUND_TRUTH_INPUT = Path(
    "data/processed/ground_truth_processed.csv"
)

IMU_1S_OUTPUT = Path(
    "data/processed/imu_features_1s.csv"
)
ALIGNED_OUTPUT = Path(
    "data/processed/aligned_imu_ground_truth.csv"
)
SUMMARY_OUTPUT = Path(
    "outputs/validation/imu_timestamp_alignment_summary.csv"
)

GRAVITY = 9.80665


def population_std(values):
    return values.std(ddof=0)


def root_mean_square(values):
    values = values.dropna()

    if values.empty:
        return np.nan

    return np.sqrt(np.mean(np.square(values)))


# --------------------------------------------------
# 1. IMU 데이터 로드
# --------------------------------------------------

imu = pd.read_csv(IMU_INPUT)

imu["timestamp"] = pd.to_datetime(
    imu["timestamp"],
    utc=True,
)

imu["timestamp_1s"] = (
    imu["timestamp"].dt.floor("s")
)

imu["acceleration_deviation"] = (
    imu["acceleration_magnitude"] - GRAVITY
).abs()

imu = imu.sort_values(
    [
        "vehicle_id",
        "session_id",
        "source_file",
        "timestamp",
    ]
)

join_keys = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
]


# --------------------------------------------------
# 2. IMU 신호 1초 집계
# --------------------------------------------------

imu_1s = (
    imu
    .groupby(join_keys, as_index=False)
    .agg(
        imu_record_count=("imu_valid", "size"),
        imu_valid_count=("imu_valid", "sum"),
        imu_valid_ratio=("imu_valid", "mean"),

        acceleration_magnitude_mean=(
            "acceleration_magnitude",
            "mean",
        ),
        acceleration_magnitude_std=(
            "acceleration_magnitude",
            population_std,
        ),
        acceleration_magnitude_max=(
            "acceleration_magnitude",
            "max",
        ),

        acceleration_deviation_mean=(
            "acceleration_deviation",
            "mean",
        ),
        acceleration_deviation_std=(
            "acceleration_deviation",
            population_std,
        ),
        acceleration_deviation_max=(
            "acceleration_deviation",
            "max",
        ),

        angular_rate_magnitude_mean=(
            "angular_rate_magnitude",
            "mean",
        ),
        angular_rate_magnitude_std=(
            "angular_rate_magnitude",
            population_std,
        ),
        angular_rate_magnitude_max=(
            "angular_rate_magnitude",
            "max",
        ),
        angular_rate_magnitude_rms=(
            "angular_rate_magnitude",
            root_mean_square,
        ),
    )
)

if imu_1s.duplicated(join_keys).any():
    raise ValueError(
        "Duplicate IMU 1-second keys detected."
    )

IMU_1S_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
imu_1s.to_csv(IMU_1S_OUTPUT, index=False)


# --------------------------------------------------
# 3. Ground Truth 준비
# --------------------------------------------------

ground_truth = pd.read_csv(GROUND_TRUTH_INPUT)

ground_truth["timestamp_1s"] = pd.to_datetime(
    ground_truth["timestamp_1s"],
    utc=True,
)

ground_truth = ground_truth.rename(
    columns={
        "ground_truth_state": "true_state",
    }
)

ground_truth["ground_truth_record_count"] = (
    ground_truth["speed_record_count"]
    + ground_truth["rpm_record_count"]
)

if ground_truth.duplicated(join_keys).any():
    raise ValueError(
        "Duplicate Ground-Truth keys detected."
    )


# --------------------------------------------------
# 4. Outer Join으로 결합 상태 검사
# --------------------------------------------------

alignment_check = imu_1s.merge(
    ground_truth,
    on=join_keys,
    how="outer",
    indicator=True,
)


# --------------------------------------------------
# 5. 파일별 Match Coverage
# --------------------------------------------------

summary_rows = []

group_columns = [
    "vehicle_id",
    "session_id",
    "source_file",
]

for group_values, group_df in alignment_check.groupby(
    group_columns,
    observed=True,
):
    vehicle_id, session_id, source_file = group_values

    imu_windows = int(
        (group_df["_merge"] != "right_only").sum()
    )
    ground_truth_windows = int(
        (group_df["_merge"] != "left_only").sum()
    )
    matched_windows = int(
        (group_df["_merge"] == "both").sum()
    )
    unmatched_imu_windows = int(
        (group_df["_merge"] == "left_only").sum()
    )
    unmatched_ground_truth_windows = int(
        (group_df["_merge"] == "right_only").sum()
    )

    coverage = (
        matched_windows / imu_windows * 100
        if imu_windows > 0
        else 0
    )

    summary_rows.append({
        "vehicle_id": vehicle_id,
        "session_id": session_id,
        "source_file": source_file,
        "imu_windows": imu_windows,
        "ground_truth_windows": ground_truth_windows,
        "matched_windows": matched_windows,
        "unmatched_imu_windows": unmatched_imu_windows,
        "unmatched_ground_truth_windows":
            unmatched_ground_truth_windows,
        "match_coverage_pct": round(coverage, 2),
    })


summary = pd.DataFrame(summary_rows)

total_imu = len(imu_1s)
total_ground_truth = len(ground_truth)
total_matched = int(
    (alignment_check["_merge"] == "both").sum()
)
total_unmatched_imu = int(
    (alignment_check["_merge"] == "left_only").sum()
)
total_unmatched_ground_truth = int(
    (alignment_check["_merge"] == "right_only").sum()
)

overall_coverage = (
    total_matched / total_imu * 100
    if total_imu > 0
    else 0
)

overall_row = pd.DataFrame([{
    "vehicle_id": "ALL",
    "session_id": "ALL",
    "source_file": "ALL_FILES",
    "imu_windows": total_imu,
    "ground_truth_windows": total_ground_truth,
    "matched_windows": total_matched,
    "unmatched_imu_windows": total_unmatched_imu,
    "unmatched_ground_truth_windows":
        total_unmatched_ground_truth,
    "match_coverage_pct": round(overall_coverage, 2),
}])

summary = pd.concat(
    [summary, overall_row],
    ignore_index=True,
)


# --------------------------------------------------
# 6. 분석용 Inner Join 데이터 생성
# --------------------------------------------------

aligned = alignment_check.loc[
    alignment_check["_merge"] == "both"
].drop(columns="_merge")

aligned = aligned.sort_values(
    join_keys
).reset_index(drop=True)

if aligned.duplicated(join_keys).any():
    raise ValueError(
        "Duplicate aligned IMU keys detected."
    )


# --------------------------------------------------
# 7. 결과 저장
# --------------------------------------------------

ALIGNED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

aligned.to_csv(ALIGNED_OUTPUT, index=False)
summary.to_csv(SUMMARY_OUTPUT, index=False)


# --------------------------------------------------
# 8. 결과 출력
# --------------------------------------------------

print("\nIMU Timestamp alignment summary:")
print(summary.to_string(index=False))

print("\nGround-Truth label distribution:")
print(
    aligned["true_state"]
    .value_counts(dropna=False)
)

print("\nIMU feature summary by state:")
print(
    aligned
    .groupby("true_state")
    .agg(
        window_count=("timestamp_1s", "size"),
        angular_mean=(
            "angular_rate_magnitude_mean",
            "mean",
        ),
        angular_std=(
            "angular_rate_magnitude_std",
            "mean",
        ),
        angular_max=(
            "angular_rate_magnitude_max",
            "mean",
        ),
        acceleration_deviation_mean=(
            "acceleration_deviation_mean",
            "mean",
        ),
        acceleration_deviation_max=(
            "acceleration_deviation_max",
            "mean",
        ),
    )
    .round(4)
    .to_string()
)

print("\nQuality checks:")
print(
    "IMU duplicate keys:",
    imu_1s.duplicated(join_keys).sum(),
)
print(
    "Ground-Truth duplicate keys:",
    ground_truth.duplicated(join_keys).sum(),
)
print(
    "Aligned duplicate keys:",
    aligned.duplicated(join_keys).sum(),
)
print("Final aligned rows:", len(aligned))

print(f"\nSaved to: {IMU_1S_OUTPUT}")
print(f"Saved to: {ALIGNED_OUTPUT}")
print(f"Saved to: {SUMMARY_OUTPUT}")
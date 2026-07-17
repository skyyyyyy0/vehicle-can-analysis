from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/aligned_imu_ground_truth.csv"
)

BINARY_OUTPUT = Path(
    "data/processed/imu_binary_analysis.csv"
)

SUMMARY_OUTPUT = Path(
    "outputs/validation/analysis_dataset_summary.csv"
)

FILE_DISTRIBUTION_OUTPUT = Path(
    "outputs/validation/file_class_distribution.csv"
)

BLOCK_DISTRIBUTION_OUTPUT = Path(
    "outputs/validation/time_block_class_distribution.csv"
)


PRIMARY_FILE = "00007171-69EA7231.MF4"
IDLE_STRESS_FILE = "00007172-69EA7237.MF4"
TRANSITION_FILE = "00007173-69EA723B.MF4"


# --------------------------------------------------
# 1. 데이터 로드
# --------------------------------------------------

aligned = pd.read_csv(INPUT_FILE)

aligned["timestamp_1s"] = pd.to_datetime(
    aligned["timestamp_1s"],
    utc=True,
)


# --------------------------------------------------
# 2. Moving과 Idle만 선택
# --------------------------------------------------

analysis = aligned.loc[
    aligned["true_state"].isin(
        ["moving", "idle"]
    )
].copy()

analysis["y_true"] = (
    analysis["true_state"] == "moving"
).astype(int)


# --------------------------------------------------
# 3. 파일별 분석 역할 지정
# --------------------------------------------------

analysis["dataset_role"] = np.select(
    [
        analysis["source_file"] == PRIMARY_FILE,
        analysis["source_file"] == IDLE_STRESS_FILE,
        analysis["source_file"] == TRANSITION_FILE,
    ],
    [
        "within_session_candidate",
        "idle_stress_test",
        "transition_diagnostic",
    ],
    default="excluded",
)


# --------------------------------------------------
# 4. 필수 Feature 검사
# --------------------------------------------------

required_features = [
    "angular_rate_magnitude_mean",
    "angular_rate_magnitude_std",
    "angular_rate_magnitude_max",
    "angular_rate_magnitude_rms",
    "acceleration_deviation_mean",
    "acceleration_deviation_max",
]

missing_count = int(
    analysis[required_features]
    .isna()
    .sum()
    .sum()
)

if missing_count > 0:
    raise ValueError(
        f"Missing IMU feature values: {missing_count}"
    )


# --------------------------------------------------
# 5. Timestamp 순서 및 10초 Block 생성
# --------------------------------------------------

analysis = analysis.sort_values(
    [
        "vehicle_id",
        "session_id",
        "source_file",
        "timestamp_1s",
    ]
).reset_index(drop=True)

analysis["time_block_10s"] = (
    analysis["timestamp_1s"].dt.floor("10s")
)


# --------------------------------------------------
# 6. Binary 데이터 저장
# --------------------------------------------------

BINARY_OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

analysis.to_csv(
    BINARY_OUTPUT,
    index=False,
)


# --------------------------------------------------
# 7. 전체 요약
# --------------------------------------------------

moving_count = int(
    (analysis["true_state"] == "moving").sum()
)
idle_count = int(
    (analysis["true_state"] == "idle").sum()
)
total_count = len(analysis)

summary = pd.DataFrame([{
    "dataset_name": "imu_binary_analysis",
    "total_windows": total_count,
    "moving_windows": moving_count,
    "idle_windows": idle_count,
    "moving_ratio_pct": round(
        moving_count / total_count * 100,
        2,
    ),
    "idle_ratio_pct": round(
        idle_count / total_count * 100,
        2,
    ),
    "vehicle_count":
        analysis["vehicle_id"].nunique(),
    "session_count":
        analysis["session_id"].nunique(),
    "source_file_count":
        analysis["source_file"].nunique(),
    "duplicate_key_count": int(
        analysis.duplicated(
            [
                "vehicle_id",
                "session_id",
                "source_file",
                "timestamp_1s",
            ]
        ).sum()
    ),
    "missing_feature_count": missing_count,
}])

SUMMARY_OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

summary.to_csv(
    SUMMARY_OUTPUT,
    index=False,
)


# --------------------------------------------------
# 8. 파일별 클래스 분포
# --------------------------------------------------

file_distribution = (
    analysis
    .groupby(
        ["source_file", "dataset_role"],
        as_index=False,
    )
    .agg(
        total_windows=("timestamp_1s", "size"),
        moving_windows=(
            "y_true",
            lambda values: int(
                (values == 1).sum()
            ),
        ),
        idle_windows=(
            "y_true",
            lambda values: int(
                (values == 0).sum()
            ),
        ),
        feature_min=(
            "angular_rate_magnitude_mean",
            "min",
        ),
        feature_median=(
            "angular_rate_magnitude_mean",
            "median",
        ),
        feature_mean=(
            "angular_rate_magnitude_mean",
            "mean",
        ),
        feature_max=(
            "angular_rate_magnitude_mean",
            "max",
        ),
    )
)

file_distribution.to_csv(
    FILE_DISTRIBUTION_OUTPUT,
    index=False,
)


# --------------------------------------------------
# 9. Primary File의 10초 Block 분포
# --------------------------------------------------

primary_data = analysis.loc[
    analysis["source_file"] == PRIMARY_FILE
].copy()

block_distribution = (
    primary_data
    .groupby("time_block_10s")
    .agg(
        total_windows=("timestamp_1s", "size"),
        moving_windows=(
            "y_true",
            lambda values: int(
                (values == 1).sum()
            ),
        ),
        idle_windows=(
            "y_true",
            lambda values: int(
                (values == 0).sum()
            ),
        ),
        feature_min=(
            "angular_rate_magnitude_mean",
            "min",
        ),
        feature_median=(
            "angular_rate_magnitude_mean",
            "median",
        ),
        feature_mean=(
            "angular_rate_magnitude_mean",
            "mean",
        ),
        feature_max=(
            "angular_rate_magnitude_mean",
            "max",
        ),
    )
    .reset_index()
)

block_distribution["contains_both_classes"] = (
    (block_distribution["moving_windows"] > 0)
    & (block_distribution["idle_windows"] > 0)
)

block_distribution.to_csv(
    BLOCK_DISTRIBUTION_OUTPUT,
    index=False,
)


# --------------------------------------------------
# 10. 결과 출력
# --------------------------------------------------

print("\nAnalysis dataset summary:")
print(summary.to_string(index=False))

print("\nFile class distribution:")
print(
    file_distribution
    .round(4)
    .to_string(index=False)
)

print("\nPrimary-file 10-second blocks:")
print(
    block_distribution
    .round(4)
    .to_string(index=False)
)

print(f"\nSaved to: {BINARY_OUTPUT}")
print(f"Saved to: {SUMMARY_OUTPUT}")
print(f"Saved to: {FILE_DISTRIBUTION_OUTPUT}")
print(f"Saved to: {BLOCK_DISTRIBUTION_OUTPUT}")
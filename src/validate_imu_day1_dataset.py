from pathlib import Path

import pandas as pd


IMU_RAW_PATH = Path(
    "data/processed/imu_signals_processed.csv"
)
IMU_1S_PATH = Path(
    "data/processed/imu_features_1s.csv"
)
GROUND_TRUTH_PATH = Path(
    "data/processed/ground_truth_processed.csv"
)
ALIGNED_PATH = Path(
    "data/processed/aligned_imu_ground_truth.csv"
)
ALIGNMENT_SUMMARY_PATH = Path(
    "outputs/validation/imu_timestamp_alignment_summary.csv"
)

QUALITY_OUTPUT = Path(
    "outputs/validation/day1_imu_quality_checks.csv"
)
STATE_SUMMARY_OUTPUT = Path(
    "outputs/validation/imu_feature_state_summary.csv"
)


imu_raw = pd.read_csv(IMU_RAW_PATH)
imu_1s = pd.read_csv(IMU_1S_PATH)
ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
aligned = pd.read_csv(ALIGNED_PATH)
alignment_summary = pd.read_csv(
    ALIGNMENT_SUMMARY_PATH
)


# Timestamp를 UTC datetime으로 변환
imu_raw["timestamp"] = pd.to_datetime(
    imu_raw["timestamp"],
    utc=True,
)
imu_1s["timestamp_1s"] = pd.to_datetime(
    imu_1s["timestamp_1s"],
    utc=True,
)
ground_truth["timestamp_1s"] = pd.to_datetime(
    ground_truth["timestamp_1s"],
    utc=True,
)
aligned["timestamp_1s"] = pd.to_datetime(
    aligned["timestamp_1s"],
    utc=True,
)


join_keys = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
]

checks = []


def add_check(
    check_name,
    passed,
    observed,
    expected,
):
    checks.append({
        "check_name": check_name,
        "status": "PASS" if passed else "FAIL",
        "observed": str(observed),
        "expected": str(expected),
    })


# --------------------------------------------------
# 1. IMU Valid 검사
# --------------------------------------------------

valid_values = set(
    imu_raw["imu_valid"].dropna().unique()
)

add_check(
    "IMU Valid values",
    valid_values.issubset({0, 1}),
    sorted(valid_values),
    "0 or 1",
)

valid_ratio = imu_raw["imu_valid"].mean()

add_check(
    "IMU Valid ratio",
    valid_ratio >= 0.95,
    f"{valid_ratio * 100:.2f}%",
    "At least 95%",
)


# --------------------------------------------------
# 2. 공식 물리 범위 검사
# --------------------------------------------------

valid_imu = imu_raw.loc[
    imu_raw["imu_valid"] == 1
]

acceleration_columns = [
    "acceleration_x",
    "acceleration_y",
    "acceleration_z",
]

angular_rate_columns = [
    "angular_rate_x",
    "angular_rate_y",
    "angular_rate_z",
]

acceleration_invalid = int(
    (
        ~valid_imu[acceleration_columns]
        .apply(lambda column: column.between(-64, 63.875))
    ).sum().sum()
)

add_check(
    "Acceleration physical range",
    acceleration_invalid == 0,
    acceleration_invalid,
    "0 values outside -64 to 63.875 m/s²",
)

angular_rate_invalid = int(
    (
        ~valid_imu[angular_rate_columns]
        .apply(lambda column: column.between(-256, 255.75))
    ).sum().sum()
)

add_check(
    "Angular-rate physical range",
    angular_rate_invalid == 0,
    angular_rate_invalid,
    "0 values outside -256 to 255.75 deg/s",
)


# --------------------------------------------------
# 3. Magnitude 검사
# --------------------------------------------------

negative_acceleration_magnitude = int(
    (valid_imu["acceleration_magnitude"] < 0).sum()
)

negative_angular_magnitude = int(
    (valid_imu["angular_rate_magnitude"] < 0).sum()
)

add_check(
    "Acceleration magnitude validity",
    negative_acceleration_magnitude == 0,
    negative_acceleration_magnitude,
    0,
)

add_check(
    "Angular-rate magnitude validity",
    negative_angular_magnitude == 0,
    negative_angular_magnitude,
    0,
)


# --------------------------------------------------
# 4. 중복 Key 검사
# --------------------------------------------------

imu_duplicate_count = int(
    imu_1s.duplicated(join_keys).sum()
)

ground_truth_duplicate_count = int(
    ground_truth.duplicated(join_keys).sum()
)

aligned_duplicate_count = int(
    aligned.duplicated(join_keys).sum()
)

add_check(
    "IMU 1-second duplicate keys",
    imu_duplicate_count == 0,
    imu_duplicate_count,
    0,
)

add_check(
    "Ground-Truth duplicate keys",
    ground_truth_duplicate_count == 0,
    ground_truth_duplicate_count,
    0,
)

add_check(
    "Aligned duplicate keys",
    aligned_duplicate_count == 0,
    aligned_duplicate_count,
    0,
)


# --------------------------------------------------
# 5. 필수 컬럼 결측 검사
# --------------------------------------------------

required_columns = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
    "imu_record_count",
    "imu_valid_ratio",
    "acceleration_magnitude_mean",
    "acceleration_magnitude_std",
    "acceleration_deviation_mean",
    "acceleration_deviation_max",
    "angular_rate_magnitude_mean",
    "angular_rate_magnitude_std",
    "angular_rate_magnitude_max",
    "vehicle_speed_kmh",
    "engine_rpm",
    "true_state",
]

missing_count = int(
    aligned[required_columns]
    .isna()
    .sum()
    .sum()
)

add_check(
    "Required-column missing values",
    missing_count == 0,
    missing_count,
    0,
)


# --------------------------------------------------
# 6. Ground Truth 범위 검사
# --------------------------------------------------

invalid_speed = int(
    (
        (aligned["vehicle_speed_kmh"] < 0)
        | (aligned["vehicle_speed_kmh"] > 251)
    ).sum()
)

invalid_rpm = int(
    (
        (aligned["engine_rpm"] < 0)
        | (aligned["engine_rpm"] > 8032)
    ).sum()
)

add_check(
    "Vehicle Speed validity",
    invalid_speed == 0,
    invalid_speed,
    0,
)

add_check(
    "Engine RPM validity",
    invalid_rpm == 0,
    invalid_rpm,
    0,
)


# --------------------------------------------------
# 7. 상태 라벨 검사
# --------------------------------------------------

states = set(
    aligned["true_state"].dropna().unique()
)

add_check(
    "Moving and Idle availability",
    {"moving", "idle"}.issubset(states),
    sorted(states),
    "moving and idle",
)


# --------------------------------------------------
# 8. Timestamp Match 검사
# --------------------------------------------------

overall_alignment = alignment_summary.loc[
    alignment_summary["source_file"] == "ALL_FILES"
].iloc[0]

unmatched_ground_truth = int(
    overall_alignment[
        "unmatched_ground_truth_windows"
    ]
)

add_check(
    "Ground-Truth matching",
    unmatched_ground_truth == 0,
    unmatched_ground_truth,
    0,
)


# --------------------------------------------------
# 9. 최종 행 개수 검사
# --------------------------------------------------

add_check(
    "Final aligned row count",
    len(aligned) == len(ground_truth),
    len(aligned),
    len(ground_truth),
)


# --------------------------------------------------
# 10. 상태별 IMU Feature 요약
# --------------------------------------------------

state_summary = (
    aligned
    .groupby("true_state", as_index=False)
    .agg(
        window_count=("timestamp_1s", "size"),
        angular_rate_mean=(
            "angular_rate_magnitude_mean",
            "mean",
        ),
        angular_rate_std_mean=(
            "angular_rate_magnitude_std",
            "mean",
        ),
        angular_rate_max_mean=(
            "angular_rate_magnitude_max",
            "mean",
        ),
        acceleration_deviation_mean=(
            "acceleration_deviation_mean",
            "mean",
        ),
        acceleration_deviation_max_mean=(
            "acceleration_deviation_max",
            "mean",
        ),
    )
)

state_summary.to_csv(
    STATE_SUMMARY_OUTPUT,
    index=False,
)


# --------------------------------------------------
# 11. 결과 저장 및 출력
# --------------------------------------------------

quality_results = pd.DataFrame(checks)

QUALITY_OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

quality_results.to_csv(
    QUALITY_OUTPUT,
    index=False,
)

print("\nDay 1 IMU quality checks:")
print(quality_results.to_string(index=False))

print("\nDataset scope:")
print("Session count:", aligned["session_id"].nunique())
print("Source file count:", aligned["source_file"].nunique())
print("Final aligned rows:", len(aligned))
print(
    "Overall match coverage:",
    f"{overall_alignment['match_coverage_pct']:.2f}%",
)

print("\nLabel distribution:")
print(aligned["true_state"].value_counts())

print("\nIMU feature summary by state:")
print(
    state_summary
    .round(4)
    .to_string(index=False)
)

print(f"\nSaved to: {QUALITY_OUTPUT}")
print(f"Saved to: {STATE_SUMMARY_OUTPUT}")
from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/imu_binary_analysis.csv"
)

SPLIT_DATA_OUTPUT = Path(
    "data/processed/imu_binary_split_dataset.csv"
)

ASSIGNMENT_OUTPUT = Path(
    "outputs/validation/validation_split_assignments.csv"
)

SUMMARY_OUTPUT = Path(
    "outputs/validation/validation_split_summary.csv"
)


PRIMARY_FILE = "00007171-69EA7231.MF4"
IDLE_STRESS_FILE = "00007172-69EA7237.MF4"
TRANSITION_FILE = "00007173-69EA723B.MF4"

DEVELOPMENT_RATIO = 0.70


# --------------------------------------------------
# 1. 데이터 로드
# --------------------------------------------------

analysis = pd.read_csv(INPUT_FILE)

analysis["timestamp_1s"] = pd.to_datetime(
    analysis["timestamp_1s"],
    utc=True,
)

analysis = analysis.sort_values(
    [
        "vehicle_id",
        "session_id",
        "source_file",
        "timestamp_1s",
    ]
).reset_index(drop=True)


# --------------------------------------------------
# 2. Primary File 시간순 분할
# --------------------------------------------------

primary = analysis.loc[
    analysis["source_file"] == PRIMARY_FILE
].copy()

primary = primary.sort_values(
    "timestamp_1s"
).reset_index(drop=True)

split_index = int(
    len(primary) * DEVELOPMENT_RATIO
)

if split_index <= 0 or split_index >= len(primary):
    raise ValueError(
        "Invalid chronological split index."
    )

primary["chronological_index"] = range(
    len(primary)
)

primary["split_role"] = "development"

primary.loc[
    primary.index >= split_index,
    "split_role",
] = "within_session_validation"

validation_start_timestamp = primary.loc[
    primary.index == split_index,
    "timestamp_1s",
].iloc[0]


# --------------------------------------------------
# 3. Idle Stress Test
# --------------------------------------------------

idle_stress = analysis.loc[
    analysis["source_file"] == IDLE_STRESS_FILE
].copy()

idle_stress["chronological_index"] = range(
    len(idle_stress)
)

idle_stress["split_role"] = "idle_stress_test"


# --------------------------------------------------
# 4. Transition Diagnostic
# --------------------------------------------------

transition = analysis.loc[
    analysis["source_file"] == TRANSITION_FILE
].copy()

transition["chronological_index"] = range(
    len(transition)
)

transition["split_role"] = "transition_diagnostic"


# --------------------------------------------------
# 5. 데이터 결합
# --------------------------------------------------

split_data = pd.concat(
    [
        primary,
        idle_stress,
        transition,
    ],
    ignore_index=True,
)

split_data = split_data.sort_values(
    [
        "source_file",
        "timestamp_1s",
    ]
).reset_index(drop=True)


# --------------------------------------------------
# 6. 분할 품질검사
# --------------------------------------------------

development = split_data.loc[
    split_data["split_role"] == "development"
]

validation = split_data.loc[
    split_data["split_role"]
    == "within_session_validation"
]

development_classes = set(
    development["true_state"].unique()
)

validation_classes = set(
    validation["true_state"].unique()
)

if development_classes != {"moving", "idle"}:
    raise ValueError(
        "Development block does not contain both classes."
    )

if validation_classes != {"moving", "idle"}:
    raise ValueError(
        "Validation block does not contain both classes."
    )

key_columns = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
]

duplicate_count = int(
    split_data.duplicated(key_columns).sum()
)

if duplicate_count > 0:
    raise ValueError(
        f"Duplicate split keys detected: {duplicate_count}"
    )


# --------------------------------------------------
# 7. 분할 요약
# --------------------------------------------------

summary = (
    split_data
    .groupby("split_role", as_index=False)
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
        first_timestamp=("timestamp_1s", "min"),
        last_timestamp=("timestamp_1s", "max"),
    )
)

summary["moving_ratio_pct"] = (
    summary["moving_windows"]
    / summary["total_windows"]
    * 100
).round(2)

summary["idle_ratio_pct"] = (
    summary["idle_windows"]
    / summary["total_windows"]
    * 100
).round(2)


# --------------------------------------------------
# 8. 결과 저장
# --------------------------------------------------

SPLIT_DATA_OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

ASSIGNMENT_OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

split_data.to_csv(
    SPLIT_DATA_OUTPUT,
    index=False,
)

assignment_columns = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
    "true_state",
    "y_true",
    "split_role",
    "chronological_index",
]

split_data[assignment_columns].to_csv(
    ASSIGNMENT_OUTPUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUTPUT,
    index=False,
)


# --------------------------------------------------
# 9. 결과 출력
# --------------------------------------------------

print("\nChronological split information:")
print("Primary rows:", len(primary))
print("Development rows:", len(development))
print("Validation rows:", len(validation))
print(
    "Validation start:",
    validation_start_timestamp,
)

print("\nSplit summary:")
print(
    summary
    .round(4)
    .to_string(index=False)
)

print("\nDevelopment state distribution:")
print(development["true_state"].value_counts())

print("\nValidation state distribution:")
print(validation["true_state"].value_counts())

print(f"\nSaved to: {SPLIT_DATA_OUTPUT}")
print(f"Saved to: {ASSIGNMENT_OUTPUT}")
print(f"Saved to: {SUMMARY_OUTPUT}")
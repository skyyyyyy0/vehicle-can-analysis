from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DATA_PATH = Path(
    "data/processed/imu_binary_split_dataset.csv"
)
THRESHOLD_PATH = Path(
    "outputs/validation/selected_threshold.json"
)

VALIDATION_DIR = Path("outputs/validation")
FIGURE_DIR = Path("outputs/figures")


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

with open(
    THRESHOLD_PATH,
    "r",
    encoding="utf-8",
) as file:
    threshold_info = json.load(file)

feature = threshold_info["feature"]
selected_threshold = float(
    threshold_info["selected_threshold"]
)

if not threshold_info.get(
    "threshold_frozen_before_validation",
    False,
):
    raise ValueError(
        "Threshold was not frozen before validation."
    )

stress_test = df[
    df["split_role"] == "idle_stress_test"
].copy()

if stress_test.empty:
    raise ValueError(
        "No idle stress-test data found."
    )

if not (stress_test["true_state"] == "idle").all():
    raise ValueError(
        "Idle stress test contains non-idle labels."
    )

stress_test["timestamp_1s"] = pd.to_datetime(
    stress_test["timestamp_1s"],
    utc=True,
)

stress_test = stress_test.sort_values(
    ["source_file", "timestamp_1s"]
).reset_index(drop=True)

stress_test["y_true"] = 0

stress_test["y_pred"] = (
    stress_test[feature] >= selected_threshold
).astype(int)

stress_test["predicted_state"] = np.where(
    stress_test["y_pred"] == 1,
    "moving",
    "idle",
)

stress_test["is_false_positive"] = (
    stress_test["y_pred"] == 1
)

# 연속된 False Positive를 하나의 이벤트로 계산
previous_fp = (
    stress_test
    .groupby("source_file")[
        "is_false_positive"
    ]
    .shift(fill_value=False)
)

stress_test["false_positive_event_start"] = (
    stress_test["is_false_positive"]
    & ~previous_fp
)

total_windows = len(stress_test)
false_positive_count = int(
    stress_test["is_false_positive"].sum()
)
true_negative_count = (
    total_windows - false_positive_count
)

false_positive_event_count = int(
    stress_test[
        "false_positive_event_start"
    ].sum()
)

false_positive_rate = safe_divide(
    false_positive_count,
    total_windows,
)

idle_recall = safe_divide(
    true_negative_count,
    total_windows,
)

test_duration_minutes = total_windows / 60

false_positive_events_per_minute = safe_divide(
    false_positive_event_count,
    test_duration_minutes,
)

# 최대 연속 오분류 Window 수
event_groups = (
    ~stress_test["is_false_positive"]
).cumsum()

max_consecutive_fp_windows = int(
    stress_test
    .groupby(event_groups)[
        "is_false_positive"
    ]
    .sum()
    .max()
)

metrics = pd.DataFrame([{
    "validation_type": "idle_only_stress_test",
    "feature": feature,
    "selected_threshold": selected_threshold,
    "total_idle_windows": total_windows,
    "true_negative": true_negative_count,
    "false_positive": false_positive_count,
    "idle_recall_specificity": idle_recall,
    "false_positive_rate": false_positive_rate,
    "false_positive_event_count":
        false_positive_event_count,
    "false_positive_events_per_minute":
        false_positive_events_per_minute,
    "max_consecutive_fp_windows":
        max_consecutive_fp_windows,
    "feature_min": stress_test[feature].min(),
    "feature_median":
        stress_test[feature].median(),
    "feature_mean": stress_test[feature].mean(),
    "feature_p95":
        stress_test[feature].quantile(0.95),
    "feature_max": stress_test[feature].max(),
    "threshold_margin_above_max": (
        selected_threshold
        - stress_test[feature].max()
    ),
    "macro_f1_applicable": False,
    "balanced_accuracy_applicable": False,
    "independent_session_validation": False,
}])

metrics.to_csv(
    VALIDATION_DIR
    / "idle_stress_test_metrics.csv",
    index=False,
)

prediction_columns = [
    column for column in [
        "vehicle_id",
        "session_id",
        "source_file",
        "timestamp_1s",
        feature,
        "true_state",
        "predicted_state",
        "is_false_positive",
        "false_positive_event_start",
    ]
    if column in stress_test.columns
]

stress_test[
    prediction_columns
].to_csv(
    VALIDATION_DIR
    / "idle_stress_test_predictions.csv",
    index=False,
)

# Timeline 그래프
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    stress_test["timestamp_1s"],
    stress_test[feature],
    marker="o",
    markersize=3,
    linewidth=1.5,
    label="Idle IMU activity",
)

ax.axhline(
    selected_threshold,
    color="red",
    linestyle="--",
    label=(
        f"Threshold {selected_threshold:.4f}"
    ),
)

false_positives = stress_test[
    stress_test["is_false_positive"]
]

if not false_positives.empty:
    ax.scatter(
        false_positives["timestamp_1s"],
        false_positives[feature],
        color="red",
        s=50,
        label="False Positive",
        zorder=3,
    )

ax.set_title("Idle-Only Threshold Stress Test")
ax.set_xlabel("Timestamp")
ax.set_ylabel(
    "Angular Rate Magnitude Mean (deg/s)"
)
ax.grid(alpha=0.25)
ax.legend()

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    FIGURE_DIR
    / "idle_stress_test_timeline.png",
    dpi=200,
)

plt.close(fig)

print("\nIdle-only stress-test metrics:")

print(
    metrics
    .round(4)
    .to_string(index=False)
)

print("\nPrediction distribution:")
print(
    stress_test["predicted_state"]
    .value_counts()
    .to_string()
)

print("\nImportant:")
print(
    "Macro F1 and Balanced Accuracy are not "
    "calculated because this dataset contains "
    "only the Idle class."
)

print("\nSaved outputs:")
print(
    VALIDATION_DIR
    / "idle_stress_test_metrics.csv"
)
print(
    VALIDATION_DIR
    / "idle_stress_test_predictions.csv"
)
print(
    FIGURE_DIR
    / "idle_stress_test_timeline.png"
)
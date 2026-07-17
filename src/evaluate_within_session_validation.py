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
BASELINE_PATH = Path(
    "outputs/validation/baseline_metrics.csv"
)

VALIDATION_DIR = Path("outputs/validation")
FIGURE_DIR = Path("outputs/figures")


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def calculate_metrics(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    moving_precision = safe_divide(tp, tp + fp)
    moving_recall = safe_divide(tp, tp + fn)
    moving_f1 = calculate_f1(
        moving_precision,
        moving_recall,
    )

    idle_precision = safe_divide(tn, tn + fn)
    idle_recall = safe_divide(tn, tn + fp)
    idle_f1 = calculate_f1(
        idle_precision,
        idle_recall,
    )

    return {
        "total_windows": len(y_true),
        "moving_windows": int((y_true == 1).sum()),
        "idle_windows": int((y_true == 0).sum()),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": safe_divide(
            tp + tn,
            len(y_true),
        ),
        "moving_precision": moving_precision,
        "moving_recall": moving_recall,
        "moving_f1": moving_f1,
        "idle_precision": idle_precision,
        "idle_recall": idle_recall,
        "idle_f1": idle_f1,
        "macro_f1": (
            moving_f1 + idle_f1
        ) / 2,
        "balanced_accuracy": (
            moving_recall + idle_recall
        ) / 2,
        "false_positive_rate": safe_divide(
            fp,
            fp + tn,
        ),
        "predicted_moving_ratio": safe_divide(
            tp + fp,
            len(y_true),
        ),
    }


VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

with open(
    THRESHOLD_PATH,
    "r",
    encoding="utf-8",
) as file:
    threshold_info = json.load(file)

if not threshold_info.get(
    "threshold_frozen_before_validation",
    False,
):
    raise ValueError(
        "Threshold was not frozen before validation."
    )

feature = threshold_info["feature"]
selected_threshold = float(
    threshold_info["selected_threshold"]
)

validation = df[
    (df["split_role"] == "within_session_validation")
    & (df["true_state"].isin(["moving", "idle"]))
].copy()

if validation.empty:
    raise ValueError(
        "No within-session validation rows found."
    )

if validation["true_state"].nunique() != 2:
    raise ValueError(
        "Validation must contain both Moving and Idle."
    )

validation["y_true"] = (
    validation["true_state"] == "moving"
).astype(int)

validation["y_pred"] = (
    validation[feature] >= selected_threshold
).astype(int)

validation["predicted_state"] = np.where(
    validation["y_pred"] == 1,
    "moving",
    "idle",
)

validation["classification_result"] = np.select(
    [
        (validation["y_true"] == 1)
        & (validation["y_pred"] == 1),

        (validation["y_true"] == 0)
        & (validation["y_pred"] == 0),

        (validation["y_true"] == 0)
        & (validation["y_pred"] == 1),

        (validation["y_true"] == 1)
        & (validation["y_pred"] == 0),
    ],
    ["TP", "TN", "FP", "FN"],
    default="unknown",
)

metrics = calculate_metrics(
    validation["y_true"],
    validation["y_pred"],
)

# Validation Baseline 불러오기
baseline_macro_f1 = np.nan
baseline_balanced_accuracy = np.nan
best_baseline_model = None

if BASELINE_PATH.exists():
    baseline = pd.read_csv(BASELINE_PATH)

    validation_baseline = baseline[
        baseline["split_role"]
        == "within_session_validation"
    ].dropna(subset=["macro_f1"])

    if not validation_baseline.empty:
        best_baseline = (
            validation_baseline
            .sort_values(
                "macro_f1",
                ascending=False,
            )
            .iloc[0]
        )

        best_baseline_model = (
            best_baseline["baseline_model"]
        )
        baseline_macro_f1 = float(
            best_baseline["macro_f1"]
        )
        baseline_balanced_accuracy = float(
            best_baseline[
                "balanced_accuracy"
            ]
        )

metrics_row = {
    "validation_type": "within_session_validation",
    "feature": feature,
    "selected_threshold": selected_threshold,
    **metrics,
    "best_baseline_model": best_baseline_model,
    "baseline_macro_f1": baseline_macro_f1,
    "macro_f1_improvement_over_baseline": (
        metrics["macro_f1"] - baseline_macro_f1
    ),
    "baseline_balanced_accuracy":
        baseline_balanced_accuracy,
    "balanced_accuracy_improvement_over_baseline": (
        metrics["balanced_accuracy"]
        - baseline_balanced_accuracy
    ),
    "development_macro_f1": threshold_info[
        "development_macro_f1"
    ],
    "development_balanced_accuracy": threshold_info[
        "development_balanced_accuracy"
    ],
    "macro_f1_change_from_development": (
        metrics["macro_f1"]
        - threshold_info["development_macro_f1"]
    ),
    "balanced_accuracy_change_from_development": (
        metrics["balanced_accuracy"]
        - threshold_info[
            "development_balanced_accuracy"
        ]
    ),
    "independent_session_validation": False,
}

metrics_df = pd.DataFrame([metrics_row])

metrics_df.to_csv(
    VALIDATION_DIR / "within_session_metrics.csv",
    index=False,
)

prediction_columns = [
    column for column in [
        "vehicle_id",
        "session_id",
        "source_file",
        "timestamp_1s",
        feature,
        "vehicle_speed_kmh",
        "engine_rpm",
        "true_state",
        "predicted_state",
        "y_true",
        "y_pred",
        "classification_result",
    ]
    if column in validation.columns
]

validation[
    prediction_columns
].to_csv(
    VALIDATION_DIR
    / "within_session_predictions.csv",
    index=False,
)

# Confusion Matrix
confusion_matrix = np.array([
    [
        metrics["true_negative"],
        metrics["false_positive"],
    ],
    [
        metrics["false_negative"],
        metrics["true_positive"],
    ],
])

fig, ax = plt.subplots(figsize=(6, 5))

image = ax.imshow(
    confusion_matrix,
    cmap="Blues",
)

ax.set_xticks([0, 1])
ax.set_xticklabels(["Predicted Idle", "Predicted Moving"])

ax.set_yticks([0, 1])
ax.set_yticklabels(["Actual Idle", "Actual Moving"])

for row in range(2):
    for column in range(2):
        ax.text(
            column,
            row,
            confusion_matrix[row, column],
            ha="center",
            va="center",
            fontsize=16,
            color="black",
        )

ax.set_title(
    "Within-Session Validation\n"
    f"Threshold = {selected_threshold:.4f}"
)

fig.colorbar(image, ax=ax)
fig.tight_layout()

fig.savefig(
    FIGURE_DIR
    / "within_session_confusion_matrix.png",
    dpi=200,
)

plt.close(fig)

print("\nWithin-session validation metrics:")

display_columns = [
    "selected_threshold",
    "total_windows",
    "moving_windows",
    "idle_windows",
    "true_positive",
    "true_negative",
    "false_positive",
    "false_negative",
    "accuracy",
    "moving_precision",
    "moving_recall",
    "moving_f1",
    "idle_precision",
    "idle_recall",
    "idle_f1",
    "macro_f1",
    "balanced_accuracy",
    "false_positive_rate",
    "baseline_macro_f1",
    "macro_f1_improvement_over_baseline",
    "macro_f1_change_from_development",
]

print(
    metrics_df[display_columns]
    .round(4)
    .to_string(index=False)
)

print("\nClassification results:")
print(
    validation[
        "classification_result"
    ].value_counts().to_string()
)

print("\nImportant:")
print(
    "This is chronological within-session validation, "
    "not independent-session generalization."
)

print("\nSaved outputs:")
print(
    VALIDATION_DIR
    / "within_session_metrics.csv"
)
print(
    VALIDATION_DIR
    / "within_session_predictions.csv"
)
print(
    FIGURE_DIR
    / "within_session_confusion_matrix.png"
)
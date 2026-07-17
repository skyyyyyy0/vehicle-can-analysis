from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DATA_PATH = Path(
    "data/processed/imu_binary_split_dataset.csv"
)
PERFORMANCE_PATH = Path(
    "outputs/validation/threshold_performance.csv"
)

VALIDATION_DIR = Path("outputs/validation")
FIGURE_DIR = Path("outputs/figures")

FEATURE = "angular_rate_magnitude_mean"

# 안정성 판정 기준
MAX_METRIC_DROP = 0.05
MAX_RECALL_DROP = 0.10


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
        "predicted_moving_ratio": safe_divide(
            tp + fp,
            len(y_true),
        ),
    }


VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)
performance = pd.read_csv(PERFORMANCE_PATH)

development = df[
    (df["split_role"] == "development")
    & (df["true_state"].isin(["moving", "idle"]))
].copy()

development["y_true"] = (
    development["true_state"] == "moving"
).astype(int)

# Step 5와 같은 기준으로 최고 Threshold 선택
ranked = performance.sort_values(
    by=[
        "macro_f1",
        "balanced_accuracy",
        "minimum_class_recall",
        "moving_recall",
    ],
    ascending=[False, False, False, False],
).reset_index(drop=True)

selected_threshold = float(
    ranked.iloc[0]["threshold"]
)

selected_pred = (
    development[FEATURE] >= selected_threshold
).astype(int)

selected_metrics = calculate_metrics(
    development["y_true"],
    selected_pred,
)

# -20%, -10%, 선택값, +10%, +20%
percentage_changes = [-20, -10, 0, 10, 20]

sensitivity_rows = []

for percentage_change in percentage_changes:
    threshold = selected_threshold * (
        1 + percentage_change / 100
    )

    y_pred = (
        development[FEATURE] >= threshold
    ).astype(int)

    metrics = calculate_metrics(
        development["y_true"],
        y_pred,
    )

    macro_f1_drop = (
        selected_metrics["macro_f1"]
        - metrics["macro_f1"]
    )

    balanced_accuracy_drop = (
        selected_metrics["balanced_accuracy"]
        - metrics["balanced_accuracy"]
    )

    moving_recall_drop = (
        selected_metrics["moving_recall"]
        - metrics["moving_recall"]
    )

    is_stable = (
        macro_f1_drop <= MAX_METRIC_DROP
        and balanced_accuracy_drop
        <= MAX_METRIC_DROP
        and moving_recall_drop
        <= MAX_RECALL_DROP
    )

    sensitivity_rows.append({
        "threshold_pct_change": percentage_change,
        "threshold": threshold,
        **metrics,
        "macro_f1_drop": macro_f1_drop,
        "balanced_accuracy_drop":
            balanced_accuracy_drop,
        "moving_recall_drop":
            moving_recall_drop,
        "is_stable": is_stable,
    })

sensitivity = pd.DataFrame(sensitivity_rows)

sensitivity.to_csv(
    VALIDATION_DIR / "threshold_sensitivity.csv",
    index=False,
)

stable_rows = sensitivity[
    sensitivity["is_stable"]
]

stable_threshold_min = (
    stable_rows["threshold"].min()
    if not stable_rows.empty else np.nan
)

stable_threshold_max = (
    stable_rows["threshold"].max()
    if not stable_rows.empty else np.nan
)

local_rows = sensitivity[
    sensitivity["threshold_pct_change"].isin(
        [-10, 0, 10]
    )
]

local_stability_pass = bool(
    local_rows["is_stable"].all()
)

broad_stability_pass = bool(
    sensitivity["is_stable"].all()
)

stability_summary = pd.DataFrame([{
    "selected_threshold": selected_threshold,
    "selected_macro_f1":
        selected_metrics["macro_f1"],
    "selected_balanced_accuracy":
        selected_metrics["balanced_accuracy"],
    "selected_moving_recall":
        selected_metrics["moving_recall"],
    "stable_threshold_min":
        stable_threshold_min,
    "stable_threshold_max":
        stable_threshold_max,
    "local_10pct_stability_pass":
        local_stability_pass,
    "broad_20pct_stability_pass":
        broad_stability_pass,
    "max_macro_f1_drop":
        sensitivity["macro_f1_drop"].max(),
    "max_balanced_accuracy_drop":
        sensitivity[
            "balanced_accuracy_drop"
        ].max(),
    "max_moving_recall_drop":
        sensitivity["moving_recall_drop"].max(),
}])

stability_summary.to_csv(
    VALIDATION_DIR
    / "threshold_stability_summary.csv",
    index=False,
)

# Validation 확인 전에 Threshold 고정
selected_threshold_info = {
    "feature": FEATURE,
    "selected_threshold": selected_threshold,
    "selection_dataset": "development",
    "selection_metric": "macro_f1",
    "development_macro_f1": float(
        selected_metrics["macro_f1"]
    ),
    "development_balanced_accuracy": float(
        selected_metrics[
            "balanced_accuracy"
        ]
    ),
    "development_moving_recall": float(
        selected_metrics["moving_recall"]
    ),
    "stable_threshold_min": (
        None
        if np.isnan(stable_threshold_min)
        else float(stable_threshold_min)
    ),
    "stable_threshold_max": (
        None
        if np.isnan(stable_threshold_max)
        else float(stable_threshold_max)
    ),
    "local_10pct_stability_pass":
        local_stability_pass,
    "broad_20pct_stability_pass":
        broad_stability_pass,
    "validation_used_for_selection": False,
    "threshold_frozen_before_validation": True,
}

with open(
    VALIDATION_DIR / "selected_threshold.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        selected_threshold_info,
        file,
        indent=2,
    )

# Sensitivity 그래프
fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    sensitivity["threshold"],
    sensitivity["macro_f1"],
    marker="o",
    label="Macro F1",
)

ax.plot(
    sensitivity["threshold"],
    sensitivity["balanced_accuracy"],
    marker="o",
    label="Balanced Accuracy",
)

ax.plot(
    sensitivity["threshold"],
    sensitivity["moving_recall"],
    marker="o",
    label="Moving Recall",
)

ax.plot(
    sensitivity["threshold"],
    sensitivity["predicted_moving_ratio"],
    marker="o",
    label="Predicted Moving Ratio",
)

ax.axvline(
    selected_threshold,
    color="black",
    linestyle=":",
    label=(
        f"Selected Threshold "
        f"{selected_threshold:.4f}"
    ),
)

ax.set_title("IMU Threshold Sensitivity")
ax.set_xlabel(
    "Angular Rate Magnitude Mean Threshold (deg/s)"
)
ax.set_ylabel("Metric")
ax.set_ylim(0, 1.05)
ax.grid(alpha=0.25)
ax.legend()

fig.tight_layout()
fig.savefig(
    FIGURE_DIR / "threshold_sensitivity.png",
    dpi=200,
)
plt.close(fig)

print("\nThreshold sensitivity:")
display_columns = [
    "threshold_pct_change",
    "threshold",
    "true_positive",
    "true_negative",
    "false_positive",
    "false_negative",
    "macro_f1",
    "balanced_accuracy",
    "moving_recall",
    "predicted_moving_ratio",
    "is_stable",
]

print(
    sensitivity[display_columns]
    .round(4)
    .to_string(index=False)
)

print("\nThreshold stability summary:")
print(
    stability_summary
    .round(4)
    .to_string(index=False)
)

print("\nThreshold frozen before validation:")
print(
    json.dumps(
        selected_threshold_info,
        indent=2,
    )
)

print("\nSaved outputs:")
print(
    VALIDATION_DIR / "threshold_sensitivity.csv"
)
print(
    VALIDATION_DIR
    / "threshold_stability_summary.csv"
)
print(
    VALIDATION_DIR / "selected_threshold.json"
)
print(
    FIGURE_DIR / "threshold_sensitivity.png"
)
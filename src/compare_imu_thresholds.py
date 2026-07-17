from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


INPUT_PATH = Path(
    "data/processed/imu_binary_split_dataset.csv"
)
BASELINE_PATH = Path(
    "outputs/validation/baseline_metrics.csv"
)

VALIDATION_DIR = Path("outputs/validation")
FIGURE_DIR = Path("outputs/figures")

FEATURE = "angular_rate_magnitude_mean"


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0.0

    return (
        2
        * precision
        * recall
        / (precision + recall)
    )


def calculate_metrics(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    total = len(y_true)

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

    macro_f1 = (moving_f1 + idle_f1) / 2

    balanced_accuracy = (
        moving_recall + idle_recall
    ) / 2

    return {
        "total_windows": total,
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": safe_divide(tp + tn, total),
        "moving_precision": moving_precision,
        "moving_recall": moving_recall,
        "moving_f1": moving_f1,
        "idle_precision": idle_precision,
        "idle_recall": idle_recall,
        "idle_f1": idle_f1,
        "macro_f1": macro_f1,
        "balanced_accuracy": balanced_accuracy,
        "minimum_class_recall": min(
            moving_recall,
            idle_recall,
        ),
        "false_positive_rate": safe_divide(
            fp,
            fp + tn,
        ),
        "predicted_moving_ratio": safe_divide(
            tp + fp,
            total,
        ),
    }


VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_PATH)

required_columns = {
    "split_role",
    "true_state",
    FEATURE,
}

missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

development = df[
    (df["split_role"] == "development")
    & (df["true_state"].isin(["moving", "idle"]))
].copy()

development = development.dropna(subset=[FEATURE])

development["y_true"] = (
    development["true_state"] == "moving"
).astype(int)

if development["true_state"].nunique() != 2:
    raise ValueError(
        "Development data must contain both Moving and Idle."
    )

# 고유 Feature 값 사이의 중간값을 Threshold로 사용
unique_values = np.sort(
    development[FEATURE].unique()
)

if len(unique_values) < 2:
    raise ValueError(
        "At least two unique feature values are required."
    )

thresholds = (
    unique_values[:-1] + unique_values[1:]
) / 2

performance_rows = []

for threshold in thresholds:
    y_pred = (
        development[FEATURE] >= threshold
    ).astype(int)

    metrics = calculate_metrics(
        development["y_true"],
        y_pred,
    )

    metrics["threshold"] = float(threshold)
    performance_rows.append(metrics)

performance = pd.DataFrame(performance_rows)

# 동일한 성능일 경우 두 클래스 Recall이 균형적인 값을 우선
ranked = performance.sort_values(
    by=[
        "macro_f1",
        "balanced_accuracy",
        "minimum_class_recall",
        "moving_recall",
    ],
    ascending=[
        False,
        False,
        False,
        False,
    ],
).reset_index(drop=True)

ranked.insert(
    0,
    "performance_rank",
    np.arange(1, len(ranked) + 1),
)

best_threshold = ranked.iloc[0]

# Threshold 순서 결과
performance = performance.sort_values(
    "threshold"
).reset_index(drop=True)

performance.to_csv(
    VALIDATION_DIR / "threshold_performance.csv",
    index=False,
)

# 상위 10개 후보
top_candidates = ranked.head(10).copy()

top_candidates.to_csv(
    VALIDATION_DIR / "top_threshold_candidates.csv",
    index=False,
)

# Baseline 값 불러오기
baseline_macro_f1 = np.nan
baseline_balanced_accuracy = np.nan

if BASELINE_PATH.exists():
    baseline = pd.read_csv(BASELINE_PATH)

    development_baseline = baseline[
        baseline["split_role"] == "development"
    ]

    baseline_macro_f1 = (
        development_baseline["macro_f1"].max()
    )

    baseline_balanced_accuracy = (
        development_baseline[
            "balanced_accuracy"
        ].max()
    )

# 성능 그래프
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(
    performance["threshold"],
    performance["macro_f1"],
    label="Macro F1",
    linewidth=2,
)

ax.plot(
    performance["threshold"],
    performance["balanced_accuracy"],
    label="Balanced Accuracy",
    linewidth=2,
)

ax.plot(
    performance["threshold"],
    performance["moving_recall"],
    label="Moving Recall",
    linestyle="--",
    alpha=0.8,
)

ax.plot(
    performance["threshold"],
    performance["idle_recall"],
    label="Idle Recall",
    linestyle="--",
    alpha=0.8,
)

ax.axvline(
    best_threshold["threshold"],
    color="black",
    linestyle=":",
    label=(
        "Best development threshold "
        f"{best_threshold['threshold']:.4f}"
    ),
)

if not np.isnan(baseline_macro_f1):
    ax.axhline(
        baseline_macro_f1,
        color="gray",
        linestyle=":",
        alpha=0.7,
        label=(
            "Baseline Macro F1 "
            f"{baseline_macro_f1:.4f}"
        ),
    )

ax.set_title(
    "Development IMU Threshold Performance"
)
ax.set_xlabel(
    "Angular Rate Magnitude Mean Threshold (deg/s)"
)
ax.set_ylabel("Metric")
ax.set_ylim(0, 1.05)
ax.grid(alpha=0.25)
ax.legend(loc="best")

fig.tight_layout()
fig.savefig(
    FIGURE_DIR / "threshold_performance_curve.png",
    dpi=200,
)
plt.close(fig)

print("\nDevelopment data:")
print(f"Total windows: {len(development)}")
print(
    development["true_state"]
    .value_counts()
    .to_string()
)

print(f"\nUnique feature values: {len(unique_values)}")
print(f"Threshold candidates: {len(thresholds)}")

print("\nTop 10 threshold candidates:")
display_columns = [
    "performance_rank",
    "threshold",
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
    "predicted_moving_ratio",
]

print(
    top_candidates[display_columns]
    .round(4)
    .to_string(index=False)
)

print("\nProvisional best threshold:")
print(f"Threshold: {best_threshold['threshold']:.6f}")
print(f"Macro F1: {best_threshold['macro_f1']:.4f}")
print(
    "Balanced Accuracy: "
    f"{best_threshold['balanced_accuracy']:.4f}"
)
print(
    "Moving Recall: "
    f"{best_threshold['moving_recall']:.4f}"
)
print(
    "Idle Recall: "
    f"{best_threshold['idle_recall']:.4f}"
)

print("\nImportant:")
print(
    "This is a development-only provisional threshold. "
    "Validation data has not been used."
)

print("\nSaved outputs:")
print(VALIDATION_DIR / "threshold_performance.csv")
print(VALIDATION_DIR / "top_threshold_candidates.csv")
print(FIGURE_DIR / "threshold_performance_curve.png")
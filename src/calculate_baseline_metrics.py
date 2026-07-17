from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/imu_binary_split_dataset.csv"
)

OUTPUT_FILE = Path(
    "outputs/validation/baseline_metrics.csv"
)


def safe_divide(
    numerator,
    denominator,
    default=0.0,
):
    if denominator == 0:
        return default

    return numerator / denominator


def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def calculate_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    tp = int(
        ((y_true == 1) & (y_pred == 1)).sum()
    )
    tn = int(
        ((y_true == 0) & (y_pred == 0)).sum()
    )
    fp = int(
        ((y_true == 0) & (y_pred == 1)).sum()
    )
    fn = int(
        ((y_true == 1) & (y_pred == 0)).sum()
    )

    moving_support = int((y_true == 1).sum())
    idle_support = int((y_true == 0).sum())

    accuracy = safe_divide(
        tp + tn,
        len(y_true),
    )

    moving_precision = safe_divide(
        tp,
        tp + fp,
    )
    moving_recall = safe_divide(
        tp,
        tp + fn,
    )
    moving_f1 = calculate_f1(
        moving_precision,
        moving_recall,
    )

    idle_precision = safe_divide(
        tn,
        tn + fn,
    )
    idle_recall = safe_divide(
        tn,
        tn + fp,
    )
    idle_f1 = calculate_f1(
        idle_precision,
        idle_recall,
    )

    # 두 실제 클래스가 모두 존재할 때만 계산
    if moving_support > 0 and idle_support > 0:
        macro_f1 = (
            moving_f1 + idle_f1
        ) / 2

        balanced_accuracy = (
            moving_recall + idle_recall
        ) / 2
    else:
        macro_f1 = np.nan
        balanced_accuracy = np.nan

    false_positive_rate = safe_divide(
        fp,
        fp + tn,
        default=np.nan,
    )

    return {
        "total_windows": len(y_true),
        "moving_support": moving_support,
        "idle_support": idle_support,
        "predicted_moving": int((y_pred == 1).sum()),
        "predicted_idle": int((y_pred == 0).sum()),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "moving_precision": moving_precision,
        "moving_recall": moving_recall,
        "moving_f1": moving_f1,
        "idle_precision": idle_precision,
        "idle_recall": idle_recall,
        "idle_f1": idle_f1,
        "macro_f1": macro_f1,
        "balanced_accuracy": balanced_accuracy,
        "false_positive_rate": false_positive_rate,
    }

# --------------------------------------------------
# 1. 데이터 로드
# --------------------------------------------------

split_data = pd.read_csv(INPUT_FILE)

split_data["timestamp_1s"] = pd.to_datetime(
    split_data["timestamp_1s"],
    utc=True,
)


# --------------------------------------------------
# 2. Development Majority Class 결정
# --------------------------------------------------

development = split_data.loc[
    split_data["split_role"] == "development"
].copy()

moving_count = int(
    (development["y_true"] == 1).sum()
)
idle_count = int(
    (development["y_true"] == 0).sum()
)

development_majority_class = (
    1 if moving_count >= idle_count else 0
)

development_majority_name = (
    "moving"
    if development_majority_class == 1
    else "idle"
)

print(
    "Development majority class:",
    development_majority_name,
)


# --------------------------------------------------
# 3. Baseline 모델
# --------------------------------------------------

baseline_models = {
    "always_idle": 0,
    "always_moving": 1,
    "development_majority": (
        development_majority_class
    ),
}


# --------------------------------------------------
# 4. 데이터 역할별 Baseline 계산
# --------------------------------------------------

result_rows = []

role_order = [
    "development",
    "within_session_validation",
    "idle_stress_test",
    "transition_diagnostic",
]

for split_role in role_order:
    subset = split_data.loc[
        split_data["split_role"] == split_role
    ].copy()

    if subset.empty:
        continue

    y_true = subset["y_true"].to_numpy()

    for baseline_name, prediction_value in (
        baseline_models.items()
    ):
        y_pred = np.full(
            shape=len(subset),
            fill_value=prediction_value,
            dtype=int,
        )

        metrics = calculate_metrics(
            y_true,
            y_pred,
        )

        result_rows.append({
            "split_role": split_role,
            "baseline_model": baseline_name,
            "predicted_class": (
                "moving"
                if prediction_value == 1
                else "idle"
            ),
            **metrics,
        })


baseline_results = pd.DataFrame(result_rows)


# --------------------------------------------------
# 5. 결과 저장
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

baseline_results.to_csv(
    OUTPUT_FILE,
    index=False,
)


# --------------------------------------------------
# 6. 핵심 결과 출력
# --------------------------------------------------

display_columns = [
    "split_role",
    "baseline_model",
    "predicted_class",
    "total_windows",
    "accuracy",
    "moving_f1",
    "idle_f1",
    "macro_f1",
    "balanced_accuracy",
    "false_positive_rate",
]

print("\nBaseline metrics:")
print(
    baseline_results[display_columns]
    .round(4)
    .to_string(index=False)
)

print(f"\nSaved to: {OUTPUT_FILE}")
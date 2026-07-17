import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PYTHON_SPLIT_PATH = (
    ROOT / "outputs/validation/validation_split_summary.csv"
)
PYTHON_THRESHOLD_PATH = (
    ROOT / "outputs/validation/threshold_performance.csv"
)
PYTHON_SELECTED_PATH = (
    ROOT / "outputs/validation/selected_threshold.json"
)
PYTHON_VALIDATION_PATH = (
    ROOT / "outputs/validation/within_session_metrics.csv"
)
PYTHON_IDLE_PATH = (
    ROOT / "outputs/validation/idle_stress_test_metrics.csv"
)

SQL_THRESHOLD_PATH = (
    ROOT / "outputs/sql/validation/sql_threshold_performance.csv"
)
SQL_VALIDATION_PATH = (
    ROOT
    / "outputs/sql/validation/"
    / "sql_selected_threshold_validation.csv"
)

OUTPUT_PATH = (
    ROOT
    / "outputs/validation/"
    / "python_sql_metric_comparison.csv"
)


required_files = [
    PYTHON_SPLIT_PATH,
    PYTHON_THRESHOLD_PATH,
    PYTHON_SELECTED_PATH,
    PYTHON_VALIDATION_PATH,
    PYTHON_IDLE_PATH,
    SQL_THRESHOLD_PATH,
    SQL_VALIDATION_PATH,
]

missing_files = [
    path for path in required_files if not path.exists()
]

if missing_files:
    missing_text = "\n".join(str(path) for path in missing_files)
    raise FileNotFoundError(
        f"Required files are missing:\n{missing_text}"
    )


python_split = pd.read_csv(PYTHON_SPLIT_PATH)
python_threshold = pd.read_csv(PYTHON_THRESHOLD_PATH)
python_validation = pd.read_csv(PYTHON_VALIDATION_PATH)
python_idle = pd.read_csv(PYTHON_IDLE_PATH)

sql_threshold = pd.read_csv(SQL_THRESHOLD_PATH)
sql_validation = pd.read_csv(SQL_VALIDATION_PATH)

with open(
    PYTHON_SELECTED_PATH,
    "r",
    encoding="utf-8",
) as file:
    selected_threshold_data = json.load(file)


selected_threshold = float(
    selected_threshold_data["selected_threshold"]
)


def select_role(dataframe, split_role):
    selected = dataframe[
        dataframe["split_role"] == split_role
    ]

    if selected.empty:
        raise ValueError(
            f"Split role not found: {split_role}"
        )

    return selected.iloc[0]


python_development = select_role(
    python_split,
    "development",
)
sql_development = select_role(
    sql_validation,
    "development",
)
sql_within_validation = select_role(
    sql_validation,
    "within_session_validation",
)
sql_idle_stress = select_role(
    sql_validation,
    "idle_stress_test",
)


python_best = python_threshold.iloc[
    (
        python_threshold["threshold"]
        - selected_threshold
    ).abs().argmin()
]

sql_best = sql_threshold.sort_values(
    ["performance_rank", "threshold"]
).iloc[0]


comparison_rows = []


def add_comparison(
    comparison_group,
    metric_name,
    python_value,
    sql_value,
    tolerance,
):
    python_numeric = float(python_value)
    sql_numeric = float(sql_value)

    absolute_difference = abs(
        python_numeric - sql_numeric
    )

    status = (
        "PASS"
        if absolute_difference <= tolerance
        else "FAIL"
    )

    comparison_rows.append(
        {
            "comparison_group": comparison_group,
            "metric_name": metric_name,
            "python_value": python_numeric,
            "sql_value": sql_numeric,
            "absolute_difference": absolute_difference,
            "tolerance": tolerance,
            "status": status,
        }
    )


# Development 데이터 개수 비교
for metric in [
    "total_windows",
    "moving_windows",
    "idle_windows",
]:
    add_comparison(
        "development_dataset",
        metric,
        python_development[metric],
        sql_development[metric],
        0,
    )


# Threshold 후보 개수 비교
add_comparison(
    "threshold_selection",
    "threshold_candidate_count",
    len(python_threshold),
    len(sql_threshold),
    0,
)

# 선택 Threshold 비교
add_comparison(
    "threshold_selection",
    "selected_threshold",
    selected_threshold,
    sql_best["threshold"],
    0.000001,
)


# Development Threshold 성능 비교
development_metrics = [
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

for metric in development_metrics:
    tolerance = (
        0
        if metric in {
            "true_positive",
            "true_negative",
            "false_positive",
            "false_negative",
        }
        else 0.000001
    )

    add_comparison(
        "development_threshold_metrics",
        metric,
        python_best[metric],
        sql_best[metric],
        tolerance,
    )


# Within-Session Validation 비교
validation_metrics = [
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
]

for metric in validation_metrics:
    tolerance = (
        0
        if metric in {
            "total_windows",
            "moving_windows",
            "idle_windows",
            "true_positive",
            "true_negative",
            "false_positive",
            "false_negative",
        }
        else 0.000001
    )

    add_comparison(
        "within_session_validation",
        metric,
        python_validation.iloc[0][metric],
        sql_within_validation[metric],
        tolerance,
    )


# Idle Stress Test 비교
idle_metric_mapping = {
    "total_idle_windows": "idle_windows",
    "true_negative": "true_negative",
    "false_positive": "false_positive",
    "idle_recall_specificity": "idle_recall",
    "false_positive_rate": "false_positive_rate",
}

for python_metric, sql_metric in idle_metric_mapping.items():
    tolerance = (
        0
        if python_metric in {
            "total_idle_windows",
            "true_negative",
            "false_positive",
        }
        else 0.000001
    )

    add_comparison(
        "idle_stress_test",
        python_metric,
        python_idle.iloc[0][python_metric],
        sql_idle_stress[sql_metric],
        tolerance,
    )


comparison = pd.DataFrame(comparison_rows)

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)
comparison.to_csv(
    OUTPUT_PATH,
    index=False,
)


print("\nPython–SQL metric comparison:")
print(comparison.to_string(index=False))

print("\nStatus summary:")
print(comparison["status"].value_counts())

failed_checks = comparison[
    comparison["status"] == "FAIL"
]

print(f"\nSaved to: {OUTPUT_PATH}")

if not failed_checks.empty:
    print("\nFailed checks:")
    print(
        failed_checks[
            [
                "comparison_group",
                "metric_name",
                "python_value",
                "sql_value",
                "absolute_difference",
            ]
        ].to_string(index=False)
    )
    raise SystemExit(1)

print("\nAll Python–SQL comparisons passed.")
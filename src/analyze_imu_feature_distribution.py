from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


INPUT_PATH = Path("data/processed/imu_binary_split_dataset.csv")
VALIDATION_DIR = Path("outputs/validation")
FIGURE_DIR = Path("outputs/figures")

PRIMARY_FEATURE = "angular_rate_magnitude_mean"

SECONDARY_FEATURES = [
    "angular_rate_magnitude_std",
    "angular_rate_magnitude_max",
    "acceleration_deviation_mean",
    "acceleration_deviation_max",
]


def summarize_feature(df, feature):
    rows = []

    for state in ["idle", "moving"]:
        values = df.loc[df["true_state"] == state, feature].dropna()

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_count = (
            (values < lower_bound) | (values > upper_bound)
        ).sum()

        rows.append({
            "feature": feature,
            "true_state": state,
            "count": len(values),
            "min": values.min(),
            "q1": q1,
            "median": values.median(),
            "mean": values.mean(),
            "q3": q3,
            "max": values.max(),
            "std": values.std(),
            "iqr": iqr,
            "lower_outlier_bound": lower_bound,
            "upper_outlier_bound": upper_bound,
            "outlier_count": int(outlier_count),
            "outlier_ratio_pct": outlier_count / len(values) * 100,
        })

    return pd.DataFrame(rows)


VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_PATH)

required_columns = {
    "split_role",
    "true_state",
    PRIMARY_FEATURE,
}

missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

development = df[
    (df["split_role"] == "development")
    & (df["true_state"].isin(["moving", "idle"]))
].copy()

if development.empty:
    raise ValueError("No development data found.")

# Primary Feature 요약
primary_summary = summarize_feature(development, PRIMARY_FEATURE)

primary_summary.to_csv(
    VALIDATION_DIR / "imu_primary_feature_distribution.csv",
    index=False,
)

# Secondary Feature 요약
available_secondary = [
    feature for feature in SECONDARY_FEATURES
    if feature in development.columns
]

secondary_summaries = [
    summarize_feature(development, feature)
    for feature in available_secondary
]

if secondary_summaries:
    secondary_summary = pd.concat(
        secondary_summaries,
        ignore_index=True,
    )
    secondary_summary.to_csv(
        VALIDATION_DIR / "imu_secondary_feature_distribution.csv",
        index=False,
    )

# Primary Feature 중첩 분석
idle = development.loc[
    development["true_state"] == "idle",
    PRIMARY_FEATURE,
].dropna()

moving = development.loc[
    development["true_state"] == "moving",
    PRIMARY_FEATURE,
].dropna()

overlap_lower = max(idle.min(), moving.min())
overlap_upper = min(idle.max(), moving.max())
has_observed_overlap = overlap_lower <= overlap_upper

idle_q3 = idle.quantile(0.75)
moving_q1 = moving.quantile(0.25)

pooled_std = np.sqrt(
    (
        (len(moving) - 1) * moving.std() ** 2
        + (len(idle) - 1) * idle.std() ** 2
    )
    / (len(moving) + len(idle) - 2)
)

cohens_d = (
    (moving.mean() - idle.mean()) / pooled_std
    if pooled_std > 0 else np.nan
)

overlap_summary = pd.DataFrame([{
    "feature": PRIMARY_FEATURE,
    "idle_median": idle.median(),
    "moving_median": moving.median(),
    "median_difference": moving.median() - idle.median(),
    "idle_q3": idle_q3,
    "moving_q1": moving_q1,
    "central_iqr_gap": moving_q1 - idle_q3,
    "observed_overlap_exists": has_observed_overlap,
    "observed_overlap_lower": (
        overlap_lower if has_observed_overlap else np.nan
    ),
    "observed_overlap_upper": (
        overlap_upper if has_observed_overlap else np.nan
    ),
    "cohens_d": cohens_d,
}])

overlap_summary.to_csv(
    VALIDATION_DIR / "imu_feature_overlap_summary.csv",
    index=False,
)

# Box Plot
fig, ax = plt.subplots(figsize=(8, 5))

boxplot = ax.boxplot(
    [idle, moving],
    labels=["Idle", "Moving"],
    patch_artist=True,
    showfliers=True,
)

for box, color in zip(
    boxplot["boxes"],
    ["#4C78A8", "#F58518"],
):
    box.set_facecolor(color)
    box.set_alpha(0.7)

ax.set_title("Development IMU Activity Distribution")
ax.set_ylabel("Angular Rate Magnitude Mean (deg/s)")
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()
fig.savefig(
    FIGURE_DIR / "imu_primary_feature_boxplot.png",
    dpi=200,
)
plt.close(fig)

# Distribution Plot
fig, ax = plt.subplots(figsize=(8, 5))

ax.hist(
    idle,
    bins=10,
    alpha=0.6,
    density=True,
    label="Idle",
    color="#4C78A8",
)

ax.hist(
    moving,
    bins=10,
    alpha=0.6,
    density=True,
    label="Moving",
    color="#F58518",
)

ax.set_title("Development IMU Feature Distribution")
ax.set_xlabel("Angular Rate Magnitude Mean (deg/s)")
ax.set_ylabel("Density")
ax.legend()
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()
fig.savefig(
    FIGURE_DIR / "imu_primary_feature_distribution.png",
    dpi=200,
)
plt.close(fig)

print("\nPrimary feature distribution:")
print(primary_summary.round(4).to_string(index=False))

print("\nFeature overlap summary:")
print(overlap_summary.round(4).to_string(index=False))

print("\nSaved outputs:")
print(VALIDATION_DIR / "imu_primary_feature_distribution.csv")
print(VALIDATION_DIR / "imu_secondary_feature_distribution.csv")
print(VALIDATION_DIR / "imu_feature_overlap_summary.csv")
print(FIGURE_DIR / "imu_primary_feature_boxplot.png")
print(FIGURE_DIR / "imu_primary_feature_distribution.png")
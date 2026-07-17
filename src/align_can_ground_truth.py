from pathlib import Path

import pandas as pd


CAN_INPUT = Path(
    "data/processed/can_byte4_processed.csv"
)
GROUND_TRUTH_INPUT = Path(
    "data/processed/ground_truth_processed.csv"
)

CAN_1S_OUTPUT = Path(
    "data/processed/can_byte4_1s.csv"
)
ALIGNED_OUTPUT = Path(
    "data/processed/aligned_can_ground_truth.csv"
)
SUMMARY_OUTPUT = Path(
    "outputs/validation/timestamp_alignment_summary.csv"
)


# --------------------------------------------------
# 1. CAN Byte 4 데이터 로드 및 1초 집계
# --------------------------------------------------

can_raw = pd.read_csv(CAN_INPUT)

can_raw["timestamp"] = pd.to_datetime(
    can_raw["timestamp"],
    utc=True,
)

can_raw["timestamp_1s"] = (
    can_raw["timestamp"].dt.floor("s")
)

can_raw = can_raw.sort_values(
    ["vehicle_id", "session_id", "source_file", "timestamp"]
)

join_keys = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
]

can_1s = (
    can_raw
    .groupby(join_keys, as_index=False)
    .agg(
        byte_4_last=("byte_4", "last"),
        byte_4_diff_mean=("byte_4_diff", "mean"),
        byte_4_diff_max=("byte_4_diff", "max"),
        byte_4_nonzero_transition_count=(
            "byte_4_diff",
            lambda values: int(
                (values.fillna(0) > 0).sum()
            ),
        ),
        can_record_count=("byte_4", "size"),
    )
)

if can_1s.duplicated(join_keys).any():
    raise ValueError("Duplicate CAN 1-second keys detected.")

CAN_1S_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
can_1s.to_csv(CAN_1S_OUTPUT, index=False)


# --------------------------------------------------
# 2. Ground Truth 데이터 준비
# --------------------------------------------------

ground_truth = pd.read_csv(GROUND_TRUTH_INPUT)

ground_truth["timestamp_1s"] = pd.to_datetime(
    ground_truth["timestamp_1s"],
    utc=True,
)

ground_truth = ground_truth.rename(
    columns={
        "ground_truth_state": "true_state",
    }
)

ground_truth["ground_truth_record_count"] = (
    ground_truth["speed_record_count"]
    + ground_truth["rpm_record_count"]
)

if ground_truth.duplicated(join_keys).any():
    raise ValueError(
        "Duplicate Ground-Truth 1-second keys detected."
    )


# --------------------------------------------------
# 3. Outer Join으로 결합 상태 확인
# --------------------------------------------------

alignment_check = can_1s.merge(
    ground_truth,
    on=join_keys,
    how="outer",
    indicator=True,
)


# --------------------------------------------------
# 4. 파일별 Match Coverage 계산
# --------------------------------------------------

summary_rows = []

group_columns = [
    "vehicle_id",
    "session_id",
    "source_file",
]

for group_values, group_df in alignment_check.groupby(
    group_columns,
    observed=True,
):
    vehicle_id, session_id, source_file = group_values

    can_windows = int(
        (group_df["_merge"] != "right_only").sum()
    )
    ground_truth_windows = int(
        (group_df["_merge"] != "left_only").sum()
    )
    matched_windows = int(
        (group_df["_merge"] == "both").sum()
    )
    unmatched_can_windows = int(
        (group_df["_merge"] == "left_only").sum()
    )
    unmatched_ground_truth_windows = int(
        (group_df["_merge"] == "right_only").sum()
    )

    coverage = (
        matched_windows / can_windows * 100
        if can_windows > 0
        else 0
    )

    summary_rows.append({
        "vehicle_id": vehicle_id,
        "session_id": session_id,
        "source_file": source_file,
        "can_windows": can_windows,
        "ground_truth_windows": ground_truth_windows,
        "matched_windows": matched_windows,
        "unmatched_can_windows": unmatched_can_windows,
        "unmatched_ground_truth_windows":
            unmatched_ground_truth_windows,
        "match_coverage_pct": round(coverage, 2),
    })


summary = pd.DataFrame(summary_rows)

total_can = len(can_1s)
total_ground_truth = len(ground_truth)
total_matched = int(
    (alignment_check["_merge"] == "both").sum()
)
total_unmatched_can = int(
    (alignment_check["_merge"] == "left_only").sum()
)
total_unmatched_ground_truth = int(
    (alignment_check["_merge"] == "right_only").sum()
)

overall_coverage = (
    total_matched / total_can * 100
    if total_can > 0
    else 0
)

overall_row = pd.DataFrame([{
    "vehicle_id": "ALL",
    "session_id": "ALL",
    "source_file": "ALL_FILES",
    "can_windows": total_can,
    "ground_truth_windows": total_ground_truth,
    "matched_windows": total_matched,
    "unmatched_can_windows": total_unmatched_can,
    "unmatched_ground_truth_windows":
        total_unmatched_ground_truth,
    "match_coverage_pct": round(overall_coverage, 2),
}])

summary = pd.concat(
    [summary, overall_row],
    ignore_index=True,
)


# --------------------------------------------------
# 5. 실제 분석용 Inner Join 데이터 생성
# --------------------------------------------------

aligned = alignment_check.loc[
    alignment_check["_merge"] == "both"
].drop(columns="_merge")

aligned = aligned.sort_values(join_keys).reset_index(drop=True)

if aligned.duplicated(join_keys).any():
    raise ValueError("Duplicate aligned keys detected.")


# --------------------------------------------------
# 6. 결과 저장
# --------------------------------------------------

ALIGNED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

aligned.to_csv(ALIGNED_OUTPUT, index=False)
summary.to_csv(SUMMARY_OUTPUT, index=False)


# --------------------------------------------------
# 7. 최종 결과 출력
# --------------------------------------------------

print("\nTimestamp alignment summary:")
print(summary.to_string(index=False))

print("\nAligned label distribution:")
print(aligned["true_state"].value_counts(dropna=False))

print("\nQuality checks:")
print("CAN 1-second duplicate keys:", can_1s.duplicated(join_keys).sum())
print(
    "Ground-Truth duplicate keys:",
    ground_truth.duplicated(join_keys).sum(),
)
print(
    "Aligned duplicate keys:",
    aligned.duplicated(join_keys).sum(),
)
print("Final aligned rows:", len(aligned))

print(f"\nSaved to: {CAN_1S_OUTPUT}")
print(f"Saved to: {ALIGNED_OUTPUT}")
print(f"Saved to: {SUMMARY_OUTPUT}")
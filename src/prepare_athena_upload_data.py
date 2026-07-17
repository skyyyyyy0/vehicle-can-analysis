from pathlib import Path
import re

import pandas as pd


INPUT_FILES = {
    "imu_features_1s": Path(
        "data/processed/imu_features_1s.csv"
    ),
    "ground_truth_1s": Path(
        "data/processed/ground_truth_processed.csv"
    ),
}

OUTPUT_DIR = Path(
    "data/processed/athena_upload"
)

AUDIT_PATH = Path(
    "outputs/validation/"
    "athena_upload_security_check.csv"
)

KEY_COLUMNS = [
    "vehicle_id",
    "session_id",
    "source_file",
    "timestamp_1s",
]

PROHIBITED_COLUMN_PATTERN = re.compile(
    r"vin|serial|device|plate|registration|"
    r"driver|customer|company|email|phone|"
    r"address|password|access_key|secret",
    re.IGNORECASE,
)

SENSITIVE_VALUE_PATTERNS = {
    "s3_uri": re.compile(
        r"s3://",
        re.IGNORECASE,
    ),
    "aws_access_key": re.compile(
        r"AKIA[0-9A-Z]{16}"
    ),
    "local_user_path": re.compile(
        r"/Users/[^/\s]+"
    ),
    "email": re.compile(
        r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"
    ),
    "possible_vin": re.compile(
        r"\b[A-HJ-NPR-Z0-9]{17}\b"
    ),
    "possible_korean_plate": re.compile(
        r"\b\d{2,3}[가-힣]\d{4}\b"
    ),
    "raw_mf4_reference": re.compile(
        r"\.mf4\b",
        re.IGNORECASE,
    ),
}


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

dataframes = {}

for dataset_name, input_path in INPUT_FILES.items():
    if not input_path.exists():
        raise FileNotFoundError(
            f"Missing input file: {input_path}"
        )

    df = pd.read_csv(input_path)

    missing_keys = (
        set(KEY_COLUMNS) - set(df.columns)
    )

    if missing_keys:
        raise ValueError(
            f"{dataset_name} missing keys: "
            f"{sorted(missing_keys)}"
        )

    prohibited_columns = [
        column
        for column in df.columns
        if PROHIBITED_COLUMN_PATTERN.search(column)
    ]

    if prohibited_columns:
        raise ValueError(
            f"{dataset_name} contains prohibited "
            f"columns: {prohibited_columns}"
        )

    dataframes[dataset_name] = df.copy()

# 두 파일에 동일한 익명화 Mapping 적용
vehicle_values = sorted({
    value
    for df in dataframes.values()
    for value in df["vehicle_id"].dropna().unique()
})

session_values = sorted({
    value
    for df in dataframes.values()
    for value in df["session_id"].dropna().unique()
})

source_file_values = sorted({
    value
    for df in dataframes.values()
    for value in df["source_file"].dropna().unique()
})

vehicle_map = {
    value: f"VEH_{index:02d}"
    for index, value in enumerate(
        vehicle_values,
        start=1,
    )
}

session_map = {
    value: f"SES_{index:02d}"
    for index, value in enumerate(
        session_values,
        start=1,
    )
}

source_file_map = {
    value: f"FILE_{index:03d}"
    for index, value in enumerate(
        source_file_values,
        start=1,
    )
}

audit_rows = []

for dataset_name, df in dataframes.items():
    df["vehicle_id"] = (
        df["vehicle_id"].map(vehicle_map)
    )

    df["session_id"] = (
        df["session_id"].map(session_map)
    )

    df["source_file"] = (
        df["source_file"].map(source_file_map)
    )

    timestamp = pd.to_datetime(
        df["timestamp_1s"],
        utc=True,
        errors="coerce",
    )

    invalid_timestamp_count = int(
        timestamp.isna().sum()
    )

    df["timestamp_1s"] = timestamp.dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    key_missing_count = int(
        df[KEY_COLUMNS].isna().sum().sum()
    )

    duplicate_key_count = int(
        df.duplicated(KEY_COLUMNS).sum()
    )

    text_values = "\n".join(
        df.astype(str)
        .to_numpy()
        .flatten()
        .tolist()
    )

    sensitive_hits = [
        pattern_name
        for pattern_name, pattern
        in SENSITIVE_VALUE_PATTERNS.items()
        if pattern.search(text_values)
    ]

    vehicle_format_valid = bool(
        df["vehicle_id"]
        .str.fullmatch(r"VEH_\d{2}")
        .all()
    )

    session_format_valid = bool(
        df["session_id"]
        .str.fullmatch(r"SES_\d{2}")
        .all()
    )

    source_file_format_valid = bool(
        df["source_file"]
        .str.fullmatch(r"FILE_\d{3}")
        .all()
    )

    status = (
        "PASS"
        if (
            invalid_timestamp_count == 0
            and key_missing_count == 0
            and duplicate_key_count == 0
            and not sensitive_hits
            and vehicle_format_valid
            and session_format_valid
            and source_file_format_valid
        )
        else "FAIL"
    )

    output_path = (
        OUTPUT_DIR / f"{dataset_name}.csv"
    )

    if status == "PASS":
        df.to_csv(
            output_path,
            index=False,
        )

    audit_rows.append({
        "dataset_name": dataset_name,
        "status": status,
        "row_count": len(df),
        "column_count": len(df.columns),
        "invalid_timestamp_count":
            invalid_timestamp_count,
        "key_missing_count":
            key_missing_count,
        "duplicate_key_count":
            duplicate_key_count,
        "sensitive_pattern_hits": (
            ", ".join(sensitive_hits)
            if sensitive_hits else "None"
        ),
        "vehicle_id_anonymized":
            vehicle_format_valid,
        "session_id_anonymized":
            session_format_valid,
        "source_file_anonymized":
            source_file_format_valid,
        "output_path": str(output_path),
    })

audit = pd.DataFrame(audit_rows)

audit.to_csv(
    AUDIT_PATH,
    index=False,
)

print("\nAthena upload security check:")
print(
    audit.to_string(index=False)
)

if not (audit["status"] == "PASS").all():
    raise ValueError(
        "Security check failed. "
        "Do not upload the files to S3."
    )

print("\nUpload-ready files:")
print(
    OUTPUT_DIR / "imu_features_1s.csv"
)
print(
    OUTPUT_DIR / "ground_truth_1s.csv"
)

print("\nSecurity audit:")
print(AUDIT_PATH)
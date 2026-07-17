WITH imu_ranked AS (
    SELECT
        *,
        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc,

        ROW_NUMBER() OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file,
                timestamp_1s
            ORDER BY timestamp_1s
        ) AS duplicate_row_number

    FROM vehicle_can_validation.imu_features_1s
),

ground_truth_ranked AS (
    SELECT
        *,
        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc,

        ROW_NUMBER() OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file,
                timestamp_1s
            ORDER BY timestamp_1s
        ) AS duplicate_row_number

    FROM vehicle_can_validation.ground_truth_1s
),

quality_summary AS (
    SELECT
        'imu_features_1s' AS dataset_name,

        COUNT(*) AS total_rows,
        COUNT(DISTINCT vehicle_id) AS vehicle_count,
        COUNT(DISTINCT session_id) AS session_count,
        COUNT(DISTINCT source_file) AS source_file_count,

        MIN(timestamp_utc) AS min_timestamp_utc,
        MAX(timestamp_utc) AS max_timestamp_utc,

        COUNT_IF(
            duplicate_row_number > 1
        ) AS duplicate_key_count,

        COUNT_IF(
            vehicle_id IS NULL
            OR TRIM(vehicle_id) = ''
            OR session_id IS NULL
            OR TRIM(session_id) = ''
            OR source_file IS NULL
            OR TRIM(source_file) = ''
            OR timestamp_1s IS NULL
            OR TRIM(timestamp_1s) = ''
        ) AS missing_key_count,

        MIN(imu_valid_ratio)
            AS imu_valid_ratio_min,

        AVG(imu_valid_ratio)
            AS imu_valid_ratio_mean,

        MAX(imu_valid_ratio)
            AS imu_valid_ratio_max,

        COUNT_IF(
            imu_valid_ratio < 1
        ) AS imu_valid_ratio_below_1_count,

        COUNT_IF(
            imu_valid_ratio IS NULL
            OR imu_valid_ratio < 0
            OR imu_valid_ratio > 1
        ) AS imu_valid_ratio_invalid_count,

        COUNT_IF(
            angular_rate_magnitude_mean IS NULL
        ) AS primary_feature_null_count,

        ROUND(
            100.0 * COUNT_IF(
                angular_rate_magnitude_mean IS NULL
            ) / NULLIF(COUNT(*), 0),
            4
        ) AS primary_feature_null_pct,

        MIN(angular_rate_magnitude_mean)
            AS primary_feature_min,

        MAX(angular_rate_magnitude_mean)
            AS primary_feature_max,

        CAST(NULL AS BIGINT)
            AS speed_null_count,

        CAST(NULL AS DOUBLE)
            AS speed_null_pct,

        CAST(NULL AS DOUBLE)
            AS speed_min_kmh,

        CAST(NULL AS DOUBLE)
            AS speed_max_kmh,

        CAST(NULL AS BIGINT)
            AS rpm_null_count,

        CAST(NULL AS DOUBLE)
            AS rpm_null_pct,

        CAST(NULL AS DOUBLE)
            AS rpm_min,

        CAST(NULL AS DOUBLE)
            AS rpm_max,

        CAST(NULL AS BIGINT)
            AS moving_count,

        CAST(NULL AS BIGINT)
            AS idle_count,

        CAST(NULL AS BIGINT)
            AS ambiguous_count,

        CAST(NULL AS BIGINT)
            AS engine_off_candidate_count

    FROM imu_ranked

    UNION ALL

    SELECT
        'ground_truth_1s' AS dataset_name,

        COUNT(*) AS total_rows,
        COUNT(DISTINCT vehicle_id) AS vehicle_count,
        COUNT(DISTINCT session_id) AS session_count,
        COUNT(DISTINCT source_file) AS source_file_count,

        MIN(timestamp_utc) AS min_timestamp_utc,
        MAX(timestamp_utc) AS max_timestamp_utc,

        COUNT_IF(
            duplicate_row_number > 1
        ) AS duplicate_key_count,

        COUNT_IF(
            vehicle_id IS NULL
            OR TRIM(vehicle_id) = ''
            OR session_id IS NULL
            OR TRIM(session_id) = ''
            OR source_file IS NULL
            OR TRIM(source_file) = ''
            OR timestamp_1s IS NULL
            OR TRIM(timestamp_1s) = ''
        ) AS missing_key_count,

        CAST(NULL AS DOUBLE)
            AS imu_valid_ratio_min,

        CAST(NULL AS DOUBLE)
            AS imu_valid_ratio_mean,

        CAST(NULL AS DOUBLE)
            AS imu_valid_ratio_max,

        CAST(NULL AS BIGINT)
            AS imu_valid_ratio_below_1_count,

        CAST(NULL AS BIGINT)
            AS imu_valid_ratio_invalid_count,

        CAST(NULL AS BIGINT)
            AS primary_feature_null_count,

        CAST(NULL AS DOUBLE)
            AS primary_feature_null_pct,

        CAST(NULL AS DOUBLE)
            AS primary_feature_min,

        CAST(NULL AS DOUBLE)
            AS primary_feature_max,

        COUNT_IF(
            vehicle_speed_kmh IS NULL
        ) AS speed_null_count,

        ROUND(
            100.0 * COUNT_IF(
                vehicle_speed_kmh IS NULL
            ) / NULLIF(COUNT(*), 0),
            4
        ) AS speed_null_pct,

        MIN(vehicle_speed_kmh)
            AS speed_min_kmh,

        MAX(vehicle_speed_kmh)
            AS speed_max_kmh,

        COUNT_IF(
            engine_rpm IS NULL
        ) AS rpm_null_count,

        ROUND(
            100.0 * COUNT_IF(
                engine_rpm IS NULL
            ) / NULLIF(COUNT(*), 0),
            4
        ) AS rpm_null_pct,

        MIN(engine_rpm)
            AS rpm_min,

        MAX(engine_rpm)
            AS rpm_max,

        COUNT_IF(
            ground_truth_state = 'moving'
        ) AS moving_count,

        COUNT_IF(
            ground_truth_state = 'idle'
        ) AS idle_count,

        COUNT_IF(
            ground_truth_state = 'ambiguous'
        ) AS ambiguous_count,

        COUNT_IF(
            ground_truth_state
            = 'engine_off_candidate'
        ) AS engine_off_candidate_count

    FROM ground_truth_ranked
)

SELECT
    *,

    CASE
        WHEN duplicate_key_count = 0
         AND missing_key_count = 0
         AND COALESCE(
             imu_valid_ratio_invalid_count,
             0
         ) = 0
         AND COALESCE(
             primary_feature_null_count,
             0
         ) = 0
         AND COALESCE(
             speed_null_count,
             0
         ) = 0
         AND COALESCE(
             rpm_null_count,
             0
         ) = 0
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS overall_status

FROM quality_summary
ORDER BY dataset_name;


-- Timestamp Gap and File-Boundary Checks


WITH all_timestamps AS (
    SELECT
        'imu_features_1s' AS dataset_name,
        vehicle_id,
        session_id,
        source_file,
        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc

    FROM vehicle_can_validation.imu_features_1s

    UNION ALL

    SELECT
        'ground_truth_1s' AS dataset_name,
        vehicle_id,
        session_id,
        source_file,
        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc

    FROM vehicle_can_validation.ground_truth_1s
),

ordered_timestamps AS (
    SELECT
        *,

        LAG(timestamp_utc) OVER (
            PARTITION BY
                dataset_name,
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_timestamp_utc,

        ROW_NUMBER() OVER (
            PARTITION BY
                dataset_name,
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS first_row_number,

        ROW_NUMBER() OVER (
            PARTITION BY
                dataset_name,
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc DESC
        ) AS last_row_number

    FROM all_timestamps
),

within_file_summary AS (
    SELECT
        dataset_name,
        vehicle_id,
        session_id,
        source_file,

        MIN(timestamp_utc)
            AS first_timestamp_utc,

        MAX(timestamp_utc)
            AS last_timestamp_utc,

        COUNT(*) AS window_count,

        COUNT_IF(
            previous_timestamp_utc IS NOT NULL
            AND date_diff(
                'second',
                previous_timestamp_utc,
                timestamp_utc
            ) > 1
        ) AS gap_gt_1s_count,

        COUNT_IF(
            previous_timestamp_utc IS NOT NULL
            AND date_diff(
                'second',
                previous_timestamp_utc,
                timestamp_utc
            ) <= 0
        ) AS non_positive_gap_count,

        COALESCE(
            MAX(
                CASE
                    WHEN previous_timestamp_utc
                         IS NOT NULL
                    THEN date_diff(
                        'second',
                        previous_timestamp_utc,
                        timestamp_utc
                    )
                END
            ),
            0
        ) AS max_gap_seconds

    FROM ordered_timestamps

    GROUP BY
        dataset_name,
        vehicle_id,
        session_id,
        source_file
),

file_ranges AS (
    SELECT
        dataset_name,
        vehicle_id,
        session_id,
        source_file,

        MAX(
            CASE
                WHEN first_row_number = 1
                THEN timestamp_utc
            END
        ) AS first_timestamp_utc,

        MAX(
            CASE
                WHEN last_row_number = 1
                THEN timestamp_utc
            END
        ) AS last_timestamp_utc,

        COUNT(*) AS window_count

    FROM ordered_timestamps

    GROUP BY
        dataset_name,
        vehicle_id,
        session_id,
        source_file
),

file_boundaries AS (
    SELECT
        *,

        LAG(source_file) OVER (
            PARTITION BY
                dataset_name,
                vehicle_id,
                session_id
            ORDER BY first_timestamp_utc
        ) AS previous_source_file,

        LAG(last_timestamp_utc) OVER (
            PARTITION BY
                dataset_name,
                vehicle_id,
                session_id
            ORDER BY first_timestamp_utc
        ) AS previous_file_last_timestamp_utc

    FROM file_ranges
)

SELECT
    dataset_name,
    'within_file' AS check_type,
    vehicle_id,
    session_id,

    CAST(NULL AS VARCHAR)
        AS previous_source_file,

    source_file,
    first_timestamp_utc,
    last_timestamp_utc,
    window_count,
    gap_gt_1s_count,
    non_positive_gap_count,
    max_gap_seconds,

    CAST(NULL AS BIGINT)
        AS boundary_gap_seconds,

    CASE
        WHEN gap_gt_1s_count = 0
         AND non_positive_gap_count = 0
         AND max_gap_seconds <= 1
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS check_status

FROM within_file_summary

UNION ALL

SELECT
    dataset_name,
    'file_boundary' AS check_type,
    vehicle_id,
    session_id,
    previous_source_file,
    source_file,
    first_timestamp_utc,
    last_timestamp_utc,
    window_count,

    CAST(NULL AS BIGINT)
        AS gap_gt_1s_count,

    CAST(NULL AS BIGINT)
        AS non_positive_gap_count,

    CAST(NULL AS BIGINT)
        AS max_gap_seconds,

    CASE
        WHEN previous_file_last_timestamp_utc
             IS NULL
        THEN NULL

        ELSE date_diff(
            'second',
            previous_file_last_timestamp_utc,
            first_timestamp_utc
        )
    END AS boundary_gap_seconds,

    CASE
        WHEN previous_file_last_timestamp_utc
             IS NULL
        THEN 'FIRST_FILE'

        WHEN date_diff(
            'second',
            previous_file_last_timestamp_utc,
            first_timestamp_utc
        ) = 1
        THEN 'PASS'

        WHEN date_diff(
            'second',
            previous_file_last_timestamp_utc,
            first_timestamp_utc
        ) > 1
        THEN 'GAP'

        ELSE 'OVERLAP_OR_DUPLICATE'
    END AS check_status

FROM file_boundaries

ORDER BY
    dataset_name,
    check_type,
    first_timestamp_utc;
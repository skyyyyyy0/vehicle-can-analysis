-- IMU–Ground Truth Alignment Coverage

WITH imu AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        timestamp_1s,

        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc,

        imu_record_count,
        imu_valid_count,
        imu_valid_ratio,
        angular_rate_magnitude_mean,
        angular_rate_magnitude_std,
        angular_rate_magnitude_max,
        angular_rate_magnitude_rms,
        acceleration_deviation_mean,
        acceleration_deviation_std,
        acceleration_deviation_max

    FROM vehicle_can_validation.imu_features_1s
),

ground_truth AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        timestamp_1s,

        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc,

        engine_rpm,
        vehicle_speed_kmh,
        rpm_record_count,
        speed_record_count,

        ground_truth_state
            AS python_ground_truth_state,

        CASE
            WHEN vehicle_speed_kmh >= 5
             AND engine_rpm >= 500
            THEN 'moving'

            WHEN vehicle_speed_kmh < 1
             AND engine_rpm >= 500
            THEN 'idle'

            WHEN vehicle_speed_kmh < 1
             AND engine_rpm <= 100
            THEN 'engine_off_candidate'

            ELSE 'ambiguous'
        END AS sql_ground_truth_state

    FROM vehicle_can_validation.ground_truth_1s
),

imu_left_join AS (
    SELECT
        i.vehicle_id,
        i.session_id,
        i.source_file,
        i.timestamp_1s,

        g.timestamp_1s
            AS matched_ground_truth_timestamp

    FROM imu AS i

    LEFT JOIN ground_truth AS g
        ON i.vehicle_id = g.vehicle_id
       AND i.session_id = g.session_id
       AND i.source_file = g.source_file
       AND i.timestamp_1s = g.timestamp_1s
),

ground_truth_left_join AS (
    SELECT
        g.vehicle_id,
        g.session_id,
        g.source_file,
        g.timestamp_1s,

        i.timestamp_1s
            AS matched_imu_timestamp

    FROM ground_truth AS g

    LEFT JOIN imu AS i
        ON g.vehicle_id = i.vehicle_id
       AND g.session_id = i.session_id
       AND g.source_file = i.source_file
       AND g.timestamp_1s = i.timestamp_1s
),

matched_data AS (
    SELECT
        i.vehicle_id,
        i.session_id,
        i.source_file,
        i.timestamp_1s,

        g.python_ground_truth_state,
        g.sql_ground_truth_state

    FROM imu AS i

    INNER JOIN ground_truth AS g
        ON i.vehicle_id = g.vehicle_id
       AND i.session_id = g.session_id
       AND i.source_file = g.source_file
       AND i.timestamp_1s = g.timestamp_1s
),

file_keys AS (
    SELECT DISTINCT
        vehicle_id,
        session_id,
        source_file
    FROM imu

    UNION

    SELECT DISTINCT
        vehicle_id,
        session_id,
        source_file
    FROM ground_truth
),

imu_counts AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        COUNT(*) AS imu_windows
    FROM imu
    GROUP BY
        vehicle_id,
        session_id,
        source_file
),

ground_truth_counts AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        COUNT(*) AS ground_truth_windows
    FROM ground_truth
    GROUP BY
        vehicle_id,
        session_id,
        source_file
),

unmatched_imu_counts AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,

        COUNT_IF(
            matched_ground_truth_timestamp IS NULL
        ) AS unmatched_imu_windows

    FROM imu_left_join

    GROUP BY
        vehicle_id,
        session_id,
        source_file
),

unmatched_ground_truth_counts AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,

        COUNT_IF(
            matched_imu_timestamp IS NULL
        ) AS unmatched_ground_truth_windows

    FROM ground_truth_left_join

    GROUP BY
        vehicle_id,
        session_id,
        source_file
),

matched_counts AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,

        COUNT(*) AS matched_windows,

        COUNT_IF(
            python_ground_truth_state
            <> sql_ground_truth_state
        ) AS label_mismatch_count,

        COUNT_IF(
            sql_ground_truth_state = 'moving'
        ) AS moving_count,

        COUNT_IF(
            sql_ground_truth_state = 'idle'
        ) AS idle_count,

        COUNT_IF(
            sql_ground_truth_state = 'ambiguous'
        ) AS ambiguous_count,

        COUNT_IF(
            sql_ground_truth_state
            = 'engine_off_candidate'
        ) AS engine_off_candidate_count

    FROM matched_data

    GROUP BY
        vehicle_id,
        session_id,
        source_file
),

file_summary AS (
    SELECT
        k.vehicle_id,
        k.session_id,
        k.source_file,

        COALESCE(
            i.imu_windows,
            0
        ) AS imu_windows,

        COALESCE(
            g.ground_truth_windows,
            0
        ) AS ground_truth_windows,

        COALESCE(
            m.matched_windows,
            0
        ) AS matched_windows,

        COALESCE(
            ui.unmatched_imu_windows,
            0
        ) AS unmatched_imu_windows,

        COALESCE(
            ug.unmatched_ground_truth_windows,
            0
        ) AS unmatched_ground_truth_windows,

        ROUND(
            100.0 * COALESCE(
                m.matched_windows,
                0
            ) / NULLIF(
                COALESCE(i.imu_windows, 0),
                0
            ),
            2
        ) AS match_coverage_pct,

        COALESCE(
            m.label_mismatch_count,
            0
        ) AS label_mismatch_count,

        COALESCE(
            m.moving_count,
            0
        ) AS moving_count,

        COALESCE(
            m.idle_count,
            0
        ) AS idle_count,

        COALESCE(
            m.ambiguous_count,
            0
        ) AS ambiguous_count,

        COALESCE(
            m.engine_off_candidate_count,
            0
        ) AS engine_off_candidate_count

    FROM file_keys AS k

    LEFT JOIN imu_counts AS i
        ON k.vehicle_id = i.vehicle_id
       AND k.session_id = i.session_id
       AND k.source_file = i.source_file

    LEFT JOIN ground_truth_counts AS g
        ON k.vehicle_id = g.vehicle_id
       AND k.session_id = g.session_id
       AND k.source_file = g.source_file

    LEFT JOIN matched_counts AS m
        ON k.vehicle_id = m.vehicle_id
       AND k.session_id = m.session_id
       AND k.source_file = m.source_file

    LEFT JOIN unmatched_imu_counts AS ui
        ON k.vehicle_id = ui.vehicle_id
       AND k.session_id = ui.session_id
       AND k.source_file = ui.source_file

    LEFT JOIN unmatched_ground_truth_counts AS ug
        ON k.vehicle_id = ug.vehicle_id
       AND k.session_id = ug.session_id
       AND k.source_file = ug.source_file
)

SELECT
    vehicle_id,
    session_id,
    source_file,
    imu_windows,
    ground_truth_windows,
    matched_windows,
    unmatched_imu_windows,
    unmatched_ground_truth_windows,
    match_coverage_pct,
    label_mismatch_count,
    moving_count,
    idle_count,
    ambiguous_count,
    engine_off_candidate_count,

    CASE
        WHEN unmatched_imu_windows = 0
         AND unmatched_ground_truth_windows = 0
        THEN 'COMPLETE'
        ELSE 'PARTIAL'
    END AS coverage_status,

    CASE
        WHEN label_mismatch_count = 0
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS label_status

FROM file_summary

UNION ALL

SELECT
    'ALL' AS vehicle_id,
    'ALL' AS session_id,
    'ALL_FILES' AS source_file,

    SUM(imu_windows) AS imu_windows,
    SUM(ground_truth_windows)
        AS ground_truth_windows,
    SUM(matched_windows) AS matched_windows,
    SUM(unmatched_imu_windows)
        AS unmatched_imu_windows,
    SUM(unmatched_ground_truth_windows)
        AS unmatched_ground_truth_windows,

    ROUND(
        100.0 * SUM(matched_windows)
        / NULLIF(SUM(imu_windows), 0),
        2
    ) AS match_coverage_pct,

    SUM(label_mismatch_count)
        AS label_mismatch_count,
    SUM(moving_count) AS moving_count,
    SUM(idle_count) AS idle_count,
    SUM(ambiguous_count) AS ambiguous_count,
    SUM(engine_off_candidate_count)
        AS engine_off_candidate_count,

    CASE
        WHEN SUM(unmatched_imu_windows) = 0
         AND SUM(unmatched_ground_truth_windows) = 0
        THEN 'COMPLETE'
        ELSE 'PARTIAL'
    END AS coverage_status,

    CASE
        WHEN SUM(label_mismatch_count) = 0
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS label_status

FROM file_summary

ORDER BY source_file;

-- SQL Aligned Dataset Sample

WITH imu AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        timestamp_1s,

        from_iso8601_timestamp(
            timestamp_1s
        ) AS timestamp_utc,

        imu_record_count,
        imu_valid_count,
        imu_valid_ratio,

        acceleration_magnitude_mean,
        acceleration_magnitude_std,
        acceleration_magnitude_max,

        acceleration_deviation_mean,
        acceleration_deviation_std,
        acceleration_deviation_max,

        angular_rate_magnitude_mean,
        angular_rate_magnitude_std,
        angular_rate_magnitude_max,
        angular_rate_magnitude_rms

    FROM vehicle_can_validation.imu_features_1s
),

ground_truth AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        timestamp_1s,

        engine_rpm,
        vehicle_speed_kmh,
        rpm_record_count,
        speed_record_count,

        ground_truth_state
            AS python_ground_truth_state,

        CASE
            WHEN vehicle_speed_kmh >= 5
             AND engine_rpm >= 500
            THEN 'moving'

            WHEN vehicle_speed_kmh < 1
             AND engine_rpm >= 500
            THEN 'idle'

            WHEN vehicle_speed_kmh < 1
             AND engine_rpm <= 100
            THEN 'engine_off_candidate'

            ELSE 'ambiguous'
        END AS sql_ground_truth_state

    FROM vehicle_can_validation.ground_truth_1s
),

aligned AS (
    SELECT
        i.vehicle_id,
        i.session_id,
        i.source_file,
        i.timestamp_1s,
        i.timestamp_utc,

        i.imu_record_count,
        i.imu_valid_count,
        i.imu_valid_ratio,

        i.acceleration_magnitude_mean,
        i.acceleration_magnitude_std,
        i.acceleration_magnitude_max,

        i.acceleration_deviation_mean,
        i.acceleration_deviation_std,
        i.acceleration_deviation_max,

        i.angular_rate_magnitude_mean,
        i.angular_rate_magnitude_std,
        i.angular_rate_magnitude_max,
        i.angular_rate_magnitude_rms,

        g.engine_rpm,
        g.vehicle_speed_kmh,
        g.rpm_record_count,
        g.speed_record_count,

        g.python_ground_truth_state,
        g.sql_ground_truth_state,

        CASE
            WHEN g.python_ground_truth_state
                 = g.sql_ground_truth_state
            THEN TRUE
            ELSE FALSE
        END AS label_match

    FROM imu AS i

    INNER JOIN ground_truth AS g
        ON i.vehicle_id = g.vehicle_id
       AND i.session_id = g.session_id
       AND i.source_file = g.source_file
       AND i.timestamp_1s = g.timestamp_1s
)

SELECT *
FROM aligned
ORDER BY
    vehicle_id,
    session_id,
    source_file,
    timestamp_utc
LIMIT 20;
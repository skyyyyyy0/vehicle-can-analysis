-- Build Binary Analysis View

CREATE OR REPLACE VIEW
vehicle_can_validation.imu_binary_analysis AS

WITH imu AS (
    SELECT
        vehicle_id,
        session_id,
        source_file,
        timestamp_1s,

        date_parse(
            timestamp_1s,
            '%Y-%m-%dT%H:%i:%sZ'
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
        END AS true_state

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

        i.angular_rate_magnitude_mean,
        i.angular_rate_magnitude_std,
        i.angular_rate_magnitude_max,
        i.angular_rate_magnitude_rms,

        i.acceleration_deviation_mean,
        i.acceleration_deviation_std,
        i.acceleration_deviation_max,

        g.engine_rpm,
        g.vehicle_speed_kmh,
        g.rpm_record_count,
        g.speed_record_count,

        g.python_ground_truth_state,
        g.true_state

    FROM imu AS i

    INNER JOIN ground_truth AS g
        ON i.vehicle_id = g.vehicle_id
       AND i.session_id = g.session_id
       AND i.source_file = g.source_file
       AND i.timestamp_1s = g.timestamp_1s
),

binary_ranked AS (
    SELECT
        *,

        CASE
            WHEN true_state = 'moving'
            THEN 1
            ELSE 0
        END AS y_true,

        ROW_NUMBER() OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS binary_row_number,

        COUNT(*) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
        ) AS binary_file_count

    FROM aligned

    WHERE true_state IN (
        'moving',
        'idle'
    )
)

SELECT
    *,

    CASE
        WHEN source_file = 'FILE_001'
         AND binary_row_number <= CAST(
             FLOOR(binary_file_count * 0.70)
             AS BIGINT
         )
        THEN 'development'

        WHEN source_file = 'FILE_001'
        THEN 'within_session_validation'

        WHEN source_file = 'FILE_002'
        THEN 'idle_stress_test'

        WHEN source_file = 'FILE_003'
        THEN 'transition_diagnostic'

        ELSE 'unassigned'
    END AS split_role

FROM binary_ranked;

-- Binary Analysis Dataset Summary

WITH split_summary AS (
    SELECT
        split_role,
        COUNT(*) AS total_windows,

        COUNT_IF(
            true_state = 'moving'
        ) AS moving_windows,

        COUNT_IF(
            true_state = 'idle'
        ) AS idle_windows,

        ROUND(
            100.0 * COUNT_IF(
                true_state = 'moving'
            ) / NULLIF(COUNT(*), 0),
            2
        ) AS moving_ratio_pct,

        ROUND(
            100.0 * COUNT_IF(
                true_state = 'idle'
            ) / NULLIF(COUNT(*), 0),
            2
        ) AS idle_ratio_pct,

        MIN(timestamp_utc)
            AS first_timestamp_utc,

        MAX(timestamp_utc)
            AS last_timestamp_utc,

        MIN(angular_rate_magnitude_mean)
            AS feature_min,

        AVG(angular_rate_magnitude_mean)
            AS feature_mean,

        MAX(angular_rate_magnitude_mean)
            AS feature_max

    FROM vehicle_can_validation.imu_binary_analysis

    GROUP BY split_role
)

SELECT *
FROM split_summary

UNION ALL

SELECT
    'all_binary' AS split_role,
    COUNT(*) AS total_windows,

    COUNT_IF(
        true_state = 'moving'
    ) AS moving_windows,

    COUNT_IF(
        true_state = 'idle'
    ) AS idle_windows,

    ROUND(
        100.0 * COUNT_IF(
            true_state = 'moving'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS moving_ratio_pct,

    ROUND(
        100.0 * COUNT_IF(
            true_state = 'idle'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS idle_ratio_pct,

    MIN(timestamp_utc)
        AS first_timestamp_utc,

    MAX(timestamp_utc)
        AS last_timestamp_utc,

    MIN(angular_rate_magnitude_mean)
        AS feature_min,

    AVG(angular_rate_magnitude_mean)
        AS feature_mean,

    MAX(angular_rate_magnitude_mean)
        AS feature_max

FROM vehicle_can_validation.imu_binary_analysis

ORDER BY split_role;
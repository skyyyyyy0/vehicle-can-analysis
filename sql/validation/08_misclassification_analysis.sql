WITH parameters AS (
    SELECT
        CAST(2.290542511310978 AS DOUBLE)
            AS selected_threshold
),

aligned_signals AS (
    SELECT
        imu.vehicle_id,
        imu.session_id,
        imu.source_file,

        date_parse(
            imu.timestamp_1s,
            '%Y-%m-%dT%H:%i:%sZ'
        ) AS timestamp_utc,

        imu.imu_record_count,
        imu.imu_valid_ratio,
        imu.acceleration_deviation_mean,
        imu.acceleration_deviation_max,
        imu.angular_rate_magnitude_mean,
        imu.angular_rate_magnitude_std,
        imu.angular_rate_magnitude_max,
        imu.angular_rate_magnitude_rms,

        ground.vehicle_speed_kmh,
        ground.engine_rpm,
        ground.speed_record_count,
        ground.rpm_record_count

    FROM vehicle_can_validation.imu_features_1s AS imu

    INNER JOIN vehicle_can_validation.ground_truth_1s AS ground
        ON imu.vehicle_id = ground.vehicle_id
       AND imu.session_id = ground.session_id
       AND imu.source_file = ground.source_file
       AND imu.timestamp_1s = ground.timestamp_1s
),

ordered_signals AS (
    SELECT
        *,

        LAG(timestamp_utc) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_timestamp_utc,

        LAG(vehicle_speed_kmh) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_speed_kmh,

        LEAD(vehicle_speed_kmh) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS next_speed_kmh,

        LAG(engine_rpm) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_engine_rpm,

        LEAD(engine_rpm) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS next_engine_rpm,

        LAG(angular_rate_magnitude_mean) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_angular_rate_mean

    FROM aligned_signals
),

scored AS (
    SELECT
        signals.*,
        analysis.split_role,
        analysis.y_true,
        parameters.selected_threshold,

        CASE
            WHEN signals.angular_rate_magnitude_mean
                 >= parameters.selected_threshold
            THEN 1
            ELSE 0
        END AS y_pred

    FROM vehicle_can_validation.imu_binary_analysis AS analysis

    INNER JOIN ordered_signals AS signals
        ON analysis.vehicle_id = signals.vehicle_id
       AND analysis.session_id = signals.session_id
       AND analysis.source_file = signals.source_file
       AND analysis.timestamp_utc = signals.timestamp_utc

    CROSS JOIN parameters
),

classified AS (
    SELECT
        *,

        CASE
            WHEN y_true = 1 AND y_pred = 1 THEN 'TP'
            WHEN y_true = 0 AND y_pred = 0 THEN 'TN'
            WHEN y_true = 0 AND y_pred = 1 THEN 'FP'
            WHEN y_true = 1 AND y_pred = 0 THEN 'FN'
        END AS classification_result

    FROM scored
),

misclassified AS (
    SELECT
        *,

        ABS(
            angular_rate_magnitude_mean
            - selected_threshold
        ) AS threshold_margin,

        vehicle_speed_kmh
        - previous_speed_kmh AS speed_change,

        engine_rpm
        - previous_engine_rpm AS rpm_change,

        angular_rate_magnitude_mean
        - previous_angular_rate_mean
            AS angular_rate_change,

        ABS(vehicle_speed_kmh - 5.0)
            AS moving_boundary_distance,

        CASE
            WHEN vehicle_speed_kmh >= 5
             AND vehicle_speed_kmh < 6
            THEN 1
            ELSE 0
        END AS near_speed_boundary_flag,

        CASE
            WHEN previous_speed_kmh IS NOT NULL
             AND (
                    (previous_speed_kmh < 5
                     AND vehicle_speed_kmh >= 5)
                 OR (previous_speed_kmh >= 5
                     AND vehicle_speed_kmh < 5)
             )
            THEN 1
            ELSE 0
        END AS state_transition_flag,

        CASE
            WHEN imu_record_count < 5
            THEN 1
            ELSE 0
        END AS low_imu_sample_flag

    FROM classified
    WHERE classification_result IN ('FP', 'FN')
)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY timestamp_utc
    ) AS error_sequence,

    RANK() OVER (
        PARTITION BY classification_result
        ORDER BY threshold_margin DESC
    ) AS error_severity_rank,

    vehicle_id,
    session_id,
    source_file,
    split_role,
    timestamp_utc,
    classification_result,
    y_true,
    y_pred,
    selected_threshold,

    angular_rate_magnitude_mean,
    angular_rate_magnitude_std,
    angular_rate_magnitude_max,
    angular_rate_magnitude_rms,
    threshold_margin,
    angular_rate_change,

    acceleration_deviation_mean,
    acceleration_deviation_max,

    vehicle_speed_kmh,
    previous_speed_kmh,
    next_speed_kmh,
    speed_change,
    moving_boundary_distance,
    near_speed_boundary_flag,
    state_transition_flag,

    engine_rpm,
    previous_engine_rpm,
    next_engine_rpm,
    rpm_change,

    imu_record_count,
    imu_valid_ratio,
    speed_record_count,
    rpm_record_count,
    low_imu_sample_flag

FROM misclassified
ORDER BY
    classification_result,
    error_severity_rank,
    timestamp_utc;

WITH parameters AS (
    SELECT
        CAST(2.290542511310978 AS DOUBLE)
            AS selected_threshold
),

aligned_signals AS (
    SELECT
        imu.vehicle_id,
        imu.session_id,
        imu.source_file,

        date_parse(
            imu.timestamp_1s,
            '%Y-%m-%dT%H:%i:%sZ'
        ) AS timestamp_utc,

        imu.imu_record_count,
        imu.angular_rate_magnitude_mean,
        ground.vehicle_speed_kmh,
        ground.engine_rpm

    FROM vehicle_can_validation.imu_features_1s AS imu

    INNER JOIN vehicle_can_validation.ground_truth_1s AS ground
        ON imu.vehicle_id = ground.vehicle_id
       AND imu.session_id = ground.session_id
       AND imu.source_file = ground.source_file
       AND imu.timestamp_1s = ground.timestamp_1s
),

ordered_signals AS (
    SELECT
        *,

        LAG(vehicle_speed_kmh) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_speed_kmh,

        LEAD(vehicle_speed_kmh) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS next_speed_kmh,

        LAG(engine_rpm) OVER (
            PARTITION BY
                vehicle_id,
                session_id,
                source_file
            ORDER BY timestamp_utc
        ) AS previous_engine_rpm

    FROM aligned_signals
),

classified AS (
    SELECT
        analysis.source_file,
        analysis.split_role,
        analysis.y_true,
        signals.timestamp_utc,
        signals.angular_rate_magnitude_mean,
        signals.vehicle_speed_kmh,
        signals.previous_speed_kmh,
        signals.next_speed_kmh,
        signals.engine_rpm,
        signals.previous_engine_rpm,
        signals.imu_record_count,
        parameters.selected_threshold,

        CASE
            WHEN signals.angular_rate_magnitude_mean
                 >= parameters.selected_threshold
            THEN 1
            ELSE 0
        END AS y_pred

    FROM vehicle_can_validation.imu_binary_analysis AS analysis

    INNER JOIN ordered_signals AS signals
        ON analysis.vehicle_id = signals.vehicle_id
       AND analysis.session_id = signals.session_id
       AND analysis.source_file = signals.source_file
       AND analysis.timestamp_utc = signals.timestamp_utc

    CROSS JOIN parameters
),

errors AS (
    SELECT
        *,

        CASE
            WHEN y_true = 0 AND y_pred = 1 THEN 'FP'
            WHEN y_true = 1 AND y_pred = 0 THEN 'FN'
        END AS classification_result,

        ABS(
            angular_rate_magnitude_mean
            - selected_threshold
        ) AS threshold_margin,

        ABS(
            engine_rpm - previous_engine_rpm
        ) AS absolute_rpm_change,

        CASE
            WHEN (
                previous_speed_kmh > 0
                AND previous_speed_kmh < 5
            )
            OR (
                next_speed_kmh > 0
                AND next_speed_kmh < 5
            )
            THEN 1
            ELSE 0
        END AS adjacent_low_speed_context_flag,

        CASE
            WHEN vehicle_speed_kmh >= 5
             AND vehicle_speed_kmh < 6
            THEN 1
            ELSE 0
        END AS near_speed_boundary_flag,

        CASE
            WHEN imu_record_count < 5
            THEN 1
            ELSE 0
        END AS low_imu_sample_flag

    FROM classified

    WHERE
        (y_true = 0 AND y_pred = 1)
        OR
        (y_true = 1 AND y_pred = 0)
),

error_summary AS (
    SELECT
        source_file,
        split_role,
        classification_result,
        COUNT(*) AS error_window_count,

        AVG(angular_rate_magnitude_mean)
            AS average_imu_activity,

        MIN(angular_rate_magnitude_mean)
            AS minimum_imu_activity,

        MAX(angular_rate_magnitude_mean)
            AS maximum_imu_activity,

        AVG(vehicle_speed_kmh)
            AS average_speed_kmh,

        AVG(threshold_margin)
            AS average_threshold_margin,

        AVG(absolute_rpm_change)
            AS average_absolute_rpm_change,

        MAX(absolute_rpm_change)
            AS maximum_absolute_rpm_change,

        COUNT_IF(
            adjacent_low_speed_context_flag = 1
        ) AS adjacent_low_speed_windows,

        COUNT_IF(
            near_speed_boundary_flag = 1
        ) AS near_speed_boundary_windows,

        COUNT_IF(
            low_imu_sample_flag = 1
        ) AS low_imu_sample_windows

    FROM errors

    GROUP BY
        source_file,
        split_role,
        classification_result
)

SELECT
    RANK() OVER (
        ORDER BY error_window_count DESC
    ) AS error_frequency_rank,

    source_file,
    split_role,
    classification_result,
    error_window_count,
    average_imu_activity,
    minimum_imu_activity,
    maximum_imu_activity,
    average_speed_kmh,
    average_threshold_margin,
    average_absolute_rpm_change,
    maximum_absolute_rpm_change,
    adjacent_low_speed_windows,
    near_speed_boundary_windows,
    low_imu_sample_windows

FROM error_summary
ORDER BY
    error_frequency_rank,
    classification_result;
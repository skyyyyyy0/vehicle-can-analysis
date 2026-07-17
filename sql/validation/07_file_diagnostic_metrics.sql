WITH parameters AS (
    SELECT
        CAST(2.290542511310978 AS DOUBLE)
            AS selected_threshold
),

predictions AS (
    SELECT
        analysis.source_file,
        analysis.split_role,
        analysis.y_true,
        analysis.angular_rate_magnitude_mean,
        parameters.selected_threshold,

        CASE
            WHEN analysis.angular_rate_magnitude_mean
                 >= parameters.selected_threshold
            THEN 1
            ELSE 0
        END AS y_pred

    FROM vehicle_can_validation.imu_binary_analysis AS analysis
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
    FROM predictions
),

file_summary AS (
    SELECT
        source_file,
        split_role,
        selected_threshold,
        COUNT(*) AS total_windows,

        COUNT_IF(y_true = 1) AS moving_windows,
        COUNT_IF(y_true = 0) AS idle_windows,

        COUNT_IF(y_pred = 1) AS predicted_moving_windows,
        COUNT_IF(y_pred = 0) AS predicted_idle_windows,

        COUNT_IF(
            classification_result = 'TP'
        ) AS true_positive,

        COUNT_IF(
            classification_result = 'TN'
        ) AS true_negative,

        COUNT_IF(
            classification_result = 'FP'
        ) AS false_positive,

        COUNT_IF(
            classification_result = 'FN'
        ) AS false_negative,

        COUNT_IF(
            classification_result IN ('FP', 'FN')
        ) AS misclassified_windows,

        MIN(angular_rate_magnitude_mean)
            AS feature_min,

        AVG(angular_rate_magnitude_mean)
            AS feature_mean,

        MAX(angular_rate_magnitude_mean)
            AS feature_max,

        AVG(
            CASE
                WHEN classification_result = 'FP'
                THEN angular_rate_magnitude_mean
            END
        ) AS false_positive_feature_mean,

        AVG(
            CASE
                WHEN classification_result = 'FN'
                THEN angular_rate_magnitude_mean
            END
        ) AS false_negative_feature_mean

    FROM classified
    GROUP BY
        source_file,
        split_role,
        selected_threshold
),

file_metrics AS (
    SELECT
        *,
        1.0 * misclassified_windows
        / NULLIF(total_windows, 0) AS error_rate,

        1.0 * false_positive
        / NULLIF(idle_windows, 0)
            AS false_positive_rate,

        1.0 * false_negative
        / NULLIF(moving_windows, 0)
            AS false_negative_rate

    FROM file_summary
)

SELECT
    RANK() OVER (
        ORDER BY
            misclassified_windows DESC,
            error_rate DESC,
            source_file,
            split_role
    ) AS error_rank,

    source_file,
    split_role,
    selected_threshold,
    total_windows,
    moving_windows,
    idle_windows,
    predicted_moving_windows,
    predicted_idle_windows,
    true_positive,
    true_negative,
    false_positive,
    false_negative,
    misclassified_windows,
    error_rate,
    false_positive_rate,
    false_negative_rate,
    feature_min,
    feature_mean,
    feature_max,
    false_positive_feature_mean,
    false_negative_feature_mean

FROM file_metrics
ORDER BY
    error_rank,
    source_file,
    split_role;
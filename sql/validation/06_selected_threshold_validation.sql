WITH parameters AS (
    SELECT
        CAST(2.290542511310978 AS DOUBLE)
            AS selected_threshold
),

predictions AS (
    SELECT
        analysis.split_role,
        analysis.y_true,
        parameters.selected_threshold,

        CASE
            WHEN analysis.angular_rate_magnitude_mean
                 >= parameters.selected_threshold
            THEN 1
            ELSE 0
        END AS y_pred

    FROM vehicle_can_validation.imu_binary_analysis AS analysis
    CROSS JOIN parameters

    WHERE analysis.split_role IN (
        'development',
        'within_session_validation',
        'idle_stress_test'
    )
),

confusion_counts AS (
    SELECT
        split_role,
        selected_threshold,
        COUNT(*) AS total_windows,
        COUNT_IF(y_true = 1) AS moving_windows,
        COUNT_IF(y_true = 0) AS idle_windows,

        COUNT_IF(
            y_true = 1 AND y_pred = 1
        ) AS true_positive,

        COUNT_IF(
            y_true = 0 AND y_pred = 0
        ) AS true_negative,

        COUNT_IF(
            y_true = 0 AND y_pred = 1
        ) AS false_positive,

        COUNT_IF(
            y_true = 1 AND y_pred = 0
        ) AS false_negative

    FROM predictions
    GROUP BY
        split_role,
        selected_threshold
),

metrics AS (
    SELECT
        *,
        1.0 * (
            true_positive + true_negative
        ) / NULLIF(total_windows, 0) AS accuracy,

        1.0 * true_positive
        / NULLIF(
            true_positive + false_positive,
            0
        ) AS moving_precision,

        1.0 * true_positive
        / NULLIF(
            true_positive + false_negative,
            0
        ) AS moving_recall,

        2.0 * true_positive
        / NULLIF(
            2 * true_positive
            + false_positive
            + false_negative,
            0
        ) AS moving_f1,

        1.0 * true_negative
        / NULLIF(
            true_negative + false_negative,
            0
        ) AS idle_precision,

        1.0 * true_negative
        / NULLIF(
            true_negative + false_positive,
            0
        ) AS idle_recall,

        2.0 * true_negative
        / NULLIF(
            2 * true_negative
            + false_positive
            + false_negative,
            0
        ) AS idle_f1,

        1.0 * false_positive
        / NULLIF(
            false_positive + true_negative,
            0
        ) AS false_positive_rate

    FROM confusion_counts
)

SELECT
    split_role,
    selected_threshold,
    total_windows,
    moving_windows,
    idle_windows,
    true_positive,
    true_negative,
    false_positive,
    false_negative,
    accuracy,
    moving_precision,
    moving_recall,
    moving_f1,
    idle_precision,
    idle_recall,
    idle_f1,

    CASE
        WHEN moving_windows > 0
         AND idle_windows > 0
        THEN (moving_f1 + idle_f1) / 2.0
        ELSE NULL
    END AS macro_f1,

    CASE
        WHEN moving_windows > 0
         AND idle_windows > 0
        THEN (moving_recall + idle_recall) / 2.0
        ELSE NULL
    END AS balanced_accuracy,

    false_positive_rate

FROM metrics
ORDER BY
    CASE split_role
        WHEN 'development' THEN 1
        WHEN 'within_session_validation' THEN 2
        WHEN 'idle_stress_test' THEN 3
        ELSE 4
    END;
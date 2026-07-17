WITH development_data AS (
    SELECT
        angular_rate_magnitude_mean,
        y_true
    FROM vehicle_can_validation.imu_binary_analysis
    WHERE split_role = 'development'
      AND angular_rate_magnitude_mean IS NOT NULL
      AND y_true IN (0, 1)
),

distinct_values AS (
    SELECT DISTINCT
        angular_rate_magnitude_mean AS feature_value
    FROM development_data
),

ordered_values AS (
    SELECT
        feature_value,
        LEAD(feature_value) OVER (
            ORDER BY feature_value
        ) AS next_feature_value
    FROM distinct_values
),

candidate_thresholds AS (
    SELECT
        (
            feature_value + next_feature_value
        ) / 2.0 AS threshold
    FROM ordered_values
    WHERE next_feature_value IS NOT NULL
),

predictions AS (
    SELECT
        thresholds.threshold,
        development.y_true,
        CASE
            WHEN development.angular_rate_magnitude_mean
                 >= thresholds.threshold
            THEN 1
            ELSE 0
        END AS y_pred
    FROM candidate_thresholds AS thresholds
    CROSS JOIN development_data AS development
),

confusion_counts AS (
    SELECT
        threshold,
        COUNT(*) AS total_windows,

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
    GROUP BY threshold
),

class_metrics AS (
    SELECT
        threshold,
        total_windows,
        true_positive,
        true_negative,
        false_positive,
        false_negative,

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

        1.0 * (
            true_positive + false_positive
        ) / NULLIF(
            total_windows,
            0
        ) AS predicted_moving_ratio
    FROM confusion_counts
),

final_metrics AS (
    SELECT
        *,
        (
            moving_f1 + idle_f1
        ) / 2.0 AS macro_f1,

        (
            moving_recall + idle_recall
        ) / 2.0 AS balanced_accuracy
    FROM class_metrics
)

SELECT
    RANK() OVER (
        ORDER BY
            macro_f1 DESC,
            balanced_accuracy DESC,
            moving_recall DESC,
            threshold ASC
    ) AS performance_rank,

    threshold,
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
    macro_f1,
    balanced_accuracy,
    predicted_moving_ratio

FROM final_metrics
ORDER BY
    performance_rank,
    threshold;
-- SQL Baseline Metrics

WITH analysis_data AS (
    SELECT
        split_role,
        y_true

    FROM vehicle_can_validation.imu_binary_analysis
),

development_majority AS (
    SELECT
        CASE
            WHEN COUNT_IF(y_true = 1)
                 >= COUNT_IF(y_true = 0)
            THEN 1
            ELSE 0
        END AS majority_prediction

    FROM analysis_data

    WHERE split_role = 'development'
),

baseline_models AS (
    SELECT *
    FROM (
        VALUES
            ('always_idle'),
            ('always_moving'),
            ('development_majority')
    ) AS models(baseline_model)
),

predictions AS (
    SELECT
        d.split_role,
        d.y_true,
        m.baseline_model,

        CASE
            WHEN m.baseline_model
                 = 'always_idle'
            THEN 0

            WHEN m.baseline_model
                 = 'always_moving'
            THEN 1

            ELSE dm.majority_prediction
        END AS y_pred

    FROM analysis_data AS d

    CROSS JOIN baseline_models AS m
    CROSS JOIN development_majority AS dm
),

confusion_counts AS (
    SELECT
        split_role,
        baseline_model,

        CASE
            WHEN MAX(y_pred) = 1
            THEN 'moving'
            ELSE 'idle'
        END AS predicted_class,

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
        ) AS false_negative,

        COUNT_IF(y_true = 1)
            AS moving_support,

        COUNT_IF(y_true = 0)
            AS idle_support

    FROM predictions

    GROUP BY
        split_role,
        baseline_model
),

class_metrics AS (
    SELECT
        *,

        CAST(
            true_positive + true_negative
            AS DOUBLE
        ) / NULLIF(total_windows, 0)
            AS accuracy,

        COALESCE(
            CAST(true_positive AS DOUBLE)
            / NULLIF(
                true_positive + false_positive,
                0
            ),
            0
        ) AS moving_precision,

        COALESCE(
            CAST(true_positive AS DOUBLE)
            / NULLIF(
                true_positive + false_negative,
                0
            ),
            0
        ) AS moving_recall,

        COALESCE(
            CAST(true_negative AS DOUBLE)
            / NULLIF(
                true_negative + false_negative,
                0
            ),
            0
        ) AS idle_precision,

        COALESCE(
            CAST(true_negative AS DOUBLE)
            / NULLIF(
                true_negative + false_positive,
                0
            ),
            0
        ) AS idle_recall,

        CAST(false_positive AS DOUBLE)
        / NULLIF(
            false_positive + true_negative,
            0
        ) AS false_positive_rate

    FROM confusion_counts
),

f1_metrics AS (
    SELECT
        *,

        CASE
            WHEN moving_precision
                 + moving_recall = 0
            THEN 0

            ELSE
                2 * moving_precision
                * moving_recall
                / (
                    moving_precision
                    + moving_recall
                )
        END AS moving_f1,

        CASE
            WHEN idle_precision
                 + idle_recall = 0
            THEN 0

            ELSE
                2 * idle_precision
                * idle_recall
                / (
                    idle_precision
                    + idle_recall
                )
        END AS idle_f1

    FROM class_metrics
)

SELECT
    split_role,
    baseline_model,
    predicted_class,
    total_windows,

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
        WHEN moving_support > 0
         AND idle_support > 0
        THEN (moving_f1 + idle_f1) / 2
        ELSE NULL
    END AS macro_f1,

    CASE
        WHEN moving_support > 0
         AND idle_support > 0
        THEN (moving_recall + idle_recall) / 2
        ELSE NULL
    END AS balanced_accuracy,

    false_positive_rate

FROM f1_metrics

ORDER BY
    CASE split_role
        WHEN 'development' THEN 1
        WHEN 'within_session_validation' THEN 2
        WHEN 'idle_stress_test' THEN 3
        WHEN 'transition_diagnostic' THEN 4
        ELSE 5
    END,
    baseline_model;
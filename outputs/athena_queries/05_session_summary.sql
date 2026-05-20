-- Purpose: Generate session-level telemetry summaries for multi-session behavioral comparison.
SELECT
    file_name,
    COUNT(*) AS total_records,
    AVG(byte_4_diff) AS avg_byte_4_diff,
    MAX(byte_4_diff) AS max_byte_4_diff,
    SUM(
        CASE
            WHEN driving_state = 'driving'
            THEN 1
            ELSE 0
        END
    ) AS driving_records,
    SUM(
        CASE
            WHEN driving_state = 'idle'
            THEN 1
            ELSE 0
        END
    ) AS idle_records
FROM validated_can_signals
GROUP BY file_name
ORDER BY avg_byte_4_diff DESC;
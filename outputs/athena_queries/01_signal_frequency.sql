-- Purpose: Analyze CAN signal frequency distribution across uploaded telemetry sessions.
SELECT
    can_id,
    COUNT(*) AS signal_count
FROM validated_can_signals
GROUP BY can_id
ORDER BY signal_count DESC;
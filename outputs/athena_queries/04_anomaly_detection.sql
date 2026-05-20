-- Purpose: Detect extreme Byte 4 transition events that may indicate unstable or anomalous CAN behavior.
SELECT 
    file_name,
    timestamp,
    byte_4,
    byte_4_diff,
    driving_state,
    dynamic_pattern
FROM validated_can_signals
WHERE byte_4_diff >= 200
ORDER BY byte_4_diff DESC
LIMIT 500;
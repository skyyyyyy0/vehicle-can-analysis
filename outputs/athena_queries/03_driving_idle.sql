-- Purpose: Compare driving and idle state behavior using CAN signal transition statistics.
SELECT 
    file_name,
    driving_state,
    COUNT(*) AS record_count
FROM validated_can_signals
GROUP BY 
    file_name,
    driving_state
ORDER BY 
    file_name,
    driving_state;
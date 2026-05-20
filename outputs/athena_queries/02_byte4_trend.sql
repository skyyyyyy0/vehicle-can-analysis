-- Purpose: Track Byte 4 transition behavior over time for signal trend visualization in Tableau.
SELECT
    ROW_NUMBER() OVER (ORDER BY file_name, timestamp) AS sample_index,
    file_name,
    timestamp,
    byte_4,
    byte_4_diff,
    driving_state
FROM validated_can_signals
WHERE can_id = 111
ORDER BY file_name, timestamp
LIMIT 10000;
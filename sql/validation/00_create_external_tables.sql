-- =====================================================
-- Vehicle CAN IMU Ground-Truth Validation
-- External Tables
-- =====================================================

CREATE DATABASE IF NOT EXISTS vehicle_can_validation;


CREATE EXTERNAL TABLE IF NOT EXISTS
vehicle_can_validation.imu_features_1s (
    vehicle_id STRING,
    session_id STRING,
    source_file STRING,
    timestamp_1s STRING,
    imu_record_count BIGINT,
    imu_valid_count BIGINT,
    imu_valid_ratio DOUBLE,
    acceleration_magnitude_mean DOUBLE,
    acceleration_magnitude_std DOUBLE,
    acceleration_magnitude_max DOUBLE,
    acceleration_deviation_mean DOUBLE,
    acceleration_deviation_std DOUBLE,
    acceleration_deviation_max DOUBLE,
    angular_rate_magnitude_mean DOUBLE,
    angular_rate_magnitude_std DOUBLE,
    angular_rate_magnitude_max DOUBLE,
    angular_rate_magnitude_rms DOUBLE
)
ROW FORMAT SERDE
'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"',
    'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION
's3://BUCKET/validated/imu_ground_truth_validation/imu_features_1s/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);


CREATE EXTERNAL TABLE IF NOT EXISTS
vehicle_can_validation.ground_truth_1s (
    vehicle_id STRING,
    session_id STRING,
    source_file STRING,
    timestamp_1s STRING,
    engine_rpm DOUBLE,
    vehicle_speed_kmh DOUBLE,
    rpm_record_count BIGINT,
    speed_record_count BIGINT,
    ground_truth_state STRING
)
ROW FORMAT SERDE
'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"',
    'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION
's3://BUCKET/validated/imu_ground_truth_validation/ground_truth_1s/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);
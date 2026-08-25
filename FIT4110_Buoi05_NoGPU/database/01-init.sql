-- =====================================================
-- AI Vision Service Database Schema
-- MySQL 8.0+
-- Smart Campus Operations Platform
-- =====================================================

-- Tạo database nếu chưa tồn tại
CREATE DATABASE IF NOT EXISTS ai_vision_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ai_vision_db;

-- =====================================================
-- Bảng: detections
-- Lưu trữ kết quả object detection từ AI model
-- =====================================================
DROP TABLE IF EXISTS detections;

CREATE TABLE detections (
    detection_id CHAR(36) PRIMARY KEY COMMENT 'UUID của detection request',
    camera_id VARCHAR(80) NOT NULL COMMENT 'ID của camera nguồn',
    detections JSON NOT NULL COMMENT 'Danh sách các đối tượng phát hiện được (JSON array)',
    risk_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'LOW' COMMENT 'Mức độ rủi ro',
    model_version VARCHAR(50) NOT NULL COMMENT 'Phiên bản model AI đã sử dụng',
    processing_time_ms INT UNSIGNED NOT NULL COMMENT 'Thời gian xử lý (milliseconds)',
    timestamp DATETIME NOT NULL COMMENT 'Thời điểm xử lý xong',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm lưu vào DB',

    INDEX idx_camera_id (camera_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_risk_level (risk_level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Lưu trữ kết quả object detection';

-- =====================================================
-- Bảng: face_matches
-- Lưu trữ kết quả so khớp khuôn mặt
-- =====================================================
DROP TABLE IF EXISTS face_matches;

CREATE TABLE face_matches (
    match_id CHAR(36) PRIMARY KEY COMMENT 'UUID của face match request',
    matched BOOLEAN NOT NULL COMMENT 'Kết quả khớp hay không',
    confidence DECIMAL(5,4) NOT NULL COMMENT 'Độ tin cậy của việc so khớp (0.0000 - 1.0000)',
    threshold DECIMAL(5,4) NOT NULL COMMENT 'Ngưỡng được sử dụng để so sánh',
    status ENUM('MATCHED', 'NOT_MATCHED', 'LOW_CONFIDENCE', 'ERROR') NOT NULL COMMENT 'Trạng thái kết quả',
    message VARCHAR(500) COMMENT 'Thông điệp mô tả kết quả',
    model_version VARCHAR(50) NOT NULL COMMENT 'Phiên bản model face recognition',
    processing_time_ms INT UNSIGNED NOT NULL COMMENT 'Thời gian xử lý (milliseconds)',
    trace_id VARCHAR(100) COMMENT 'Trace ID cho mục đích audit',
    timestamp DATETIME NOT NULL COMMENT 'Thời điểm xử lý xong',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm lưu vào DB',

    INDEX idx_timestamp (timestamp),
    INDEX idx_matched (matched),
    INDEX idx_status (status),
    INDEX idx_trace_id (trace_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Lưu trữ kết quả so khớp khuôn mặt';

-- =====================================================
-- Bảng: model_info
-- Lưu trữ thông tin về các AI model đang sử dụng
-- =====================================================
DROP TABLE IF EXISTS model_info;

CREATE TABLE model_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(50) NOT NULL UNIQUE COMMENT 'ID của model',
    model_type ENUM('object_detection', 'face_recognition', 'anomaly_detection') NOT NULL COMMENT 'Loại model',
    framework VARCHAR(50) NOT NULL COMMENT 'Framework AI được sử dụng',
    framework_version VARCHAR(20) NOT NULL COMMENT 'Phiên bản framework',
    classes JSON COMMENT 'Danh sách classes mà model hỗ trợ (JSON array)',
    confidence_threshold_default DECIMAL(3,2) NOT NULL DEFAULT 0.50 COMMENT 'Ngưỡng confidence mặc định',
    input_size INT UNSIGNED COMMENT 'Kích thước input chuẩn (pixels)',
    accuracy_map DECIMAL(5,4) COMMENT 'Độ chính xác trung bình (mAP)',
    inference_time_ms_avg INT UNSIGNED COMMENT 'Thời gian inference trung bình (ms)',
    last_updated DATETIME COMMENT 'Thời điểm model được cập nhật gần nhất',
    status ENUM('ACTIVE', 'LOADING', 'ERROR', 'DEPRECATED') NOT NULL DEFAULT 'ACTIVE' COMMENT 'Trạng thái model',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_model_type (model_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Lưu trữ thông tin AI model';

-- =====================================================
-- DỮ LIỆU MẪU
-- =====================================================

-- Dữ liệu mẫu: detections
INSERT INTO detections (detection_id, camera_id, detections, risk_level, model_version, processing_time_ms, timestamp) VALUES
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2babc',
    'cam-gate-01',
    '[{"label": "person", "confidence": 0.95, "bbox": {"x": 100, "y": 50, "width": 80, "height": 150}, "class_id": 0}, {"label": "backpack", "confidence": 0.72, "bbox": {"x": 120, "y": 180, "width": 30, "height": 40}, "class_id": 26}]',
    'LOW',
    'yolov8n-v1.0',
    45,
    '2026-08-25 10:30:01'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2babf',
    'cam-gate-02',
    '[]',
    'LOW',
    'yolov8n-v1.0',
    32,
    '2026-08-25 10:32:00'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bab1',
    'cam-library-01',
    '[{"label": "person", "confidence": 0.98, "bbox": {"x": 200, "y": 100, "width": 75, "height": 145}, "class_id": 0}]',
    'LOW',
    'yolov8n-v1.0',
    38,
    '2026-08-25 10:35:15'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bab2',
    'cam-parking-01',
    '[{"label": "car", "confidence": 0.92, "bbox": {"x": 50, "y": 200, "width": 200, "height": 150}, "class_id": 2}, {"label": "person", "confidence": 0.88, "bbox": {"x": 300, "y": 250, "width": 60, "height": 120}, "class_id": 0}, {"label": "motorcycle", "confidence": 0.85, "bbox": {"x": 400, "y": 280, "width": 80, "height": 100}, "class_id": 3}]',
    'MEDIUM',
    'yolov8n-v1.0',
    52,
    '2026-08-25 10:40:22'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bab3',
    'cam-entrance-01',
    '[{"label": "person", "confidence": 0.96, "bbox": {"x": 150, "y": 80, "width": 70, "height": 140}, "class_id": 0}, {"label": "person", "confidence": 0.94, "bbox": {"x": 280, "y": 75, "width": 72, "height": 142}, "class_id": 0}, {"label": "person", "confidence": 0.91, "bbox": {"x": 420, "y": 85, "width": 68, "height": 138}, "class_id": 0}, {"label": "person", "confidence": 0.89, "bbox": {"x": 550, "y": 90, "width": 65, "height": 135}, "class_id": 0}, {"label": "person", "confidence": 0.87, "bbox": {"x": 680, "y": 82, "width": 70, "height": 140}, "class_id": 0}]',
    'HIGH',
    'yolov8n-v1.0',
    68,
    '2026-08-25 11:00:00'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bab4',
    'cam-gate-03',
    '[{"label": "person", "confidence": 0.93, "bbox": {"x": 180, "y": 60, "width": 85, "height": 160}, "class_id": 0}, {"label": "backpack", "confidence": 0.78, "bbox": {"x": 200, "y": 220, "width": 35, "height": 45}, "class_id": 26}, {"label": "dog", "confidence": 0.81, "bbox": {"x": 350, "y": 300, "width": 100, "height": 80}, "class_id": 16}]',
    'MEDIUM',
    'yolov8n-v1.0',
    55,
    '2026-08-25 11:15:30'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bab5',
    'cam-library-02',
    '[{"label": "person", "confidence": 0.97, "bbox": {"x": 220, "y": 120, "width": 78, "height": 148}, "class_id": 0}, {"label": "cat", "confidence": 0.65, "bbox": {"x": 50, "y": 350, "width": 60, "height": 50}, "class_id": 15}]',
    'LOW',
    'yolov8n-v1.0',
    42,
    '2026-08-25 11:30:45'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bab6',
    'cam-parking-02',
    '[{"label": "car", "confidence": 0.94, "bbox": {"x": 100, "y": 150, "width": 250, "height": 180}, "class_id": 2}, {"label": "car", "confidence": 0.89, "bbox": {"x": 400, "y": 160, "width": 220, "height": 170}, "class_id": 2}]',
    'LOW',
    'yolov8n-v1.0',
    48,
    '2026-08-25 11:45:00'
);

-- Dữ liệu mẫu: face_matches
INSERT INTO face_matches (match_id, matched, confidence, threshold, status, message, model_version, processing_time_ms, trace_id, timestamp) VALUES
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc01',
    TRUE,
    0.9300,
    0.7500,
    'MATCHED',
    'Khuôn mặt khớp với độ tin cậy cao',
    'facenet-v1.2',
    120,
    'trace-20260825-001',
    '2026-08-25 10:30:02'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc02',
    FALSE,
    0.4500,
    0.7500,
    'NOT_MATCHED',
    'Khuôn mặt không khớp, confidence thấp hơn ngưỡng',
    'facenet-v1.2',
    95,
    'trace-20260825-002',
    '2026-08-25 10:35:15'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc03',
    FALSE,
    0.6800,
    0.7500,
    'LOW_CONFIDENCE',
    'Không đủ độ tin cậy để xác nhận, cần kiểm tra thủ công',
    'facenet-v1.2',
    88,
    'trace-20260825-003',
    '2026-08-25 10:40:30'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc04',
    TRUE,
    0.9500,
    0.7000,
    'MATCHED',
    'Khuôn mặt khớp với độ tin cậy cao',
    'facenet-v1.2',
    110,
    'trace-20260825-004',
    '2026-08-25 10:50:00'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc05',
    TRUE,
    0.8800,
    0.8500,
    'MATCHED',
    'Khuôn mặt khớp với độ tin cậy cao',
    'facenet-v1.2',
    105,
    'trace-20260825-005',
    '2026-08-25 11:00:00'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc06',
    FALSE,
    0.5200,
    0.8500,
    'LOW_CONFIDENCE',
    'Không đủ độ tin cậy để xác nhận, cần kiểm tra thủ công',
    'facenet-v1.2',
    92,
    'trace-20260825-006',
    '2026-08-25 11:15:00'
),
(
    '0196fb3d-4ad7-7d1e-9f49-5d5148d2bc07',
    FALSE,
    0.3500,
    0.7000,
    'NOT_MATCHED',
    'Khuôn mặt không khớp, confidence thấp hơn ngưỡng',
    'facenet-v1.2',
    98,
    'trace-20260825-007',
    '2026-08-25 11:30:00'
);

-- Dữ liệu mẫu: model_info
INSERT INTO model_info (model_id, model_type, framework, framework_version, classes, confidence_threshold_default, input_size, accuracy_map, inference_time_ms_avg, last_updated, status) VALUES
(
    'yolov8n-v1.0',
    'object_detection',
    'ultralytics',
    '8.3.0',
    '[{"id": 0, "name": "person", "description": "Con người"}, {"id": 2, "name": "car", "description": "Ô tô"}, {"id": 3, "name": "motorcycle", "description": "Xe máy"}, {"id": 15, "name": "cat", "description": "Mèo"}, {"id": 16, "name": "dog", "description": "Chó"}, {"id": 26, "name": "backpack", "description": "Ba lô"}]',
    0.50,
    640,
    0.7320,
    35,
    '2026-07-15 00:00:00',
    'ACTIVE'
),
(
    'facenet-v1.2',
    'face_recognition',
    'facenet-pytorch',
    '1.0.0',
    NULL,
    0.70,
    160,
    0.9870,
    80,
    '2026-06-20 00:00:00',
    'ACTIVE'
);

-- =====================================================
-- Views tiện ích
-- =====================================================

-- View: Thống kê detections theo camera
CREATE OR REPLACE VIEW v_detections_by_camera AS
SELECT
    camera_id,
    COUNT(*) as total_detections,
    SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as low_risk,
    SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_risk,
    SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk,
    SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_risk,
    AVG(processing_time_ms) as avg_processing_time_ms,
    MAX(timestamp) as last_detection
FROM detections
GROUP BY camera_id;

-- View: Thống kê face matching
CREATE OR REPLACE VIEW v_face_match_stats AS
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_matches,
    SUM(CASE WHEN matched = TRUE THEN 1 ELSE 0 END) as matched_count,
    SUM(CASE WHEN matched = FALSE THEN 1 ELSE 0 END) as not_matched_count,
    SUM(CASE WHEN status = 'LOW_CONFIDENCE' THEN 1 ELSE 0 END) as low_confidence_count,
    AVG(confidence) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time_ms
FROM face_matches
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- =====================================================
-- Stored Procedures
-- =====================================================

DELIMITER //

-- Procedure: Xóa detections cũ hơn N ngày
CREATE PROCEDURE sp_cleanup_old_detections(IN days_to_keep INT)
BEGIN
    DELETE FROM detections
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);

    SELECT ROW_COUNT() as deleted_rows;
END //

-- Procedure: Lấy detections với phân trang
CREATE PROCEDURE sp_get_detections_paginated(
    IN p_limit INT,
    IN p_offset INT,
    IN p_camera_id VARCHAR(80)
)
BEGIN
    SET @sql = 'SELECT * FROM detections';

    IF p_camera_id IS NOT NULL AND p_camera_id != '' THEN
        SET @sql = CONCAT(@sql, ' WHERE camera_id = ''', p_camera_id, '''');
    END IF;

    SET @sql = CONCAT(@sql, ' ORDER BY timestamp DESC LIMIT ', p_limit, ' OFFSET ', p_offset);

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

DELIMITER ;

-- =====================================================
-- Hoàn thành
-- =====================================================
SELECT 'Database ai_vision_db đã được tạo thành công!' AS status;
SELECT 'Tổng số bảng: 3 (detections, face_matches, model_info)' AS tables_info;

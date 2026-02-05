-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    line_uid VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    timezone VARCHAR(50) DEFAULT 'Asia/Tokyo'
);

-- 일정 유형 테이블 (채용 프로세스 단계별 분류)
CREATE TABLE IF NOT EXISTS schedule_types (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_code VARCHAR(20) UNIQUE NOT NULL,
    type_name_ja VARCHAR(50) NOT NULL,
    type_name_ko VARCHAR(50) NOT NULL,
    display_order INT NOT NULL,
    color_code VARCHAR(7) DEFAULT '#4A90E2'
);

-- 기본 데이터 삽입 (존재하지 않을 경우에만)
INSERT IGNORE INTO schedule_types (type_code, type_name_ja, type_name_ko, display_order, color_code) VALUES
('ES_SUBMIT', 'ES提出', 'ES 제출', 1, '#FF6B6B'),
('SPI_TEST', 'SPI試験', 'SPI 테스트', 2, '#4ECDC4'),
('INTERVIEW_1', '一次面接', '1차 면접', 3, '#45B7D1'),
('INTERVIEW_2', '二次面接', '2차 면접', 4, '#96CEB4'),
('INTERVIEW_3', '三次面接', '3차 면접', 5, '#FFEAA7'),
('FINAL_INTERVIEW', '最終面接', '최종 면접', 6, '#DDA15E'),
('EXPLANATION', '会社説明会', '회사 설명회', 7, '#C9ADA7'),
('INTERNSHIP', 'インターン', '인턴십', 8, '#B4A7D6'),
('RESULT_NOTIFY', '結果通知日', '결과 통지일', 9, '#F9C74F'),
('OTHER', 'その他', '기타', 10, '#90A4AE');

-- 일정 테이블
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    type_id INT NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    schedule_date DATE NOT NULL,
    schedule_time TIME,
    location VARCHAR(300),
    memo TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES schedule_types(type_id),
    INDEX idx_user_date (user_id, schedule_date),
    INDEX idx_schedule_date (schedule_date)
);

-- 알림 이력 테이블 (중복 발송 방지)
CREATE TABLE IF NOT EXISTS notification_logs (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    schedule_id BIGINT NOT NULL,
    notification_type ENUM('D-10', 'D-5', 'D-3', 'D-1', 'D-DAY') NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    UNIQUE KEY unique_notification (schedule_id, notification_type)
);

-- 주간 리포트 발송 이력
CREATE TABLE IF NOT EXISTS weekly_reports (
    report_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    report_date DATE NOT NULL,
    schedules_count INT DEFAULT 0,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_weekly_report (user_id, report_date)
);

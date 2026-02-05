import os
import mysql.connector
from datetime import datetime
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'recruitment_schedule')
        
    def get_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def init_db(self, schema_path: str = 'schema.sql'):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                
            # Split assertions because mysql connector can't do multiple at once easily safely
            # or requires multi=True
            statements = schema_sql.split(';')
            
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        print(f"Schema Init Warning (might be expected): {e}")
            
            conn.commit()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Database initialization failed: {e}")
        finally:
            cursor.close()
            conn.close()

    def create_schedule(self, line_uid: str, schedule_data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Get user_id from line_uid
            cursor.execute("SELECT user_id FROM users WHERE line_uid = %s", (line_uid,))
            user = cursor.fetchone()
            
            if not user:
                # Create user if not exists
                cursor.execute("INSERT INTO users (line_uid) VALUES (%s)", (line_uid,))
                user_id = cursor.lastrowid
            else:
                user_id = user['user_id']
                
            # Get type_id from type_code
            cursor.execute("SELECT type_id FROM schedule_types WHERE type_code = %s", (schedule_data['type_code'],))
            type_info = cursor.fetchone()
            type_id = type_info['type_id'] if type_info else 10 # Default to OTHER
            
            sql = """
                INSERT INTO schedules 
                (user_id, type_id, company_name, schedule_date, schedule_time, location, memo) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                user_id,
                type_id,
                schedule_data['company_name'],
                schedule_data['schedule_date'],
                schedule_data.get('schedule_time'),
                schedule_data.get('location'),
                schedule_data.get('memo')
            )
            
            cursor.execute(sql, values)
            conn.commit()
            return cursor.lastrowid
            
        finally:
            cursor.close()
            conn.close()

    def get_user_schedules(self, line_uid: str, month: str = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.*, st.type_code, st.type_name_ja, st.type_name_ko, st.color_code
                FROM schedules s
                JOIN users u ON s.user_id = u.user_id
                JOIN schedule_types st ON s.type_id = st.type_id
                WHERE u.line_uid = %s
            """
            params = [line_uid]
            
            if month:
                # month format: YYYY-MM
                sql += " AND DATE_FORMAT(s.schedule_date, '%Y-%m') = %s"
                params.append(month)
                
            sql += " ORDER BY s.schedule_date ASC"
            
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()

    def get_schedules_by_date(self, target_date) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.*, st.type_code, st.type_name_ja, u.line_uid
                FROM schedules s
                JOIN users u ON s.user_id = u.user_id
                JOIN schedule_types st ON s.type_id = st.type_id
                WHERE s.schedule_date = %s
            """
            cursor.execute(sql, (target_date,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def is_notification_sent(self, schedule_id: int, notification_type: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT 1 FROM notification_logs WHERE schedule_id = %s AND notification_type = %s"
            cursor.execute(sql, (schedule_id, notification_type))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()

    def log_notification(self, schedule_id: int, notification_type: str, success: bool, error: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO notification_logs (schedule_id, notification_type, is_success, error_message)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (schedule_id, notification_type, success, error))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_active_users(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Users with recent activity or schedules
            sql = "SELECT * FROM users WHERE last_active > DATE_SUB(NOW(), INTERVAL 30 DAY)"
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_user_schedules_range(self, line_uid: str, start_date, end_date) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.*, st.type_name_ja
                FROM schedules s
                JOIN users u ON s.user_id = u.user_id
                JOIN schedule_types st ON s.type_id = st.type_id
                WHERE u.line_uid = %s AND s.schedule_date BETWEEN %s AND %s
                ORDER BY s.schedule_date
            """
            cursor.execute(sql, (line_uid, start_date, end_date))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def log_weekly_report(self, user_id: int, report_date, count: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO weekly_reports (user_id, report_date, schedules_count)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE schedules_count = %s, sent_at = CURRENT_TIMESTAMP
            """
            cursor.execute(sql, (user_id, report_date, count, count))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

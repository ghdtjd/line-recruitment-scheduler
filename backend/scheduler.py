from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from linebot import LineBotApi
from linebot.models import FlexSendMessage, TextSendMessage
from database import Database
import asyncio

class NotificationScheduler:
    def __init__(self, db: Database, line_bot_api: LineBotApi):
        self.db = db
        self.line_bot_api = line_bot_api
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # Daily reminders at 8 AM
        self.scheduler.add_job(
            self.send_daily_reminders,
            'cron',
            hour=8,
            minute=0,
            timezone='Asia/Tokyo'
        )
        
        # Weekly report on Monday 8 AM
        self.scheduler.add_job(
            self.send_weekly_reports,
            'cron',
            day_of_week='mon',
            hour=8,
            minute=0,
            timezone='Asia/Tokyo'
        )
        
        self.scheduler.start()
    
    async def send_daily_reminders(self):
        """Send D-10, D-5, D-3, D-1 reminders"""
        print("Running daily reminders...")
        today = datetime.now().date()
        reminder_days = [10, 5, 3, 1]
        
        for days_before in reminder_days:
            target_date = today + timedelta(days=days_before)
            schedules = self.db.get_schedules_by_date(target_date)
            
            for schedule in schedules:
                try:
                    # Check if already sent
                    if self.db.is_notification_sent(schedule['schedule_id'], f'D-{days_before}'):
                        continue
                    
                    flex_message = self.create_reminder_flex_message(schedule, days_before)
                    
                    self.line_bot_api.push_message(
                        schedule['line_uid'],
                        FlexSendMessage(
                            alt_text=f"📅 D-{days_before} リマインド: {schedule['company_name']}",
                            contents=flex_message
                        )
                    )
                    
                    self.db.log_notification(
                        schedule['schedule_id'],
                        f'D-{days_before}',
                        success=True
                    )
                    
                except Exception as e:
                    print(f"Error sending reminder for schedule {schedule.get('schedule_id')}: {e}")
                    self.db.log_notification(
                        schedule['schedule_id'],
                        f'D-{days_before}',
                        success=False,
                        error=str(e)
                    )
    
    def create_reminder_flex_message(self, schedule, days_before):
        emoji_map = {
            'ES_SUBMIT': '📝',
            'SPI_TEST': '✏️',
            'INTERVIEW_1': '👔',
            'INTERVIEW_2': '💼',
            'INTERVIEW_3': '🎯',
            'FINAL_INTERVIEW': '🏆',
            'EXPLANATION': '🏢',
            'INTERNSHIP': '📚'
        }
        
        emoji = emoji_map.get(schedule['type_code'], '📅')
        type_name = schedule['type_name_ja']
        
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{emoji} D-{days_before} リマインド",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FF6B6B"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "企業",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": schedule['company_name'],
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 5
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "内容",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": type_name,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 5
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "日時",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": str(schedule['schedule_date']),
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 5
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": f"あと{days_before}日です。準備を忘れずに!",
                        "margin": "md",
                        "size": "sm",
                        "color": "#999999"
                    }
                ]
            }
        }
    
    async def send_weekly_reports(self):
        print("Sending weekly reports...")
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        
        users = self.db.get_active_users()
        
        for user in users:
            schedules = self.db.get_user_schedules_range(
                user['line_uid'],
                today,
                week_end
            )
            
            if not schedules:
                continue
            
            try:
                msg_text = f"📊 今週の予定 ({today} ~ {week_end})\nTotal: {len(schedules)}件\n\n"
                for s in schedules:
                    msg_text += f"- {s['schedule_date']} {s['company_name']} ({s['type_name_ja']})\n"
                
                self.line_bot_api.push_message(
                    user['line_uid'],
                    TextSendMessage(text=msg_text)
                )
                
                self.db.log_weekly_report(user['user_id'], today, len(schedules))
                
            except Exception as e:
                print(f"Weekly report error for user {user['user_id']}: {e}")

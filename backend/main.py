from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os
from database import Database
from scheduler import NotificationScheduler
from nlp_parser import ScheduleParser
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS for LIFF
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE Config
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("Warning: LINE Channel Token or Secret is missing.")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

db = Database()
scheduler = NotificationScheduler(db, line_bot_api)
nlp_parser = ScheduleParser()

@app.on_event("startup")
async def startup_event():
    # Initialize DB (Create tables if not exists)
    try:
        db.init_db()
    except Exception as e:
        print(f"Startup DB Init failed: {e}")
        
    scheduler.start()
    print("Scheduler started.")

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        print(f"Webhook error: {e}")
        # Return 200 OK to LINE anyway to avoid retries on logic errors
        return "OK"
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    line_uid = event.source.user_id
    
    # NLP Schedule Registration
    if any(keyword in user_message for keyword in ['ES', '面接', 'SPI', '説明会', '提出', 'テスト']):
        try:
            parsed = nlp_parser.parse(user_message)
            if parsed:
                db.create_schedule(line_uid, parsed)
                reply = f"✅ 登録完了!\n\n企業: {parsed['company_name']}\n種類: {parsed['type_name']}\n日時: {parsed['schedule_date']}"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply)
                )
                return
        except Exception as e:
            print(f"NLP Parse Error: {e}")
            pass # Fallback to default message
            
    # Default Response
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="予定を登録するには、「カレンダー」ボタンを押すか、「3/15 トヨタ ES提出」のように話しかけてください！")
    )

from pydantic import BaseModel
from typing import Optional

class ScheduleCreateRequest(BaseModel):
    line_uid: str
    type_code: str
    company_name: str
    schedule_date: str
    schedule_time: Optional[str] = None
    location: Optional[str] = None
    memo: Optional[str] = None

@app.post("/api/schedules")
async def create_schedule(data: ScheduleCreateRequest):
    schedule_data = {
        'type_code': data.type_code,
        'company_name': data.company_name,
        'schedule_date': data.schedule_date,
        'schedule_time': data.schedule_time,
        'location': data.location,
        'memo': data.memo
    }
    
    try:
        schedule_id = db.create_schedule(data.line_uid, schedule_data)
        return {"success": True, "schedule_id": schedule_id}
    except Exception as e:
        print(f"API Create Schedule Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schedules/{line_uid}")
async def get_schedules(line_uid: str, month: str = None):
    try:
        schedules = db.get_user_schedules(line_uid, month)
        # Handle datetime serialization if necessary (fastapi/pydantic usually handles it, 
        # but pure mysql cursor returns datetime objects)
        return {"schedules": schedules}
    except Exception as e:
        print(f"API Get Schedules Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

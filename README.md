# LINE 취업 일정 관리 시스템 (Recruitment Schedule Manager)

일본 취준생을 위한 LINE 기반 자기주도형 채용 일정 관리 시스템입니다.

## 📁 프로젝트 구조

- `backend/`: FastAPI 기반의 백엔드 서버 (API, 스케줄러, NLP)
- `frontend/`: React + Vite 기반의 LIFF 웹페이지 (달력 UI)
- `schema.sql`: MySQL 데이터베이스 스키마

## 🚀 설치 및 실행 방법

### 1. 데이터베이스 설정 (MySQL)

MySQL이 설치되어 있어야 합니다.

```bash
# MySQL 접속
mysql -u root -p

# DB 생성 및 스키마 적용
CREATE DATABASE recruitment_schedule;
USE recruitment_schedule;
SOURCE schema.sql;
```

### 2. 백엔드 (Backend) 설정

```bash
cd backend

# 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
# .env 파일을 생성하고 아래 내용을 채워주세요 (backend/ 폴더 내)
# LINE_CHANNEL_ACCESS_TOKEN=...
# LINE_CHANNEL_SECRET=...
# DB_USER=root
# DB_PASSWORD=your_password

# 서버 실행
uvicorn main:app --reload
```
서버는 `http://localhost:8000`에서 실행됩니다.
- API 문서: `http://localhost:8000/docs`

### 3. 프론트엔드 (Frontend) 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경변수 설정
# .env 파일을 frontend/ 폴더 내에 생성 (필요시)
# VITE_API_BASE_URL=http://localhost:8000/api

# 개발 서버 실행
npm run dev
```
프론트엔드는 `http://localhost:5173`에서 실행됩니다.

## 🧪 테스트 방법

### 1. 로컬 테스트 (LINE 연동 없이)
- **API 테스트**: `http://localhost:8000/docs` 접속 후 `POST /api/schedules` 등을 직접 호출해봅니다.
- **화면 테스트**: `http://localhost:5173` 접속. (LIFF ID가 없으면 LINE 로그인 기능은 작동하지 않지만, 화면 UI는 확인 가능합니다.)

### 2. LINE 연동 테스트 (실전)
LINE 플랫폼은 `https` 주소만 허용하므로 `ngrok` 같은 터널링 도구가 필요합니다.

1. **ngrok 실행**:
   ```bash
   ngrok http 8000  # 백엔드 터널링
   ngrok http 5173  # 프론트엔드 터널링 (별도 세션)
   ```
2. **LINE Developers Console 설정**:
   - **Messaging API Webhook**: ngrok 백엔드 주소 + `/webhook` 입력 (예: `https://xxxx.ngrok.io/webhook`)
   - **LIFF Endpoint**: ngrok 프론트엔드 주소 입력
3. **실제 사용**:
   - LINE 봇에게 "내일 도요타 면접"이라고 말해보기
   - LIFF 달력 열어서 일정 등록해보기


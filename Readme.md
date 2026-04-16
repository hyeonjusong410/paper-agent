# 📡 PaperAgent — AI 논문 트렌드 대시보드

AI 분야 최신 논문을 자동 수집하고 트렌드를 분석하는 대시보드 에이전트입니다.

## 주요 기능

- **자동 논문 수집** — arXiv에서 매일 AI 관련 논문 자동 수집 (cs.AI, cs.LG, cs.CL)
- **트렌드 키워드 분석** — 논문 초록에서 핵심 키워드 빈도 분석
- **주목 논문** — 트렌드 점수 기반 주목 논문 선별
- **기관별/저자별 현황** — Google, OpenAI, Meta 등 주요 기관 논문 현황
- **AI 논문 분석 에이전트** — Gemini AI 기반 논문 트렌드 질문 응답
- **주간 메일 발송** — 매주 금요일 오전 6시 트렌드 리포트 자동 발송
- **월별 키워드 히트맵** — 키워드 트렌드 변화 시각화

## 기술 스택

| 분류 | 기술 |
|---|---|
| 백엔드 | Python, Flask |
| 데이터베이스 | Supabase (PostgreSQL) |
| 논문 수집 | arXiv API |
| AI 에이전트 | Google Gemini API |
| 스케줄러 | APScheduler |
| 메일 발송 | Gmail SMTP |
| 배포 | Render |

## 프로젝트 구조

```
paper-agent/
├── app.py          # Flask 서버 + API 라우트
├── collector.py    # arXiv 논문 수집 + DB 저장
├── agent.py        # Gemini AI 논문 분석 에이전트
├── mailer.py       # 주간 트렌드 메일 발송
├── templates/
│   └── index.html  # 대시보드 화면
├── requirements.txt
└── .env            # 환경변수 (git 미포함)
```

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/hyeonjusong410/paper-agent.git
cd paper-agent
```

### 2. 가상환경 설정
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일 생성:
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=your_supabase_connection_string
MAIL_TO=recipient@gmail.com
GMAIL_ADDRESS=your@gmail.com
GMAIL_PASSWORD=your_app_password
```

### 5. 실행
```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 배포

Render + Supabase 조합으로 무료 배포 가능합니다.

### 환경변수 설정 (Render)
| Key | Value |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `DATABASE_URL` | Supabase Connection String |
| `MAIL_TO` | 수신 이메일 |
| `GMAIL_ADDRESS` | 발신 Gmail |
| `GMAIL_PASSWORD` | Gmail 앱 비밀번호 |

## 자동화 스케줄

| 작업 | 주기 |
|---|---|
| 논문 수집 | 매일 오전 9시 |
| 트렌드 메일 발송 | 매주 금요일 오전 6시 |

## 라이선스

MIT License
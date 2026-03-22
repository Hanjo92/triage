#!/bin/bash

echo "Checking and seeding initial Database..."
# DB가 비어있으면 초기 행동 데이터 16개를 자동으로 주입합니다.
python scripts/seed_actions.py

echo "Starting Telegram Bot in background..."
python src/platforms/telegram/bot.py &

echo "Starting FastAPI Server..."
# Railway에서 할당해 주는 동적 PORT 환경변수를 사용합니다.
uvicorn src.platforms.toss.main:app --host 0.0.0.0 --port ${PORT:-8000}

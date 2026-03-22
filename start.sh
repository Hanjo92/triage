#!/bin/bash

# Railway 서버용 통합 실행 스크립트
echo "Starting Telegram Bot..."
python src/platforms/telegram/bot.py &

echo "Starting FastAPI Server..."
# Railway에서 할당해 주는 동적 PORT 환경변수를 사용합니다.
uvicorn src.platforms.toss.main:app --host 0.0.0.0 --port ${PORT:-8000}

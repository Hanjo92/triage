# Triage Deploy Guide

트리아지 텔레그램 봇 + DB 연동 및 배포 가이드
1. 개요
텔레그램 봇에 PostgreSQL DB를 연결하고 Railway를 통해 배포하는 가이드
2. 필요한 스택
- Python- python-telegram-bot- PostgreSQL- Railway
3. DB 연결 코드 (예시)
import psycopg2conn = psycopg2.connect(    dbname="your_db",    user="your_user",    password="your_password",    host="your_host")cursor = conn.cursor()
4. 유저 저장 로직
def save_user(user_id):    cursor.execute("INSERT INTO users (id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))    conn.commit()
5. 체크인 저장
def save_checkin(user_id, energy, time, state):    cursor.execute(        "INSERT INTO checkins (user_id, energy, time, state) VALUES (%s,%s,%s,%s)",        (user_id, energy, time, state)    )    conn.commit()
6. 추천 연결
def get_actions(energy):    cursor.execute("SELECT name FROM actions WHERE energy_level=%s LIMIT 3", (energy,))    return cursor.fetchall()
7. Railway 배포
1. Railway 가입2. GitHub 연결3. 프로젝트 생성4. PostgreSQL 추가5. 환경변수 설정 (DB_URL, BOT_TOKEN)6. 배포
8. 실행
python bot.py

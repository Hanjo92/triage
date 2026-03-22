import sys
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

# 루트 모듈 인식용 상대 경로
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.db.session import SessionLocal
from src.db.models import User, DailyCheckin, Completion, Action
from src.core.recommendation import recommend_actions
from src.core.streak import get_missed_days, get_completion_score

app = FastAPI(title="Triage API for Toss Miniapp", version="1.0.0")

def get_db():
    """DB 세션 제너레이터 (FastAPI의 Depends 용도)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schema Models ---
class CheckinRequest(BaseModel):
    user_id: str
    energy_level: str
    available_time: str
    mental_state: str

class ActionItemModel(BaseModel):
    action_id: str
    label: str
    prompt_copy: str

class CheckinResponse(BaseModel):
    mode: str
    message: str
    action_candidates: List[ActionItemModel]

class CompletionRequest(BaseModel):
    user_id: str
    action_id: str
    status: str

class CompletionResponse(BaseModel):
    score: float
    streak_message: str

# --- API Endpoints ---
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "Triage Toss MiniApp API Server is running."}

@app.post("/v1/checkins", response_model=CheckinResponse)
def create_checkin(req: CheckinRequest, db=Depends(get_db)):
    """
    1. 사용자의 아침 체크인 데이터를 받음 (에너지, 시간, 상태)
    2. 최근 놓친 일수(missed_days)를 조회해 모드 판별 (recovery / start / maintain)
    3. 해당 모드에 맞는 행동 3개를 추천 리스트로 반환
    """
    # [토스 미니앱] 용도이므로 user_id를 고유값으로 가입 처리
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        # 최초 접속 유저의 경우 임시 생성 (실제 운영 시 toss CI/DI 값 연동 필요)
        user = User(id=req.user_id, toss_id=req.user_id)
        db.add(user)
        db.commit()
    
    missed_days = get_missed_days(db, user.id)
    mode, rec_actions = recommend_actions(db, req.energy_level, req.available_time, req.mental_state, missed_days)
    
    # 체크인 이력 저장
    checkin = DailyCheckin(
        user_id=user.id,
        energy_level=req.energy_level,
        available_time=req.available_time,
        mental_state=req.mental_state,
        mode=mode
    )
    db.add(checkin)
    db.commit()
    
    # UX 카피 모드 처리
    if mode == 'recovery':
        msg = f"※ 최근 루틴이 며칠 끊겼네요. 무리하지 말고 딱 떨어지는 초소형 윈(Win)만 챙겨볼까요?"
    elif mode == 'start':
        msg = "몸이 무거울 땐 착수 자체를 작게 자르는 게 좋습니다. 이 중 하나만 해보죠."
    else:
        msg = "좋습니다! 오늘 하루를 열어줄 작은 행동을 골라주세요."
        
    candidates = [
        ActionItemModel(action_id=act.id, label=act.label, prompt_copy=act.prompt_copy)
        for act in rec_actions
    ]
    
    # 예외(비상) 액티브 액션 처리가 필요할 때 (예: DB 비어있을 때)
    if not candidates:
        candidates.append(ActionItemModel(action_id="fallback", label="물 한 잔 마시기", prompt_copy="가볍게 물부터 마셔볼까요?"))
        
    return CheckinResponse(mode=mode, message=msg, action_candidates=candidates)

@app.post("/v1/completions", response_model=CompletionResponse)
def record_completion(req: CompletionRequest, db=Depends(get_db)):
    """
    사용자가 제시된 액션을 완료/부분완료/실패 했는지 상태 기록하고
    점수 체계에 따른 소프트 스트릭(Soft Streak) 계산 결과를 응답
    """
    # 사용자의 오늘 모드를 조회하여 회복 점수로 계산할지 판별
    recent_checkin = db.query(DailyCheckin)\
        .filter(DailyCheckin.user_id == req.user_id)\
        .order_by(DailyCheckin.created_at.desc()).first()
        
    is_recovery_mode = (recent_checkin and recent_checkin.mode == 'recovery')
    
    score = get_completion_score(req.status, is_recovery_mode)
    
    if req.action_id != "fallback":
        completion = Completion(
            user_id=req.user_id,
            action_id=req.action_id,
            status=req.status,
            score=score
        )
        db.add(completion)
        db.commit()
        
    # 결과 메시지
    if req.status == "done":
        streak_msg = "🎉 훌륭합니다! 오늘의 스트릭이 성공적으로 이어졌어요."
    elif req.status == "partial":
        streak_msg = "👍 완벽하지 않아도 괜찮아요. 행동이 끊기지 않은 것이 중요합니다!"
    else:
        streak_msg = "괜찮습니다! 자책하거나 스트레스 받지 마세요. 끊어진 흐름은 다시 붙이면 됩니다."

    return CompletionResponse(score=score, streak_message=streak_msg)

@app.get("/v1/streaks/today")
def get_streak_state(user_id: str, db=Depends(get_db)):
    """현재 스트릭 상태(놓친 날짜 수 등) 조회 API"""
    missed_days = get_missed_days(db, user_id)
    needs_recovery = (missed_days >= 2)
    return {
        "user_id": user_id,
        "missed_days": missed_days,
        "needs_recovery": needs_recovery,
        "message": "회복 모드 발동 필요!" if needs_recovery else "순항 중!"
    }

import sys
import os

# src 폴더의 모듈을 import 할 수 있도록 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.session import engine, SessionLocal, Base
from src.db.models import Action, User, DailyCheckin, Completion

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 기획서 기준 행동 데이터셋 (MVP용 액션)
seed_data = [
    # 📌 초저강도 / 회복 (Recovery / Low energy / 1-3 mins)
    { "label": "물 한 잔 마시기", "prompt_copy": "딱 한 잔, 물만 마시고 와볼까요?", "mode_tags": ["recovery", "micro_win"], "energy_tags": ["low", "mid"], "time_tags": ["1"], "state_tags": ["tired", "distracted"], "domain_tags": ["life", "health"], "difficulty": 1, "recovery_safe": True },
    { "label": "자리에서 10초 스트레칭", "prompt_copy": "일어나기 힘들면 앉은 채로 기지개만 10초 쭉 켜봐요.", "mode_tags": ["recovery", "micro_win"], "energy_tags": ["low"], "time_tags": ["1"], "state_tags": ["tired", "stressed"], "domain_tags": ["health"], "difficulty": 1, "recovery_safe": True },
    { "label": "깊게 숨 3번 쉬기", "prompt_copy": "아무 생각 없이, 코로 들이마시고 입으로 내쉬기 딱 3번만 해요.", "mode_tags": ["recovery", "micro_win"], "energy_tags": ["low", "mid"], "time_tags": ["1"], "state_tags": ["stressed", "distracted"], "domain_tags": ["life"], "difficulty": 1, "recovery_safe": True },
    { "label": "휴대폰 내려놓기", "prompt_copy": "지금 잡고 있는 그 폰을 1분만 책상 끝에 밀어둘까요?", "mode_tags": ["recovery"], "energy_tags": ["low"], "time_tags": ["1"], "state_tags": ["distracted"], "domain_tags": ["life"], "difficulty": 1, "recovery_safe": True },
    { "label": "창밖 10초 보기", "prompt_copy": "잠깐 눈을 쉬어줄 겸 10초만 멍하니 밖을 봐요.", "mode_tags": ["recovery"], "energy_tags": ["low"], "time_tags": ["1"], "state_tags": ["tired"], "domain_tags": ["life"], "difficulty": 1, "recovery_safe": True },
    
    # 📌 시작형 / 압박 및 미루기 상태 대응 (Start / Low-Mid energy / 1-3 mins)
    { "label": "작업 파일 열기", "prompt_copy": "딴 건 안 해도 좋으니 파일 창만 띄워둘까요?", "mode_tags": ["start"], "energy_tags": ["low", "mid"], "time_tags": ["1", "3"], "state_tags": ["stressed", "distracted"], "domain_tags": ["work", "study"], "difficulty": 1, "recovery_safe": True },
    { "label": "할 일 1개 적기", "prompt_copy": "머릿속이 복잡하죠? 지금 제일 걸리는 거 딱 한 줄만 적어봅시다.", "mode_tags": ["start", "recovery"], "energy_tags": ["low", "mid"], "time_tags": ["1", "3"], "state_tags": ["stressed", "distracted"], "domain_tags": ["work", "life"], "difficulty": 1, "recovery_safe": True },
    { "label": "첫 줄만 작성하기", "prompt_copy": "완성은 나중에. 일단 첫 단어나 한 줄만 써볼까요?", "mode_tags": ["start", "micro_win"], "energy_tags": ["mid"], "time_tags": ["1", "3"], "state_tags": ["stressed"], "domain_tags": ["work", "study"], "difficulty": 2, "recovery_safe": False },
    { "label": "제목만 정하기", "prompt_copy": "본문은 손대지 말고 뭐할지 제목만 먼저 붙여봐요.", "mode_tags": ["start"], "energy_tags": ["low", "mid"], "time_tags": ["1", "3"], "state_tags": ["stressed", "distracted"], "domain_tags": ["work", "study"], "difficulty": 2, "recovery_safe": False },
    { "label": "타이머 3분 시작하기", "prompt_copy": "폰 알람을 '3분'만 맞추고 그것만 해볼까요?", "mode_tags": ["start"], "energy_tags": ["mid", "high"], "time_tags": ["3"], "state_tags": ["distracted", "stressed"], "domain_tags": ["work", "study"], "difficulty": 2, "recovery_safe": False },
    
    # 📌 유지형 / 중강도 이상 (Maintain / Mid-High / 3-10+ mins)
    { "label": "책상 3분 정리", "prompt_copy": "주변에 있는 빈 컵이나 쓰레기만 먼저 싹 치워볼까요?", "mode_tags": ["maintain", "micro_win"], "energy_tags": ["mid"], "time_tags": ["3"], "state_tags": ["distracted"], "domain_tags": ["life", "work"], "difficulty": 2, "recovery_safe": True },
    { "label": "짧은 글 3줄 쓰기", "prompt_copy": "너무 깊게 생각 말고 떠오르는 대로 딱 세 줄만 써봅시다.", "mode_tags": ["maintain", "start"], "energy_tags": ["mid", "high"], "time_tags": ["3", "10"], "state_tags": ["focused"], "domain_tags": ["work", "study"], "difficulty": 2, "recovery_safe": False },
    { "label": "어깨/목 스트레칭 3분", "prompt_copy": "뻐근한 목이랑 어깨만 3분간 가볍게 돌려주세요.", "mode_tags": ["maintain", "micro_win"], "energy_tags": ["mid"], "time_tags": ["3"], "state_tags": ["tired"], "domain_tags": ["health"], "difficulty": 2, "recovery_safe": True },
    { "label": "집중 10분 하기", "prompt_copy": "흐름이 나쁘지 않네요. 지금부터 딱 10분만 푹 빠져볼까요?", "mode_tags": ["maintain"], "energy_tags": ["mid", "high"], "time_tags": ["10"], "state_tags": ["focused"], "domain_tags": ["work", "study"], "difficulty": 3, "recovery_safe": False },
    { "label": "문서 부분 작성", "prompt_copy": "오늘의 몫으로 1페이지 분량만 채워봅시다.", "mode_tags": ["maintain"], "energy_tags": ["high"], "time_tags": ["10", "20", "30"], "state_tags": ["focused"], "domain_tags": ["work", "study"], "difficulty": 4, "recovery_safe": False },
    { "label": "핵심 로직 1개 구현", "prompt_copy": "지금 집중력이면 작은 기능 하나 정도는 충분히 완성할 수 있어요.", "mode_tags": ["maintain"], "energy_tags": ["high"], "time_tags": ["20", "30"], "state_tags": ["focused"], "domain_tags": ["work"], "difficulty": 5, "recovery_safe": False }
]

def seed():
    db = SessionLocal()
    
    try:
        existing_count = db.query(Action).count()
        if existing_count > 0:
            print(f"🔥 데이터베이스에 이미 {existing_count}개의 행동 데이터가 존재합니다. 덮어쓰지 않고 종료합니다.")
            return

        print("🚀 [트리아지] 초기 행동 데이터셋(Action Dataset) 시딩을 시작합니다...")
        for data in seed_data:
            action = Action(
                label=data["label"],
                prompt_copy=data["prompt_copy"],
                mode_tags=data["mode_tags"],
                energy_tags=data["energy_tags"],
                time_tags=data["time_tags"],
                state_tags=data["state_tags"],
                domain_tags=data["domain_tags"],
                difficulty=data["difficulty"],
                recovery_safe=data["recovery_safe"]
            )
            db.add(action)
        
        db.commit()
        print(f"✅ 성공적으로 {len(seed_data)}개의 행동 데이터가 DB에 삽입되었습니다.")
    
    except Exception as e:
        print(f"❌ 데이터 시딩 중 오류 발생: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    seed()

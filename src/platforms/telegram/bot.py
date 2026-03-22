import sys
import os
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 프로젝트 최상단 폴더의 모듈들을 인식하도록 경로 지정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.db.session import SessionLocal
from src.db.models import User, DailyCheckin, Completion, Action, UserReminder
from src.core.recommendation import recommend_actions
from src.core.streak import get_missed_days, get_completion_score

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

async def get_or_create_user(db, telegram_id: str):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 커맨드 - 초기 진입 및 가입"""
    context.user_data.clear()
    
    # 봇 시작 시 DB에 유저 저장 (스케줄러에서 메시지를 쏠 수 있도록 채팅방 ID 확보)
    telegram_id = str(update.effective_user.id)
    db = SessionLocal()
    try:
        await get_or_create_user(db, telegram_id)
    finally:
        db.close()
        
    webapp_url = os.getenv("WEBAPP_URL", "https://YOUR_WEBAPP_URL_HERE.up.railway.app").strip()
    if not webapp_url.startswith("http"):
        webapp_url = "https://" + webapp_url
        
    keyboard = [
        [InlineKeyboardButton("🚀 트리아지 미니앱 켜기", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton("🙂 에너지 좋음", callback_data="energy_high")],
        [InlineKeyboardButton("😐 그냥 보통", callback_data="energy_mid")],
        [InlineKeyboardButton("😵 완전 방전됨", callback_data="energy_low")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("굿모닝! 트리아지에 오신 걸 환영합니다.\n오늘 아침 상태는 어때요?", reply_markup=reply_markup)

# ==========================================
# ⏰ 커스텀 개인화 알람 기능 (매 분마다 검사)
# ==========================================
async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    """모든 가입 유저의 커스텀 알람 시간과 현재 시간을 대조하여 발송"""
    import pytz
    from datetime import datetime
    try:
        seoul = pytz.timezone('Asia/Seoul')
    except ImportError:
        return
        
    now = datetime.now(seoul)
    current_time_str = f"{now.hour:02d}:{now.minute:02d}"
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.telegram_id.isnot(None)).all()
        for user in users:
            reminders = db.query(UserReminder).filter(UserReminder.user_id == user.id).all()
            user_times = [r.time_str for r in reminders] if reminders else ["08:00"]
            
            if current_time_str in user_times:
                keyboard = [
                    [InlineKeyboardButton("🙂 가벼운 편", callback_data="energy_high")],
                    [InlineKeyboardButton("😐 그냥 보통", callback_data="energy_mid")],
                    [InlineKeyboardButton("😵 완전 방전", callback_data="energy_low")],
                    [InlineKeyboardButton("🛑 오늘은 패스", callback_data="energy_skip")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                try:
                    await context.bot.send_message(
                        chat_id=user.telegram_id,
                        text="🌅 새로운 루틴을 시작할 시간입니다! 마음의 준비 상태는 어떠신가요?",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logging.error(f"유저 {user.telegram_id} 에게 알림 발송 실패: {e}")
    finally:
        db.close()

async def trigger_reminder_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/push 커맨드 - 테스트용 즉시 알림 발송"""
    await update.message.reply_text("수동 알림을 전체 발송합니다...")
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.telegram_id.isnot(None)).all()
        for user in users:
            keyboard = [
                [InlineKeyboardButton("🙂 가벼운 편", callback_data="energy_high")],
                [InlineKeyboardButton("😐 그냥 보통", callback_data="energy_mid")]
            ]
            msg = await context.bot.send_message(chat_id=user.telegram_id, text="수동 PUSH 테스트입니다.", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()

async def add_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/alarm HH:MM 명령어로 새 알람 추가"""
    if not context.args:
        await update.message.reply_text("📝 사용법: `/alarm 08:30` (24시간제 시간과 분을 띄어쓰기 없이 적어주세요)", parse_mode="Markdown")
        return
    time_str = context.args[0]
    if len(time_str) != 5 or ":" not in time_str:
        await update.message.reply_text("❌ 시간 형식이 잘못되었습니다. 08:30, 14:00 와 같이 콜론(:)을 넣어주세요.")
        return
        
    db = SessionLocal()
    try:
        user = await get_or_create_user(db, str(update.effective_user.id))
        exists = db.query(UserReminder).filter(UserReminder.user_id == user.id, UserReminder.time_str == time_str).first()
        if not exists:
            db.add(UserReminder(user_id=user.id, time_str=time_str))
            db.commit()
        await update.message.reply_text(f"✅ 매일 **{time_str}**에 추가로 봇이 말을 걸어드릴게요! (기존 기본 알람 08:00은 대체됩니다)", parse_mode="Markdown")
    finally:
        db.close()

async def list_alarms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = await get_or_create_user(db, str(update.effective_user.id))
        rems = db.query(UserReminder).filter(UserReminder.user_id == user.id).all()
        if not rems:
            await update.message.reply_text("🔔 등록된 맞춤 알람이 없습니다. (기본으로 매일 아침 08:00에 발송됩니다)\n\n알람 추가 명령어:\n`/alarm 09:30`")
        else:
            times = ", ".join(sorted([r.time_str for r in rems]))
            await update.message.reply_text(f"🔔 현재 등록된 나의 개인 알람 시간들:\n**{times}**\n\n알람 추가: `/alarm HH:MM`\n모두 초기화: `/clear_alarms`", parse_mode="Markdown")
    finally:
        db.close()

async def clear_alarms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = await get_or_create_user(db, str(update.effective_user.id))
        rems = db.query(UserReminder).filter(UserReminder.user_id == user.id).all()
        for r in rems:
            db.delete(r)
        db.commit()
        await update.message.reply_text("♻️ 내가 만든 수동 알람들을 전부 지웠습니다! 이제 다시 기본(아침 08:00) 1개만 발송됩니다.")
    finally:
        db.close()
# ==========================================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    telegram_id = str(query.from_user.id)

    db = SessionLocal()
    try:
        user = await get_or_create_user(db, telegram_id)
        
        # 0. 오늘은 건너뛰기 (스케줄러 팝업에서 선택 시)
        if data == "energy_skip":
            await query.edit_message_text("알겠습니다! 무리하지 마세요.\n언제든 `/start`를 눌러 다시 시작할 수 있습니다. 푹 쉬세요 🍵")
            return
            
        # 1. 시간 선택
        if data.startswith("energy_"):
            context.user_data['energy'] = data.split("_")[1]
            keyboard = [
                [InlineKeyboardButton("딱 3분 가능", callback_data="time_3")],
                [InlineKeyboardButton("10분 정도", callback_data="time_10")],
                [InlineKeyboardButton("30분 이상 여유", callback_data="time_30")]
            ]
            await query.edit_message_text("지금 가볍게 투자할 수 있는 최대 시간은요?", reply_markup=InlineKeyboardMarkup(keyboard))
            
        # 2. 멘탈/기분 선택
        elif data.startswith("time_"):
            context.user_data['time'] = data.split("_")[1]
            keyboard = [
                [InlineKeyboardButton("🤔 집중 잘됨", callback_data="state_focused")],
                [InlineKeyboardButton("🌀 약간 산만함", callback_data="state_distracted")],
                [InlineKeyboardButton("💦 스트레스/압박", callback_data="state_stressed")],
                [InlineKeyboardButton("💤 그냥 지침", callback_data="state_tired")]
            ]
            await query.edit_message_text("현재 멘탈 및 기분은 어떤 상태인가요?", reply_markup=InlineKeyboardMarkup(keyboard))

        # 3. 상황별 추천 액션
        elif data.startswith("state_"):
            state_val = data.split("_")[1]
            context.user_data['state'] = state_val
            
            energy = context.user_data.get('energy', 'mid')
            time_val = context.user_data.get('time', '10')
            missed_days = get_missed_days(db, user.id)
            
            mode, rec_actions = recommend_actions(db, energy, time_val, state_val, missed_days)
            context.user_data['mode'] = mode
            
            checkin = DailyCheckin(
                user_id=user.id,
                energy_level=energy,
                available_time=time_val,
                mental_state=state_val,
                mode=mode
            )
            db.add(checkin)
            db.commit()

            if mode == 'recovery':
                msg = f"※ 감지됨: {missed_days}일 연속 미수행\n\n최근 루틴이 조금 끊겼군요. 괜찮아요! 무리하지 말고 딱 떨어지는 초소형 미션만 챙겨볼까요?"
            elif mode == 'start':
                msg = "몸이 무겁고 압박이 클 땐 다른 생각 말고 진입장벽을 부수는 것 하나만 골라보죠."
            else:
                msg = "좋습니다! 오늘 하루를 열어줄 작은 승리(Win)를 골라주세요."

            keyboard = []
            for act in rec_actions:
                keyboard.append([InlineKeyboardButton(act.label, callback_data=f"action_{act.id}")])
            if not rec_actions:
                keyboard.append([InlineKeyboardButton("물 한 잔 마시기", callback_data="fallback_action")])
                
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

        # 4. 행동 선택 후 프롬프트 노출
        elif data.startswith("action_"):
            action_id = data.replace("action_", "")
            context.user_data['chosen_action_id'] = action_id
            
            action = db.query(Action).filter(Action.id == action_id).first()
            prompt = action.prompt_copy if action else "자, 선택하신 행동을 지금 가볍게 시작해볼까요?"
            
            keyboard = [
                [InlineKeyboardButton("✅ 끝까지 완료", callback_data="done")],
                [InlineKeyboardButton("👌 조금 시도함", callback_data="partial")],
                [InlineKeyboardButton("❌ 결국 못함", callback_data="fail")]
            ]
            await query.edit_message_text(f"💡 {prompt}\n\n(행동을 마친 뒤 아래 결과를 체크해주세요)", reply_markup=InlineKeyboardMarkup(keyboard))

        # 5. 최종 결과
        elif data in ["done", "partial", "fail"]:
            status = data
            action_id = context.user_data.get('chosen_action_id')
            mode = context.user_data.get('mode', 'maintain')
            
            is_recovery = (mode == 'recovery')
            score = get_completion_score(status, is_recovery)
            
            if action_id:
                completion = Completion(user_id=user.id, action_id=action_id, status=status, score=score)
                db.add(completion)
                db.commit()

            if status == "done":
                await query.edit_message_text("🎉 훌륭합니다! 오늘의 스트릭이 성공적으로 이어졌어요. 내일 아침 알람 때 봐요!")
            elif status == "partial":
                await query.edit_message_text("👍 완벽하지 않아도 괜찮아요. 행동이 끊기지 않은 것이 중요합니다!")
            elif status == "fail":
                keyboard = [
                    [InlineKeyboardButton("🛡️ 회복 행동 하나 해보기", callback_data="recovery_mode_trigger")]
                ]
                await query.edit_message_text("괜찮습니다! 자책하거나 스트레스 받지 마세요.\n대신, 아주 작게 끊어진 흐름만 1초만에 다시 붙여볼까요?", reply_markup=InlineKeyboardMarkup(keyboard))

        # 6. 회복 모드 권유
        elif data == "recovery_mode_trigger":
            _, rec_actions = recommend_actions(db, energy='low', available_time='1', state='tired', missed_days=2) 
            keyboard = []
            for act in rec_actions:
                keyboard.append([InlineKeyboardButton(act.label, callback_data=f"recoverdone_{act.id}")])
            if not rec_actions:
                keyboard.append([InlineKeyboardButton("물 한 잔 마시기", callback_data="recoverdone_fallback")])
            await query.edit_message_text("이 중 가장 당장 숨 안 차고 할 수 있는 걸 골라 완료버튼을 눌러주세요.", reply_markup=InlineKeyboardMarkup(keyboard))

        # 7. 회복 모드 완료
        elif data.startswith("recoverdone_"):
            action_id = data.replace("recoverdone_", "")
            score = get_completion_score('done', is_recovery_mode=True)
            if action_id != "fallback":
                completion = Completion(user_id=user.id, action_id=action_id, status='done', score=score)
                db.add(completion)
                db.commit()
            await query.edit_message_text("🙌 방금 복귀 플래그 꽂기 성공! 루틴은 끊어지지 않았습니다. 내일 또 만나요.")
            
    finally:
        db.close()

from telegram.ext import MessageHandler, filters

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지정되지 않은 명령어 또는 텍스트를 쳤을 때 안내"""
    await update.message.reply_text("진행 중인 질문의 버튼을 눌러주세요!\n처음 상태로 되돌리려면 /start 를 다시 입력해 주세요. ♻️")

def main():
    if TOKEN == "YOUR_BOT_TOKEN_HERE" or not TOKEN:
        logging.warning("⚠️ 환경변수에 BOT_TOKEN이 등록되지 않았습니다.")
        
    app = ApplicationBuilder().token(TOKEN).build()

    # 한국시간(UTC+9) 오전 8시를 기준 시간으로 설정
    if app.job_queue:
        try:
            import pytz
            app.job_queue.run_repeating(check_reminders, interval=60)
            print(f"🕒 개인별 맞춤 알람 스케줄러 등록 완료 (매 분 검사)")
        except ImportError:
            logging.warning("⚠️ 서드파티 스케줄러를 위해 pytz가 필요합니다.")
    else:
        logging.error("❌ python-telegram-bot[job-queue] 패키지가 없어 스케줄러를 비활성화합니다.")
        
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("push", trigger_reminder_now))
    app.add_handler(CommandHandler("alarm", add_alarm))
    app.add_handler(CommandHandler("alarms", list_alarms))
    app.add_handler(CommandHandler("clear_alarms", clear_alarms))
    app.add_handler(CallbackQueryHandler(button))
    # 텍스트를 칠 경우 친절하게 안내하는 텍스트 핸들러
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_unknown_message))
    
    print("🤖 [트리아지] 텔레그램 봇 모듈 동작 준비 완료! (Ctrl+C를 눌러 종료)")
    # 실 배포/테스트 준비 완료
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

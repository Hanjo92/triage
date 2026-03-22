
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🙂 괜찮음", callback_data="energy_good")],
        [InlineKeyboardButton("😐 보통", callback_data="energy_mid")],
        [InlineKeyboardButton("😵 힘듦", callback_data="energy_low")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("오늘 상태 어때요?", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("energy"):
        keyboard = [
            [InlineKeyboardButton("3분", callback_data="time_3")],
            [InlineKeyboardButton("10분", callback_data="time_10")],
            [InlineKeyboardButton("30분+", callback_data="time_30")]
        ]
        await query.edit_message_text("오늘 가능한 시간은?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("time"):
        keyboard = [
            [InlineKeyboardButton("문서 열기", callback_data="action_1")],
            [InlineKeyboardButton("할일 1개 적기", callback_data="action_2")],
            [InlineKeyboardButton("3분 정리", callback_data="action_3")]
        ]
        await query.edit_message_text("오늘은 이 중 하나 해볼까요?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("action"):
        keyboard = [
            [InlineKeyboardButton("완료", callback_data="done")],
            [InlineKeyboardButton("조금 함", callback_data="partial")],
            [InlineKeyboardButton("못함", callback_data="fail")]
        ]
        await query.edit_message_text("완료했어요?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "done":
        await query.edit_message_text("좋아요. 오늘은 연결됐어요 🔥")

    elif data == "partial":
        await query.edit_message_text("이 정도면 충분히 이어졌어요 👍")

    elif data == "fail":
        keyboard = [
            [InlineKeyboardButton("회복하기", callback_data="recovery")]
        ]
        await query.edit_message_text("괜찮아요. 다시 시작할까요?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "recovery":
        keyboard = [
            [InlineKeyboardButton("물 한 잔 마시기", callback_data="recover_done")],
            [InlineKeyboardButton("1분 정리", callback_data="recover_done")],
            [InlineKeyboardButton("할 일 1개 적기", callback_data="recover_done")]
        ]
        await query.edit_message_text("가장 쉬운 것 하나만 해볼까요?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "recover_done":
        await query.edit_message_text("복귀 성공 👌")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()


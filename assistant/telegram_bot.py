import os
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from telegram import Update
from dotenv import load_dotenv
from .brain import get_response

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_raw_user_id = os.getenv("MY_USER_ID", "")
USER_ID = int(_raw_user_id) if _raw_user_id.isdigit() else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey, I'm Rick! Wubba lubba dub dub! Talk to me or use voice on my main console.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    history = context.chat_data.get("history")
    reply, updated_history = get_response(user_msg, history)
    context.chat_data["history"] = updated_history
    await update.message.reply_text(reply)


def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Telegram bot started...")
    app.run_polling()


async def send_notification(text: str):
    if USER_ID is None:
        print("send_notification: MY_USER_ID is not configured; skipping.")
        return
    from telegram import Bot
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=USER_ID, text=text)

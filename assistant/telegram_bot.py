import os
import warnings

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from .brain import get_response

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_user_id_str = os.getenv("MY_USER_ID", "")
if not _user_id_str:
    warnings.warn("MY_USER_ID is not set. Notifications will not be sent.", RuntimeWarning)
    USER_ID = 0
else:
    USER_ID = int(_user_id_str)

# Per-user conversation history (keyed by Telegram user ID)
_chat_history: dict[int, list] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    _chat_history.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "Hello! I'm your AI assistant. You can chat with me here or use voice on my host device."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    uid = update.effective_user.id
    user_msg = update.message.text
    history = _chat_history.get(uid, [])
    reply, history = get_response(user_msg, history)
    _chat_history[uid] = history
    await update.message.reply_text(reply)


def run_bot():
    """Build and start the Telegram bot (blocking)."""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Telegram bot started...")
    app.run_polling()


async def send_notification(text: str):
    """Send a message to the configured Telegram user ID."""
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=USER_ID, text=text)

import logging
import telegram
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database.db import Database
from keyboards import get_main_menu_keyboard
from config import ADMIN_ID

logger = logging.getLogger(__name__)
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(
        user_id=user.id,
        first_name=user.first_name,
        username=user.username
    )
    
    await update.message.reply_text(
        "Добро пожаловать в магазин!",
        reply_markup=get_main_menu_keyboard(user.id)
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    logger.error(f"Ошибка: {error}", exc_info=error)
    
    if isinstance(error, telegram.error.BadRequest) and "Query is too old" in str(error):
        return
    
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"Произошла ошибка:\n{error}\n\nUpdate: {update}"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения админу: {e}")

def setup_common_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error_handler)
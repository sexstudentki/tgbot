import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import admin, shop, support, common
from config import BOT_TOKEN
from handlers.admin import setup_admin_handlers
from handlers.shop import setup_shop_handlers
from database.db import Database

# Инициализация
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    db = Database()
    if not db.connect():
        logger.error("Не удалось подключиться к базе данных!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", common.start))
    application.add_handler(CommandHandler("add", admin.add_item))
    application.add_handler(CommandHandler("add_all", admin.add_all_items))
    application.add_handler(CommandHandler("users", admin.show_users))
    application.add_handler(CommandHandler("addadmin", admin.add_admin))
    
    # Регистрация callback обработчиков
    application.add_handler(CallbackQueryHandler(common.button))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, common.handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(common.error_handler)

    setup_admin_handlers(application)
    setup_shop_handlers(application)    
    
    logger.info("Бот запущен...")
    application.run_polling()
    db.close()

if __name__ == "__main__":
    main()
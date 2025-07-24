from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    Application
)
from database.db import Database
from keyboards import get_support_ticket_keyboard

db = Database()
support_chats = {}  # {message_id: {'user_id': int, 'admin_id': int, 'user_message': str}}

async def request_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Напишите ваше сообщение в поддержку:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ])
    )
    context.user_data["awaiting_support"] = True

async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_support"):
        return
    
    user = update.effective_user
    message = update.message.text
    
    # Отправка сообщения админам
    admins = db.get_admins()
    for admin in admins:
        try:
            msg = await context.bot.send_message(
                admin['user_id'],
                f"📨 Новое сообщение в поддержку:\n\n"
                f"👤 Пользователь: @{user.username or user.id}\n"
                f"🆔 ID: {user.id}\n\n"
                f"📝 Сообщение:\n{message}",
                reply_markup=get_support_ticket_keyboard(user.id)
            )
            support_chats[msg.message_id] = {
                "user_id": user.id,
                "admin_id": admin['user_id'],
                "user_message": message
            }
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")
    
    await update.message.reply_text(
        "Ваше сообщение отправлено в поддержку. Спасибо!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
        ])
    )
    context.user_data["awaiting_support"] = False

async def close_support_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[2])
    await query.edit_message_text("✅ Тикет закрыт")
    
    await context.bot.send_message(
        user_id,
        "✅ Ваш запрос в поддержку закрыт. Спасибо за обращение!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
        ])
    )

def setup_support_handlers(application):
    application.add_handler(CallbackQueryHandler(request_support_message, pattern="^support$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message))
    application.add_handler(CallbackQueryHandler(close_support_ticket, pattern="^close_ticket_"))
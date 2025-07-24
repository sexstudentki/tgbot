from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
from database.db import Database
from keyboards import (  # Убрали точку в начале импорта
    get_admin_keyboard,
    get_manage_items_keyboard,
    get_stats_keyboard,
    get_edit_item_keyboard,
    get_confirmation_keyboard,
    get_pagination_keyboard
)
from utils import is_admin, extract_price_number  # Убрали точку в начале импорта
from config import ADMIN_ID

db = Database()

# ========== Админ панель ==========
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    if isinstance(update, Update):
        await update.message.reply_text(
            "👑 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
    else:
        await update.edit_message_text(
            "👑 Админ-панель",
            reply_markup=get_admin_keyboard()
        )

async def show_manage_items_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    await query.edit_message_text(
        "🛍 Управление товарами",
        reply_markup=get_manage_items_keyboard()
    )

async def show_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    await query.edit_message_text(
        "📊 Статистика продаж",
        reply_markup=get_stats_keyboard()
    )

# ========== Управление пользователями ==========
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    await show_users_page(update, user_id, page)

async def show_users_page(update: Update, user_id: int, page: int):
    if not is_admin(user_id):
        return
    
    users_per_page = 10
    offset = (page - 1) * users_per_page
    users = db.get_all_users(limit=users_per_page, offset=offset)
    total_users = db.get_user_count()
    total_pages = (total_users + users_per_page - 1) // users_per_page
    
    message = f"📊 Список пользователей (Страница {page}/{total_pages}):\n\n"
    for i, user in enumerate(users, 1):
        username = f"@{user['username']}" if user['username'] else "нет"
        reg_date = user['registration_date'].strftime("%d.%m.%Y %H:%M")
        message += (
            f"{i + offset}. ID: {user['user_id']}\n"
            f"   👤 Имя: {user['first_name']}\n"
            f"   📛 Юзернейм: {username}\n"
            f"   📅 Дата регистрации: {reg_date}\n"
            f"   {'👑 Админ' if user['is_admin'] else ''}\n\n"
        )
    
    keyboard = get_pagination_keyboard(page, total_pages)
    keyboard.inline_keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    
    if isinstance(update, Update):
        await update.message.reply_text(message, reply_markup=keyboard)
    else:
        await update.edit_message_text(message, reply_markup=keyboard)

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /addadmin <user_id>\nПример: /addadmin 123456789"
        )
        return
    
    try:
        new_admin_id = int(context.args[0])
        if db.add_admin(new_admin_id):
            await update.message.reply_text(f"✅ Пользователь {new_admin_id} добавлен как админ")
            try:
                await context.bot.send_message(
                    new_admin_id,
                    "🎉 Вас добавили как админа этого бота!\nТеперь вам доступны админские команды."
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ Не удалось добавить админа")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. ID должен быть числом")

# ========== Управление товарами ==========
async def show_edit_item_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    item_id = int(query.data.split('_')[2])
    item = db.get_items(item_id=item_id)[0]
    
    text = (
        f"✏️ Редактирование товара:\n\n"
        f"Название: {item['name']}\n"
        f"Цена: {item['price']}\n"
        f"Количество: {item['quantity']}\n"
        f"Описание: {item['description']}"
    )
    
    await query.edit_message_text(text, reply_markup=get_edit_item_keyboard(item_id))

async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    item_id = int(query.data.split('_')[2])
    item = db.get_items(item_id=item_id)[0]
    context.user_data["item_to_delete"] = item_id
    
    await query.edit_message_text(
        f"Вы уверены, что хотите удалить товар:\n{item['name']}?",
        reply_markup=get_confirmation_keyboard()
    )

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    item_id = context.user_data.get("item_to_delete")
    if item_id and db.delete_item(item_id):
        await query.edit_message_text("✅ Товар удален")
    else:
        await query.edit_message_text("❌ Ошибка при удалении")
    
    await show_admin_panel(query, query.from_user.id)

# ========== Статистика ==========
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    period = query.data.split('_')[1]
    period_names = {'all_time': 'за все время', 'weekly': 'за неделю', 'daily': 'за день'}
    stats = db.get_sales_stats(period)
    
    text = f"📊 Статистика продаж ({period_names[period]}):\n\n"
    if stats['items']:
        for item in stats['items']:
            text += f"{item['name']}: {item['sold']} шт. = {item['total']} RUB\n"
        text += f"\n💵 Доход за период: {stats['period_sum']} RUB"
    else:
        text += "Нет данных"
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_stats")]
        ])
    )

def setup_admin_handlers(application):
    # Команды
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("users", show_users))
    
    # Callback-обработчики
    application.add_handler(CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(show_manage_items_menu, pattern="^admin_manage_items$"))
    application.add_handler(CallbackQueryHandler(show_stats_menu, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(show_users_page, pattern="^users_page_"))
    application.add_handler(CallbackQueryHandler(show_edit_item_menu, pattern="^edit_item_"))
    application.add_handler(CallbackQueryHandler(confirm_delete_item, pattern="^delete_item_"))
    application.add_handler(CallbackQueryHandler(delete_item, pattern="^confirm_delete$"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="^stats_"))
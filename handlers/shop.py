from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # Добавляем импорт
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.db import Database
from ..keyboards import (
    get_shop_categories_keyboard,
    get_shop_items_keyboard,
    get_item_detail_keyboard
)
from ..utils import is_admin

db = Database()

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "🏪 Выберите категорию:"
    keyboard = get_shop_categories_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard)

async def show_category_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split('_')[1])
    items = db.get_items(category_id)
    category_name = db.get_category_name(category_id)
    
    text = f"{category_name}:\n\n"
    for item in items:
        item_name = item.get('name', 'Без названия')
        price = item.get('price', '0 RUB')
        quantity = item.get('quantity', 0)
        
        text += f"• {item_name} - {price}"
        text += f" ({quantity} шт.)" if quantity > 0 else " (Нет в наличии)"
        text += "\n"
    
    keyboard = get_shop_items_keyboard(category_id)
    await query.edit_message_text(text, reply_markup=keyboard)

async def handle_item_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    item_id = int(query.data.split('_')[1])
    items = db.get_items(item_id=item_id)
    
    if not items:
        await query.answer("Товар не найден!", show_alert=True)
        return
    
    item = items[0]
    text = (
        f"🎁 {item['name']}\n"
        f"💰 Цена: {item['price']}\n"
        f"📝 Описание: {item['description']}\n\n"
    )
    
    if item['quantity'] <= 0:
        text += "😔 Товар закончился"
    
    keyboard = get_item_detail_keyboard(item, user_id)
    await query.edit_message_text(text, reply_markup=keyboard)

async def process_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    item_id = int(query.data.split('_')[1])
    item = db.get_items(item_id=item_id)[0]
    
    if item['quantity'] <= 0:
        await query.answer("😔 Товар закончился!", show_alert=True)
        return
    
    if not db.update_item_quantity(item['id'], -1):
        await query.answer("❌ Ошибка при покупке!", show_alert=True)
        return
    
    # Записываем покупку
    db.record_purchase(user_id, item['id'], 1, item['price'])
    
    success_text = (
        f"🎉 Поздравляем с покупкой!\n"
        f"📦 Товар: {item['name']}\n"
        f"💵 Цена: {item['price']}\n\n"
        f"✅ Товар добавлен в ваш инвентарь.\n"
        f"🛒 Для получения свяжитесь с администратором."
    )
    
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("В главное меню", callback_data="back_to_main")]
        ])
    )
    
    # Уведомление админам
    if is_admin(user_id):
        return
        
    admins = db.get_admins()
    for admin in admins:
        try:
            await context.bot.send_message(
                admin['user_id'],
                f"🛒 Новая покупка:\n\n"
                f"👤 Пользователь: @{query.from_user.username or query.from_user.id}\n"
                f"📦 Товар: {item['name']}\n"
                f"🏷 Категория: {item['category_name']}\n"
                f"💵 Цена: {item['price']}\n"
                f"📊 Осталось: {item['quantity']} шт."
            )
        except Exception as e:
            print(f"Ошибка уведомления админа: {e}")

def setup_shop_handlers(application):
    application.add_handler(CallbackQueryHandler(show_categories, pattern="^shop$"))
    application.add_handler(CallbackQueryHandler(show_category_items, pattern="^category_"))
    application.add_handler(CallbackQueryHandler(handle_item_selection, pattern="^item_"))
    application.add_handler(CallbackQueryHandler(process_purchase, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(show_categories, pattern="^back_to_shop$"))
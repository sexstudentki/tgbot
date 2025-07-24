from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.db import Database
from config import ADMIN_ID

db = Database()

def get_main_menu_keyboard(user_id):
    buttons = [
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
    ]
    
    if user_id == ADMIN_ID or db.is_admin(user_id):
        buttons.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(buttons)

def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🛍 Управление товарами", callback_data="admin_manage_items")],
        [InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ])

def get_manage_items_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить товар", callback_data="add_item")],
        [InlineKeyboardButton("✏️ Редактировать товар", callback_data="edit_item")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
    ])

def get_stats_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕒 За все время", callback_data="stats_all_time")],
        [InlineKeyboardButton("📅 За неделю", callback_data="stats_weekly")],
        [InlineKeyboardButton("📆 За день", callback_data="stats_daily")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
    ])

def get_shop_categories_keyboard():
    categories = db.get_categories()
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(
            category['name'],
            callback_data=f"category_{category['id']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)

def get_shop_items_keyboard(category_id):
    items = db.get_items(category_id)
    buttons = []
    for item in items:
        item_name = item.get('name', 'Без названия')
        price = item.get('price', '0 RUB')
        quantity = item.get('quantity', 0)
        
        if quantity <= 0:
            btn_text = f"~~{item_name} - {price}~~ (Нет в наличии)"
        else:
            btn_text = f"{item_name} - {price} ({quantity} шт.)"
        
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"item_{item['id']}")])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_shop")])
    return InlineKeyboardMarkup(buttons)

def get_item_detail_keyboard(item, user_id):
    if item['quantity'] <= 0:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"category_{item['category_id']}"
            )]
        ])
    
    buttons = []
    if user_id == ADMIN_ID or db.is_admin(user_id):
        buttons.append(
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_item_{item['id']}")
        )
    
    buttons.extend([
        InlineKeyboardButton("✅ Купить", callback_data=f"buy_{item['id']}"),
        InlineKeyboardButton("🔙 Назад", callback_data=f"category_{item['category_id']}")
    ])
    
    return InlineKeyboardMarkup([buttons])

def get_edit_item_keyboard(item_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Название", callback_data=f"edit_field_{item_id}_name")],
        [InlineKeyboardButton("💰 Цена", callback_data=f"edit_field_{item_id}_price")],
        [InlineKeyboardButton("📦 Количество", callback_data=f"edit_field_{item_id}_quantity")],
        [InlineKeyboardButton("📝 Описание", callback_data=f"edit_field_{item_id}_description")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_item_{item_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_items")]
    ])

def get_pagination_keyboard(page, total_pages, prefix="users_page"):
    keyboard = []
    if page > 1:
        keyboard.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_{page-1}"))
    if page < total_pages:
        keyboard.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}_{page+1}"))
    return InlineKeyboardMarkup([keyboard])

def get_confirmation_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да", callback_data="confirm_delete")],
        [InlineKeyboardButton("❌ Нет", callback_data="cancel_delete")]
    ])

def get_support_ticket_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ответ отправлен", callback_data=f"close_ticket_{user_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_ticket_{user_id}")]
    ])
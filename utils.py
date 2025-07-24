from database.db import Database
from config import ADMIN_ID  # Добавляем импорт

db = Database()

def is_admin(user_id):
    """Проверяет, является ли пользователь админом"""
    return user_id == ADMIN_ID or db.is_admin(user_id)

def extract_price_number(price_str):
    """Извлекает числовое значение из строки цены"""
    if not price_str:
        return 0
    
    if isinstance(price_str, (int, float)):
        return int(price_str)
    
    try:
        digits = ''.join(c for c in str(price_str) if c.isdigit())
        return int(digits) if digits else 0
    except (ValueError, TypeError):
        return 0
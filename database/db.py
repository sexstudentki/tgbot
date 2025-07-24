import mysql.connector
from mysql.connector import Error
from .models import Category, Item, User, Purchase
from ..shop_items import SHOP_ITEMS
from ..utils import extract_price_number

class Database:
    def __init__(self):
        self.connection = None
        self.shop_items = SHOP_ITEMS
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='telegram_shop',
                autocommit=True
            )
            print("✅ Успешное подключение к MySQL")
            return True
        except Error as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            return False
    
    def get_categories(self):
        """Возвращает список категорий с русскими названиями"""
        return [
            {'id': 1, 'name': 'Наборы'},
            {'id': 2, 'name': 'Оружие'},
            {'id': 3, 'name': 'Броня'},
            {'id': 4, 'name': 'Буст'},
            {'id': 5, 'name': 'Обвесы/Другое'}
        ]
    
    def get_items(self, category_id=None, item_id=None):
        """Получаем товары из базы данных"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return []
                    
            cursor = self.connection.cursor(dictionary=True)
            
            if item_id:
                cursor.execute("""
                    SELECT i.*, 
                    CASE i.category_id
                        WHEN 1 THEN 'kits'
                        WHEN 2 THEN 'weapons'
                        WHEN 3 THEN 'armor'
                        WHEN 4 THEN 'boost'
                        WHEN 5 THEN 'other'
                    END as category_key
                    FROM items i
                    WHERE i.id = %s
                """, (item_id,))
                
                db_item = cursor.fetchone()
                if not db_item:
                    return []
                
                category_key = db_item['category_key']
                item_data = SHOP_ITEMS.get(category_key, {}).get('ru', {}).get(db_item['name'], {})
                
                return [{
                    'id': db_item['id'],
                    'name': item_data.get('name', db_item['name']),
                    'price': db_item['price'] or item_data.get('price', '0 RUB'),
                    'description': item_data.get('description', 'Нет описания'),
                    'quantity': db_item['quantity'],
                    'category_id': db_item['category_id'],
                    'category_name': self.get_category_name(db_item['category_id']),
                    'category_key': category_key
                }]
            
            if category_id:
                cursor.execute("""
                    SELECT i.*, 
                    CASE i.category_id
                        WHEN 1 THEN 'kits'
                        WHEN 2 THEN 'weapons'
                        WHEN 3 THEN 'armor'
                        WHEN 4 THEN 'boost'
                        WHEN 5 THEN 'other'
                    END as category_key
                    FROM items i
                    WHERE i.category_id = %s
                """, (category_id,))
                
                db_items = cursor.fetchall()
                items = []
                
                for db_item in db_items:
                    category_key = db_item['category_key']
                    item_data = SHOP_ITEMS.get(category_key, {}).get('ru', {}).get(db_item['name'], {})
                    
                    items.append({
                        'id': db_item['id'],
                        'name': item_data.get('name', db_item['name']),
                        'price': db_item['price'] or item_data.get('price', '0 RUB'),
                        'description': item_data.get('description', 'Нет описания'),
                        'quantity': db_item['quantity'],
                        'category_id': db_item['category_id'],
                        'category_name': self.get_category_name(db_item['category_id']),
                        'category_key': category_key
                    })
                
                return items
            
            return []
            
        except Error as e:
            print(f"❌ Ошибка при загрузке товаров: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()


    def get_category_name(self, category_id):
        """Возвращает русское название категории по ID"""
        category_map = {
            1: "Наборы",
            2: "Оружие",
            3: "Броня", 
            4: "Буст",
            5: "Обвесы/Другое"
        }
        return category_map.get(category_id, "Неизвестная категория")
    
    def get_item_quantity(self, category_id, item_name):
        """Получаем текущее количество товара"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return None
                    
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT quantity FROM items 
                WHERE category_id = %s AND name = %s
                LIMIT 1
            """, (category_id, item_name))
            
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            print(f"❌ Ошибка получения количества: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def update_item_quantity(self, item_id, change):
        """Обновляем количество товара в БД"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE items SET quantity = GREATEST(0, quantity + %s) WHERE id = %s",
                (change, item_id)
            )
            return cursor.rowcount > 0
        except Error as e:
            print(f"❌ Ошибка обновления количества: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def add_item_to_db(self, category_id, item_name, quantity, price=None):
        """Добавляем или обновляем товар в БД"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, quantity FROM items 
                WHERE name = %s AND category_id = %s
                LIMIT 1
            """, (item_name, category_id))
            
            existing_item = cursor.fetchone()
            
            if existing_item:
                item_id, current_quantity = existing_item
                if current_quantity + quantity < 0:
                    return False
                
                if price:
                    cursor.execute("""
                        UPDATE items 
                        SET quantity = GREATEST(0, quantity + %s), price = %s 
                        WHERE id = %s
                    """, (quantity, price, item_id))
                else:
                    cursor.execute("""
                        UPDATE items 
                        SET quantity = GREATEST(0, quantity + %s) 
                        WHERE id = %s
                    """, (quantity, item_id))
            else:
                if quantity < 0:
                    return False
                    
                if price:
                    cursor.execute("""
                        INSERT INTO items (category_id, name, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (category_id, item_name, quantity, price))
                else:
                    category_names = list(SHOP_ITEMS.keys())
                    category_name = category_names[category_id - 1]
                    default_price = SHOP_ITEMS.get(category_name, {}).get('ru', {}).get(item_name, {}).get('price')
                    
                    cursor.execute("""
                        INSERT INTO items (category_id, name, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (category_id, item_name, quantity, default_price))
            
            return True
        except Error as e:
            print(f"❌ Ошибка добавления товара: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def register_user(self, user_id, first_name, username):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            
            if first_name:
                first_name = first_name.encode('utf-8', 'ignore').decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (user_id, first_name, username, registration_date)
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                    first_name = VALUES(first_name),
                    username = VALUES(username)
            """, (user_id, first_name, username))
            return True
        except Error as e:
            print(f"❌ Ошибка регистрации пользователя: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def add_admin(self, user_id):
        """Добавляет пользователя как админа"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_admin = TRUE 
                WHERE user_id = %s
            """, (user_id,))
            return cursor.rowcount > 0
        except Error as e:
            print(f"❌ Ошибка добавления админа: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def record_purchase(self, user_id, item_id, quantity, total_price):
        """Сохраняет покупку в базе данных"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO purchases (user_id, item_id, quantity, purchase_date)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, item_id, quantity))
            return True
        except Error as e:
            print(f"❌ Ошибка записи покупки: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_sales_stats(self, period):
        """Статистика продаж с суммой за указанный период"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return {'items': [], 'period_sum': 0}

            cursor = self.connection.cursor(dictionary=True)

            if period == "daily":
                query = """
                    SELECT i.name, i.price, COUNT(p.id) as sold 
                    FROM purchases p
                    JOIN items i ON p.item_id = i.id
                    WHERE DATE(p.purchase_date) = CURDATE()
                    GROUP BY i.name, i.price
                    ORDER BY sold DESC
                """
                sum_query = """
                    SELECT SUM(i.price) as period_sum 
                    FROM purchases p
                    JOIN items i ON p.item_id = i.id
                    WHERE DATE(p.purchase_date) = CURDATE()
                """
            elif period == "weekly":
                query = """
                    SELECT i.name, i.price, COUNT(p.id) as sold 
                    FROM purchases p
                    JOIN items i ON p.item_id = i.id
                    WHERE YEARWEEK(p.purchase_date) = YEARWEEK(NOW())
                    GROUP BY i.name, i.price
                    ORDER BY sold DESC
                """
                sum_query = """
                    SELECT SUM(i.price) as period_sum 
                    FROM purchases p
                    JOIN items i ON p.item_id = i.id
                    WHERE YEARWEEK(p.purchase_date) = YEARWEEK(NOW())
                """
            else:  # all_time
                query = """
                    SELECT i.name, i.price, COUNT(p.id) as sold 
                    FROM purchases p
                    JOIN items i ON p.item_id = i.id
                    GROUP BY i.name, i.price
                    ORDER BY sold DESC
                """
                sum_query = """
                    SELECT SUM(i.price) as period_sum 
                    FROM purchases p
                    JOIN items i ON p.item_id = i.id
                """

            cursor.execute(query)
            stats = []
            for row in cursor.fetchall():
                price = extract_price_number(row['price'])
                sold = row['sold']
                total = price * sold
                
                stats.append({
                    'name': row['name'],
                    'price': price,
                    'sold': sold,
                    'total': total
                })
            
            cursor.execute(sum_query)
            sum_result = cursor.fetchone()
            period_sum = sum_result['period_sum'] or 0 if sum_result else 0
            
            return {
                'items': stats,
                'period_sum': period_sum
            }
            
        except Error as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return {'items': [], 'period_sum': 0}
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_admins(self):
        """Возвращает список всех админов"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection: 
                    return []
                    
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT user_id 
                FROM users 
                WHERE is_admin = TRUE
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Ошибка получения списка админов: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()

    def delete_item(self, item_id):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
            return cursor.rowcount > 0
        except Error as e:
            print(f"❌ Ошибка удаления товара: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_all_users(self, limit=None, offset=None):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return []

            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT user_id, first_name, username, 
                       registration_date, is_admin 
                FROM users 
                ORDER BY registration_date DESC
            """
            
            if limit is not None:
                query += f" LIMIT {limit}"
                if offset is not None:
                    query += f" OFFSET {offset}"
            
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Ошибка получения пользователей: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_user_count(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return 0

            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
        except Error as e:
            print(f"❌ Ошибка подсчёта пользователей: {e}")
            return 0
        finally:
            if 'cursor' in locals():
                cursor.close()

    def update_item_field(self, item_id, field, value):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            
            if field == 'quantity':
                value = int(value)
            
            cursor.execute(f"UPDATE items SET {field} = %s WHERE id = %s", (value, item_id))
            return cursor.rowcount > 0
        except Error as e:
            print(f"❌ Ошибка обновления товара: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def is_admin(self, user_id):
        """Проверяет, является ли пользователь админом"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
                    
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT is_admin 
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()
            return result and result[0]
        except Error as e:
            print(f"❌ Ошибка проверки прав админа: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Соединение с MySQL закрыто")
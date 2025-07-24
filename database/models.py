from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    user_id: int
    first_name: str
    username: str
    registration_date: datetime
    is_admin: bool = False

@dataclass
class Item:
    id: int
    name: str
    price: str
    description: str
    quantity: int
    category_id: int
    category_name: str = ""
    category_key: str = ""

@dataclass 
class Category:
    id: int
    name: str

@dataclass
class Purchase:
    user_id: int
    item_id: int
    price: str
    purchase_date: datetime
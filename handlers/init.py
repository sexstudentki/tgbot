from .admin import setup_admin_handlers
from .shop import setup_shop_handlers
from .common import setup_common_handlers
from .support import setup_support_handlers

__all__ = [
    'setup_admin_handlers',
    'setup_shop_handlers',
    'setup_common_handlers',
    'setup_support_handlers'
]
"""
API Routers package.
"""

from .auth import router as auth_router
from .users import router as users_router
from .products import router as products_router
from .customers import router as customers_router
from .warehouse import router as warehouse_router
from .sales import router as sales_router
from .reports import router as reports_router
from .sms import router as sms_router
from .dashboard import router as dashboard_router
from .expenses import router as expenses_router
from .suppliers import router as suppliers_router


__all__ = [
    "auth_router",
    "users_router",
    "products_router",
    "customers_router",
    "warehouse_router",
    "sales_router",
    "reports_router",
    "sms_router",
    "dashboard_router",
    "expenses_router",
    "suppliers_router",
]

from .auth_controller import router as auth_router
from .customer_controller import router as customer_router
from .order_controller import router as order_router
from .service_controller import router as service_router
from .employee_controller import router as employee_router
from .contact_controller import router as contact_router

__all__ = [
    "auth_router",
    "customer_router",
    "order_router",
    "service_router",
    "employee_router",
    "contact_router"
]
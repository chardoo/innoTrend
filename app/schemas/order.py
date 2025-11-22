from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.customer import Customer
from app.models.order import OrderStatus
from app.models.service import Service

class OrderBase(BaseModel):
    customer_id: str
    service_id: str
    quantity: Optional[int] = None
    description: Optional[str] = None
    amount: float
    color: Optional[str] = None
    unit_price: Optional[float] = None
    status: Optional[OrderStatus] = None
    progress_notes: Optional[str] = None
    

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    service_id: Optional[str] = None
    quantity: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[OrderStatus] = None
    progress_notes: Optional[str] = None
    color: Optional[str] = None
    unit_price: Optional[float] = None

class OrderResponse(OrderBase):
    id: str
    order_number: str
    quantity: Optional[int] = None
    status: OrderStatus
    progress_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    color: Optional[str] = None
    unit_price: Optional[float] = None
    service_id: str
    service: Optional[Service] = None
    customer_id: str
    customer: Optional[Customer] = None
    
    class Config:
        from_attributes = True
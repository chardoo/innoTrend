from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Customer(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    phone: str
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
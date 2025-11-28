from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

from app.models.postgress_model import ExpenseType

# Expense Schemas
class ExpenseBase(BaseModel):
    date: datetime
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    type: ExpenseType
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    date: Optional[datetime] = None
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[ExpenseType] = None
    description: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
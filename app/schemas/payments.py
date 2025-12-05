from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.postgress_model import PaymentType, PaymentStatus

class PaymentRequest(BaseModel):
    payment_type: PaymentType
    amount: Optional[float] = Field(None, gt=0, description="Custom amount (optional)")
    description: Optional[str] = None

class PaymentInitializeResponse(BaseModel):
    payment_url: str
    payment_reference: str
    amount: float
    expires_at: datetime

class PaymentVerifyRequest(BaseModel):
    payment_reference: str

class PaymentResponse(BaseModel):
    id: str
    student_id: str
    payment_reference: str
    amount: float
    payment_type: PaymentType
    status: PaymentStatus
    description: Optional[str]
    verified_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


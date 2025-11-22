from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ContactBase(BaseModel):
    name: str
    email: EmailStr
    message: str
    phone: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageSend(BaseModel):
    recipient_ids: list[str]
    subject: str
    message: str
    send_via_email: bool = True
    send_via_sms: bool = False

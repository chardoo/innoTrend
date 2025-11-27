from pydantic import UUID4, BaseModel, EmailStr
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
    email: str
    name: str
    phone: Optional[str] = None
    message: str
    created_at: datetime
 
    
    
    class Config:
        from_attributes = True

class MessageSend(BaseModel):
    contact_ids: list[str]
    recipient_contacts: list[str]
    customers_ids: list[str]
    subject: str
    message: str
    send_via_email: bool = True
    send_via_sms: bool = False

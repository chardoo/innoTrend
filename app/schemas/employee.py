from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmployeeBase(BaseModel):
    name: str
    job_title: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    salary: Optional[float] = None
    referee: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    salary: Optional[float] = None
    referee: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


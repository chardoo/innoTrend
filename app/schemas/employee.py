from pydantic import UUID4, BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmployeeBase(BaseModel):
    name: str
    job_title: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    hire_date: Optional[datetime] = None  # FIXED: Added type annotation
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
    hire_date: Optional[datetime] = None  # FIXED: Made optional for updates
    image_url: Optional[str] = None
    salary: Optional[float] = None
    referee: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str  # CHANGED: Use int for PostgreSQL auto-increment ID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
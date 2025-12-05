from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.postgress_model import StudentStatus

# Student Account Schemas
class StudentRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(min_length=2, max_length=255)
    phone: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class StudentLogin(BaseModel):
    email: EmailStr
    password: str

# Admission Form Schemas
class AdmissionFormBase(BaseModel):
    # Personal Information
    full_name: str = Field(min_length=2, max_length=255)
    date_of_birth: datetime
    gender: Optional[str] = Field(None, max_length=20)
    phone: str = Field(min_length=10, max_length=50)
    address: str
    city: str = Field(max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(max_length=100)
    
    # Emergency Contact
    emergency_contact_name: str = Field(max_length=255)
    emergency_contact_phone: str = Field(min_length=10, max_length=50)
    emergency_contact_relationship: str = Field(max_length=100)
    
    # Academic Information
    previous_school: Optional[str] = Field(None, max_length=255)
    grade_level: str = Field(max_length=50)
    intended_major: Optional[str] = Field(None, max_length=255)
    start_date: datetime  # Fixed: Added colon and proper type annotation
    end_date: datetime    # Fixed: Added colon and proper type annotation

class AdmissionFormCreate(AdmissionFormBase):
    profile_image_url: Optional[str] = None
    document_urls: Optional[List[str]] = None

class AdmissionFormUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    previous_school: Optional[str] = None
    grade_level: Optional[str] = None
    intended_major: Optional[str] = None
    start_date: Optional[datetime] = None  # Fixed: Proper Optional syntax
    end_date: Optional[datetime] = None    # Fixed: Proper Optional syntax
    profile_image_url: Optional[str] = None
    document_urls: Optional[List[str]] = None

class StudentResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    previous_school: Optional[str]
    grade_level: Optional[str]
    intended_major: Optional[str]
    profile_image_url: Optional[str]
    document_urls: Optional[str]
    status: StudentStatus
    admission_date: Optional[datetime]  # Fixed: Changed from Optional[str] to Optional[datetime]
    start_date: Optional[datetime]      # Fixed: Proper Optional syntax
    end_date: Optional[datetime]        # Fixed: Proper Optional syntax
    rejection_reason: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StudentStatusUpdate(BaseModel):
    status: StudentStatus
    rejection_reason: Optional[str] = None
    
    @field_validator('rejection_reason')
    @classmethod
    def validate_rejection_reason(cls, v, info):
        if info.data.get('status') == StudentStatus.REJECTED and not v:
            raise ValueError('Rejection reason is required when status is REJECTED')
        return v

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentResponse
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.config.firebase import get_db
from app.middleware.auth_middleware import require_admin
from app.models.postgress_model import StudentStatus
from app.schemas.student import (
    StudentRegister,
    StudentLogin,
    AdmissionFormCreate,
    AdmissionFormUpdate,
    StudentResponse,
    StudentStatusUpdate,
    AuthResponse
)
from app.services.student_service import StudentService
from app.utils.helpers import create_access_token

# JWT Configuration (adjust these based on your existing auth setup)
SECRET_KEY = "your-secret-key-here"  # Use environment variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

student_router = APIRouter(prefix="/students", tags=["Students"])


async def get_current_student(
    token: str = Depends(lambda: None),  # Replace with your token dependency
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated student"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id: str = payload.get("sub")
        if student_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    student = await StudentService.get_student(db, student_id)
    if student is None:
        raise credentials_exception
    return student

# Public Endpoints (No Authentication Required)

@student_router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_student(
    student_data: StudentRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new student account"""
    student = await StudentService.create_student_account(db, student_data)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.id, "type": "student"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": student
    }

@student_router.post("/login", response_model=AuthResponse)
async def login_student(
    credentials: StudentLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login as a student"""
    student = await StudentService.authenticate_student(
        db, credentials.email, credentials.password
    )
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.id, "type": "student"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": student
    }

# Student Endpoints (Requires Student Authentication)

@student_router.get("/me", response_model=StudentResponse)
async def get_current_student_profile(
    current_student = Depends(get_current_student)
):
    """Get current student profile"""
    return current_student

@student_router.post("/admission-form", response_model=StudentResponse)
async def submit_admission_form(
    form_data: AdmissionFormCreate,
    db: AsyncSession = Depends(get_db),
    current_student = Depends(get_current_student)
):
    """Submit admission form"""
    return await StudentService.submit_admission_form(
        db, current_student.id, form_data
    )

@student_router.put("/admission-form", response_model=StudentResponse)
async def update_admission_form(
    form_data: AdmissionFormUpdate,
    db: AsyncSession = Depends(get_db),
    current_student = Depends(get_current_student)
):
    """Update admission form"""
    return await StudentService.update_admission_form(
        db, current_student.id, form_data
    )

# Admin Endpoints (Requires Admin Authentication)

@student_router.get("/", response_model=List[StudentResponse])
async def get_all_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[StudentStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all students with optional filters (Admin only)"""
    return await StudentService.get_students(
        db, skip, limit, status_filter, search
    )

@student_router.get("/statistics")
async def get_admission_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get admission statistics (Admin only)"""
    return await StudentService.get_admission_statistics(db)

@student_router.get("/{student_id}", response_model=StudentResponse)
async def get_student_by_id(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get student by ID (Admin only)"""
    return await StudentService.get_student(db, student_id)

@student_router.patch("/{student_id}/status", response_model=StudentResponse)
async def update_student_status(
    student_id: str,
    status_data: StudentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update student admission status (Admin only)"""
    return await StudentService.update_student_status(db, student_id, status_data)

@student_router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a student (Admin only)"""
    await StudentService.delete_student(db, student_id)
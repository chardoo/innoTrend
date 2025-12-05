from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from typing import List, Optional
from fastapi import HTTPException, status
import json
from passlib.context import CryptContext

from app.models.postgress_model import Student, StudentStatus
from app.schemas.student import (
    StudentRegister, 
    AdmissionFormCreate, 
    AdmissionFormUpdate,
    StudentStatusUpdate
)
from app.services.expenses import to_naive_utc
from app.utils.helpers import get_password_hash, verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class StudentService:
    

  
    @staticmethod
    async def create_student_account(
        db: AsyncSession, 
        student_data: StudentRegister
    ) -> Student:
        """Create a new student account"""
        # Check if email already exists
        result = await db.execute(
            select(Student).where(Student.email == student_data.email)
        )
        existing_student = result.scalar_one_or_none()
        
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create student with hashed password
        student = Student(
            email=student_data.email,
            password_hash=get_password_hash(student_data.password),
            full_name=student_data.full_name,
            phone=student_data.phone
        )
        
        db.add(student)
        await db.commit()
        await db.refresh(student)
        return student
    
    @staticmethod
    async def authenticate_student(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[Student]:
        """Authenticate a student"""
        result = await db.execute(
            select(Student).where(Student.email == email)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            return None
        
        if not verify_password(password, student.password_hash):
            return None
        
        if not student.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student account is inactive"
            )
        
        return student
    
    @staticmethod
    async def submit_admission_form(
        db: AsyncSession,
        student_id: str,
        form_data: AdmissionFormCreate
    ) -> Student:
        """Submit or update admission form"""
        result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        form_data.start_date = to_naive_utc(form_data.start_date)
        form_data.end_date = to_naive_utc(form_data.end_date)
        student = result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Convert document URLs list to JSON string
        document_urls_json = json.dumps(form_data.document_urls) if form_data.document_urls else None
        
        # Update student with admission form data
        update_data = form_data.model_dump(exclude={'document_urls'})
        for field, value in update_data.items():
            setattr(student, field, value)
        
        student.document_urls = document_urls_json
        student.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(student)
        return student
    
    @staticmethod
    async def get_student(db: AsyncSession, student_id: str) -> Student:
        """Get student by ID"""
        result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        return student
    
    @staticmethod
    async def get_students(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[StudentStatus] = None,
        search: Optional[str] = None
    ) -> List[Student]:
        """Get all students with optional filters"""
        query = select(Student).order_by(Student.created_at.desc())
        
        filters = []
        if status_filter:
            filters.append(Student.status == status_filter)
        
        if search:
            search_filter = or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
                Student.phone.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_admission_form(
        db: AsyncSession,
        student_id: str,
        form_data: AdmissionFormUpdate
    ) -> Student:
        """Update admission form"""
        student = await StudentService.get_student(db, student_id)
        
        form_data.start_date = to_naive_utc(form_data.start_date)
        form_data.end_date = to_naive_utc(form_data.end_date)
        update_data = form_data.model_dump(exclude_unset=True, exclude={'document_urls'})
        for field, value in update_data.items():
            setattr(student, field, value)
        
        # Handle document URLs if provided
        if form_data.document_urls is not None:
            student.document_urls = json.dumps(form_data.document_urls)
        
        student.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(student)
        return student
    
    @staticmethod
    async def update_student_status(
        db: AsyncSession,
        student_id: str,
        status_data: StudentStatusUpdate
    ) -> Student:
        """Update student admission status (Admin only)"""
        student = await StudentService.get_student(db, student_id)
        
        student.status = status_data.status
        
        if status_data.status == StudentStatus.APPROVED:
            student.admission_date = datetime.utcnow()
            student.rejection_reason = None
        elif status_data.status == StudentStatus.REJECTED:
            student.rejection_reason = status_data.rejection_reason
            student.admission_date = None
        elif status_data.status == StudentStatus.ENROLLED:
            if not student.admission_date:
                student.admission_date = datetime.utcnow()
        
        student.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(student)
        return student
    
    @staticmethod
    async def delete_student(db: AsyncSession, student_id: str) -> bool:
        """Delete a student (Admin only)"""
        student = await StudentService.get_student(db, student_id)
        await db.delete(student)
        await db.commit()
        return True
    
    @staticmethod
    async def get_admission_statistics(db: AsyncSession) -> dict:
        """Get admission statistics"""
        # Count by status
        status_query = select(
            Student.status,
            func.count(Student.id).label('count')
        ).group_by(Student.status)
        
        status_results = await db.execute(status_query)
        
        by_status = {}
        total_count = 0
        
        for student_status, count in status_results:
            by_status[student_status.value] = count
            total_count += count
        
        # Recent applications (last 30 days)
        thirty_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_query = select(func.count(Student.id)).where(
            Student.created_at >= thirty_days_ago
        )
        recent_result = await db.execute(recent_query)
        recent_count = recent_result.scalar()
        
        return {
            "total_students": total_count,
            "by_status": by_status,
            "recent_applications_30_days": recent_count,
            "pending_review": by_status.get(StudentStatus.PENDING.value, 0)
        }
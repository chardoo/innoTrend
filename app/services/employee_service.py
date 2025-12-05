from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.postgress_model import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services.expenses import to_naive_utc

class EmployeeService:
    @staticmethod
    async def create_employee(db: AsyncSession, employee: EmployeeCreate) -> EmployeeResponse:
        """Create a new employee"""
        employee.hire_date = to_naive_utc(employee.hire_date)
        db_employee = Employee(**employee.model_dump())
        db.add(db_employee)
        await db.commit()
        await db.refresh(db_employee)
        
        return EmployeeResponse.model_validate(db_employee)
    
    @staticmethod
    async def get_employee(db: AsyncSession, employee_id: str) -> EmployeeResponse:
        """Get employee by ID"""
        result = await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        return EmployeeResponse.model_validate(employee)
    
    @staticmethod
    async def list_employees(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[EmployeeResponse]:
        """List all employees with optional search"""
        query = select(Employee)
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                (Employee.name.ilike(search_pattern)) |
                (Employee.job_title.ilike(search_pattern))
            )
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        employees = result.scalars().all()
        
        return [EmployeeResponse.model_validate(e) for e in employees]
    
    @staticmethod
    async def update_employee(
        db: AsyncSession,
        employee_id: str,
        employee_update: EmployeeUpdate
    ) -> EmployeeResponse:
        """Update employee"""
        employee_update.hire_date = to_naive_utc(employee_update.hire_date)
        result = await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        update_data = employee_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)
        
        await db.commit()
        await db.refresh(employee)
        
        return EmployeeResponse.model_validate(employee)
    
    @staticmethod
    async def delete_employee(db: AsyncSession, employee_id: str) -> bool:
        """Delete employee"""
        result = await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        await db.delete(employee)
        await db.commit()
        return True
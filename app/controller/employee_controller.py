from fastapi import APIRouter, Depends, status
from typing import List, Optional
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services.employee_service import EmployeeService
from app.middleware.auth_middleware import require_admin, get_optional_user
from app.config.firebase import get_db
from sqlalchemy.ext.asyncio import  AsyncSession
router = APIRouter(prefix="/api/employees", tags=["Employees"])

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new employee (Admin only)"""
    employee_service = EmployeeService()
    return await employee_service.create_employee(db, employee)

@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_optional_user)
):
    """List all employees (Public endpoint)"""
    employee_service = EmployeeService()
    return await employee_service.list_employees(db, skip=skip, limit=limit, search=search)

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_optional_user)
):
    """Get employee by ID (Public endpoint)"""
    employee_service = EmployeeService()
    return await employee_service.get_employee(db,employee_id)

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update employee (Admin only)"""
    employee_service = EmployeeService()
    return await employee_service.update_employee(db, employee_id, employee)

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete employee (Admin only)"""
    employee_service = EmployeeService()
    await employee_service.delete_employee(db,employee_id)
    return {"message": "Employee deleted successfully"}

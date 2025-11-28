from datetime import datetime
from typing import List, Optional
from app.config.firebase import get_db
from fastapi import APIRouter, Depends, status, BackgroundTasks, Query
from app.middleware.auth_middleware import require_admin
from app.models.postgress_model import ExpenseType
from app.schemas.expenses import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services.expenses import ExpenseService
from sqlalchemy.ext.asyncio import  AsyncSession
expense_router = APIRouter(prefix="/expenses", tags=["Expenses"])

@expense_router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new expense (Admin only)"""
    return await ExpenseService.create_expense(db, expense_data)

@expense_router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get expense by ID (Admin only)"""
    return await ExpenseService.get_expense(db, expense_id)

@expense_router.get("/", response_model=List[ExpenseResponse])
async def get_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[ExpenseType] = None,
    start_date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all expenses with optional filters (Admin only)"""
    parsed_start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    parsed_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    return await ExpenseService.get_expenses(
        db, skip, limit, type, parsed_start, parsed_end
    )

@expense_router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update an expense (Admin only)"""
    return await ExpenseService.update_expense(db, expense_id, expense_data)

@expense_router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete an expense (Admin only)"""
    await ExpenseService.delete_expense(db, expense_id)

@expense_router.get("/statistics/summary")
async def get_expense_statistics(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    start_date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get expense statistics (Admin only)"""
    parsed_start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    parsed_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    return await ExpenseService.get_expense_statistics(
        db, year, month, parsed_start, parsed_end
    )

# ========== SERVICES ==========

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, extract, and_, or_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.postgress_model import Expense, ExpenseType
from app.schemas.expenses import ExpenseCreate, ExpenseUpdate


def to_naive_utc(dt: datetime) -> datetime:
    # convert aware -> UTC naive, leave naive as-is
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return 
class ExpenseService:
    @staticmethod
    async def create_expense(db: AsyncSession, expense_data: ExpenseCreate) -> Expense:
        """Create a new expense"""
        print("Creating expense with data:", expense_data)
        expense_data.date = to_naive_utc(expense_data.date)
        expense = Expense(**expense_data.model_dump())
        print("Expense object created:", expense)
        db.add(expense)
        print("Expense added to session")
        await db.commit()
        await db.refresh(expense)
        return expense
    
    @staticmethod
    async def get_expense(db: AsyncSession, expense_id: str) -> Optional[Expense]:
        """Get expense by ID"""
        result = await db.execute(select(Expense).where(Expense.id == expense_id))
        expense = result.scalar_one_or_none()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        return expense
    
    @staticmethod
    async def get_expenses(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        type: Optional[ExpenseType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Expense]:
        """Get all expenses with optional filters"""
        query = select(Expense).order_by(Expense.date.desc())
        
        filters = []
        if type:
            filters.append(Expense.type == type)
        if start_date:
            filters.append(Expense.date >= start_date)
        if end_date:
            filters.append(Expense.date <= end_date)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_expense(
        db: AsyncSession,
        expense_id: str,
        expense_data: ExpenseUpdate
    ) -> Expense:
        """Update an expense"""
        expense = await ExpenseService.get_expense(db, expense_id)
        
        update_data = expense_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)
        
        expense.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(expense)
        return expense 
    
    @staticmethod
    async def delete_expense(db: AsyncSession, expense_id: str) -> bool:
        """Delete an expense"""
        expense = await ExpenseService.get_expense(db, expense_id)
        await db.delete(expense)
        await db.commit()
        return True
    
    @staticmethod
    async def get_expense_statistics(
        db: AsyncSession,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get expense statistics"""
        
        filters = []
        if year:
            filters.append(extract('year', Expense.date) == year)
        if month and year:
            filters.append(extract('month', Expense.date) == month)
        if start_date:
            filters.append(Expense.date >= start_date)
        if end_date:
            filters.append(Expense.date <= end_date)
        
        # Total expenses by type
        type_query = select(
            Expense.type,
            func.count(Expense.id).label('count'),
            func.sum(Expense.amount).label('total')
        ).group_by(Expense.type)
        
        if filters:
            type_query = type_query.where(and_(*filters))
        
        type_results = await db.execute(type_query)
        
        by_type = {}
        total_amount = 0.0
        total_count = 0
        
        for exp_type, count, total in type_results:
            amount = float(total) if total else 0.0
            by_type[exp_type.value] = {
                "count": count,
                "total": amount
            }
            total_amount += amount
            total_count += count
        
        # Monthly breakdown if year is specified
        monthly_breakdown = None
        if year:
            monthly_query = select(
                extract('month', Expense.date).label('month'),
                func.count(Expense.id).label('count'),
                func.sum(Expense.amount).label('total')
            ).where(extract('year', Expense.date) == year)
            
            if filters:
                monthly_query = monthly_query.where(and_(*filters))
            
            monthly_query = monthly_query.group_by('month')
            monthly_results = await db.execute(monthly_query)
            
            monthly_breakdown = {}
            for month_num in range(1, 13):
                monthly_breakdown[month_num] = {
                    "month": month_num,
                    "month_name": datetime(year, month_num, 1).strftime('%B'),
                    "count": 0,
                    "total": 0.0
                }
            
            for month_num, count, total in monthly_results:
                month_int = int(month_num)
                monthly_breakdown[month_int]["count"] = count
                monthly_breakdown[month_int]["total"] = float(total) if total else 0.0
        
        return {
            "total_expenses": total_amount,
            "total_count": total_count,
            "average_expense": total_amount / total_count if total_count > 0 else 0.0,
            "by_type": by_type,
            "monthly_breakdown": list(monthly_breakdown.values()) if monthly_breakdown else None,
            "filters": {
                "year": year,
                "month": month,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }


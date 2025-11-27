from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.services.customer_service import CustomerService
from app.middleware.auth_middleware import require_admin
from app.config.firebase import get_db
from sqlalchemy.ext.asyncio import  AsyncSession
router = APIRouter(prefix="/api/customers", tags=["Customers"])

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
        db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new customer (Admin only)"""
    customer_service = CustomerService()
    return await customer_service.create_customer(db, customer)

@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """List all customers with search (Admin only)"""
    customer_service = CustomerService()
    return await customer_service.list_customers(db, skip=skip, limit=limit, search=search)

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get customer by ID (Admin only)"""
    customer_service = CustomerService()
    return await customer_service.get_customer(db,customer_id)

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
        db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update customer (Admin only)"""
    customer_service = CustomerService()
    return await customer_service.update_customer(db, customer_id, customer)

@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete customer (Admin only)"""
    customer_service = CustomerService()
    await customer_service.delete_customer(db, customer_id)
    return {"message": "Customer deleted successfully"}

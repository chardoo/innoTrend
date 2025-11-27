from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.postgress_model import Customer, Order
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

class CustomerService:
    @staticmethod
    async def create_customer(db: AsyncSession, customer: CustomerCreate) -> CustomerResponse:
        """Create a new customer"""
        # Check if customer exists
        result = await db.execute(
            select(Customer).where(Customer.email == customer.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this email already exists"
            )
        
        db_customer = Customer(**customer.model_dump())
        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        
        return CustomerResponse.model_validate(db_customer)
    
    @staticmethod
    async def get_customer(db: AsyncSession, customer_id: str) -> CustomerResponse:
        """Get customer by ID"""
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        print("Get customer result:", result)
        customer = result.scalar_one_or_none()
        print("Get customer customer:", customer)
        print("Get customer customer:", customer)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return CustomerResponse.model_validate(customer)
    
    @staticmethod
    async def list_customers(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None
    ) -> List[CustomerResponse]:
        """List all customers with optional search"""
        query = select(Customer)
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                (Customer.name.ilike(search_pattern)) | 
                (Customer.email.ilike(search_pattern)) |
                (Customer.phone.ilike(search_pattern))
            )
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        customers = result.scalars().all()
        
        return [CustomerResponse.model_validate(c) for c in customers]
    
    @staticmethod
    async def update_customer(
        db: AsyncSession, 
        customer_id: str, 
        customer_update: CustomerUpdate
    ) -> CustomerResponse:
        """Update customer details"""
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        update_data = customer_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        await db.commit()
        await db.refresh(customer)
        
        return CustomerResponse.model_validate(customer)
    
    @staticmethod
    async def delete_customer(db: AsyncSession, customer_id: str) -> bool:
        """Delete customer"""
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check if customer has orders
        order_result = await db.execute(
            select(Order).where(Order.customer_id == customer_id).limit(1)
        )
        if order_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete customer with existing orders"
            )
        
        await db.delete(customer)
        await db.commit()
        return True
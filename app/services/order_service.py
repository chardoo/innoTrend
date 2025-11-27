from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.postgress_model import Customer, Order, OrderStatus, Service
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.utils.helpers import generate_order_number

class OrderService:
    @staticmethod
    async def _verify_relations(db: AsyncSession, customer_id: str, service_id: str):
        """Verify customer and service exist"""
        customer_result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        if not customer_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        service_result = await db.execute(
            select(Service).where(Service.id == service_id)
        )
        if not service_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    @staticmethod
    async def create_order(db: AsyncSession, order: OrderCreate) -> OrderResponse:
        """Create a new order"""
        await OrderService._verify_relations(db, order.customer_id, order.service_id)
        
        db_order = Order(
            **order.model_dump(),
            order_number=generate_order_number()
        )
        
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order, ['customer', 'service'])
        
        return OrderResponse.model_validate(db_order)
    
    @staticmethod
    async def get_order(db: AsyncSession, order_id: str) -> OrderResponse:
        """Get order by ID with related data"""
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.customer), selectinload(Order.service))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return OrderResponse.model_validate(order)
    
    @staticmethod
    async def list_orders(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[OrderResponse]:
        """List all orders with optional filters"""
        query = select(Order).options(
            selectinload(Order.customer),
            selectinload(Order.service)
        )
        
        # Apply filters
        if status:
            query = query.where(Order.status == status)
        
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                (Order.order_number.ilike(search_pattern)) |
                (Order.description.ilike(search_pattern)) |
                (Customer.name.ilike(search_pattern))|
                (Order.status.ilike(search_pattern))
            )
        
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return [OrderResponse.model_validate(order) for order in orders]
    
    @staticmethod
    async def update_order(
        db: AsyncSession,
        order_id: str,
        order_update: OrderUpdate
    ) -> OrderResponse:
        """Update order details"""
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.customer), selectinload(Order.service))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        update_data = order_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        await db.commit()
        await db.refresh(order)
        
        return OrderResponse.model_validate(order)
    
    @staticmethod
    async def delete_order(db: AsyncSession, order_id: str) -> bool:
        """Delete order"""
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        await db.delete(order)
        await db.commit()
        return True
    
    @staticmethod
    async def get_order_statistics(db: AsyncSession) -> dict:
        """Get order statistics"""
        # Count by status
        status_counts = await db.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )
        
        stats = {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0,
            "total_revenue": 0.0
        }
        
        for status, count in status_counts:
            stats["total"] += count
            stats[status.value] = count
        
        # Calculate total revenue from completed orders
        revenue_result = await db.execute(
            select(func.sum(Order.amount))
            .where(Order.status == OrderStatus.COMPLETED)
        )
        revenue = revenue_result.scalar_one_or_none()
        stats["total_revenue"] = float(revenue) if revenue else 0.0
        
        return stats
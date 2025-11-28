from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional

from fastapi.params import Query
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.services.order_service import OrderService
from app.services.customer_service import CustomerService
from app.services.sms_service import SMSService
from app.services.email_service import EmailService
from app.middleware.auth_middleware import require_admin, require_super_admin
from app.models.order import OrderStatus
from app.config.firebase import get_db
from sqlalchemy.ext.asyncio import  AsyncSession
router = APIRouter(prefix="/api/orders", tags=["Orders"])

async def send_order_notifications(
    order: OrderResponse,
    customer,
    is_new: bool = False,
    status_changed: bool = False
):
    """Background task to send order notifications"""
    sms_service = SMSService()
    email_service = EmailService()
    
    if is_new:
        # Notify admin about new order
        # await sms_service.notify_admin_new_order(order.order_number, customer.name)
        # await email_service.notify_admin_new_order(
        #     order.order_number,
        #     order.customer.name,
        #     order.customer.email,
        #     order.service,
        #     order.amount,
        #     order.customer.phone
        # )
        
        # Send confirmation to customer
        await email_service.send_order_confirmation(
            order.customer.email,
            order.order_number,
            order.customer.name,
            order.service.title,
            order.amount
        )
        await sms_service.send_order_notification(
            order.customer.phone,
            order.order_number,
            order.status.value
        )
    
    if status_changed:
        # Send update to customer
        await sms_service.send_order_notification(
            order.customer.phone,
            order.order_number,
            order.status.value
        )
        await email_service.send_order_update(
            order.customer.email,
            order.order_number,
            order.customer.name,
            order.status.value,
            order.progress_notes
        )

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new order (Admin only)"""

    order_service = OrderService()
    customer_service = CustomerService()
    
    new_order = await order_service.create_order(db, order)
    customer = await customer_service.get_customer(db, order.customer_id)
    
    # Send notifications in background
    background_tasks.add_task(
        send_order_notifications,
        new_order,
        customer,
        is_new=True
    )
    
    return new_order

@router.get("", response_model=List[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """List all orders with filters (Admin only)"""
    order_service = OrderService()
    return await order_service.list_orders(db,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        search=search
    )

@router.get("/statistics")
async def get_order_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_super_admin),
    period: Optional[str] = Query(None, enum=["today", "week", "month", "year", "all"]),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    start_date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Format: YYYY-MM-DD"),
    include_monthly_breakdown: bool = Query(False, description="Include monthly breakdown"),
    include_comparison: bool = Query(False, description="Compare with previous period")
):
    """
    Get comprehensive order statistics (Admin only)
    
    Query Parameters:
    - period: Predefined period (today/week/month/year/all)
    - year: Specific year
    - month: Specific month (1-12, requires year)
    - start_date: Custom start date (YYYY-MM-DD)
    - end_date: Custom end date (YYYY-MM-DD)
    - include_monthly_breakdown: Get monthly breakdown for the period
    - include_comparison: Compare with previous period
    """
    order_service = OrderService()
    
    # Parse custom dates if provided
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    return await order_service.get_order_statistics(
        db=db,
        period=period,
        year=year,
        month=month,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        include_monthly_breakdown=include_monthly_breakdown,
        include_comparison=include_comparison
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get order by ID (Admin only)"""
    order_service = OrderService()
    return await order_service.get_order(db, order_id)

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order: OrderUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update order (Admin only)"""
    order_service = OrderService()
    customer_service = CustomerService()
    
    # Get old order to check if status changed
    old_order = await order_service.get_order(db, order_id)
    updated_order = await order_service.update_order(db, order_id, order)
    
    # If status changed, send notifications
    if order.status and old_order.status != updated_order.status:
        customer = await customer_service.get_customer(db,updated_order.customer_id)
        background_tasks.add_task(
            send_order_notifications,
            updated_order,
            customer,
            status_changed=True
        )
    
    return updated_order

@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete order (Admin only)"""
    order_service = OrderService()
    await order_service.delete_order(db,order_id)
    return {"message": "Order deleted successfully"}

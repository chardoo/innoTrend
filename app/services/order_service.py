from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import and_, case, extract, select, func
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
    async def get_order_statistics(
        db: AsyncSession,
        period: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_monthly_breakdown: bool = False,
        include_comparison: bool = False
    ) -> dict:
        """Get comprehensive order statistics with filtering"""
        
        # Determine date range based on period
        if period:
            start_date, end_date = OrderService._get_period_dates(period)
        elif year and month:
            # Specific month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        elif year:
            # Entire year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
        
        # Get main statistics
        stats = await OrderService._calculate_statistics(db, start_date, end_date)
        
        # Add filter info
        stats["filters"] = {
            "period": period,
            "year": year,
            "month": month,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
        
        # Add monthly breakdown if requested
        if include_monthly_breakdown:
            stats["monthly_breakdown"] = await OrderService._get_monthly_breakdown(
                db, start_date, end_date, year
            )
        
        # Add comparison with previous period if requested
        if include_comparison and start_date and end_date:
            stats["comparison"] = await OrderService._get_comparison(
                db, start_date, end_date
            )
        
        # Add additional metrics
        stats["metrics"] = await OrderService._get_additional_metrics(
            db, start_date, end_date
        )
        
        return stats
    
    @staticmethod
    def _get_period_dates(period: str) -> tuple[datetime, datetime]:
        """Get start and end dates for predefined periods"""
        now = datetime.now()
        
        if period == "today":
            start = datetime(now.year, now.month, now.day)
            end = start + timedelta(days=1) - timedelta(seconds=1)
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            end = start + timedelta(days=7) - timedelta(seconds=1)
        elif period == "month":
            start = datetime(now.year, now.month, 1)
            if now.month == 12:
                end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)
        elif period == "year":
            start = datetime(now.year, 1, 1)
            end = datetime(now.year, 12, 31, 23, 59, 59)
        else:  # "all"
            return None, None
        
        return start, end
    
    @staticmethod
    async def _calculate_statistics(
        db: AsyncSession,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> dict:
        """Calculate basic order statistics"""
        
        # Build filters
        filters = []
        if start_date:
            filters.append(Order.created_at >= start_date)
        if end_date:
            filters.append(Order.created_at <= end_date)
        
        # Count by status
        status_query = select(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status)
        
        if filters:
            status_query = status_query.where(and_(*filters))
        
        status_counts = await db.execute(status_query)
        
        stats = {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0
        }
        
        for status, count in status_counts:
            stats["total"] += count
            stats[status.value] = count
        
        # Calculate revenue and average from completed orders
        revenue_query = select(
            func.sum(Order.amount).label('total'),
            func.avg(Order.amount).label('average'),
            func.count(Order.id).label('count')
        ).where(Order.status == OrderStatus.COMPLETED)
        
        if filters:
            revenue_query = revenue_query.where(and_(*filters))
        
        revenue_result = await db.execute(revenue_query)
        revenue_data = revenue_result.first()
        
        if revenue_data:
            stats["total_revenue"] = float(revenue_data.total) if revenue_data.total else 0.0
            stats["average_order_value"] = float(revenue_data.average) if revenue_data.average else 0.0
            stats["completed_orders_count"] = revenue_data.count or 0
        
        return stats
    
    @staticmethod
    async def _get_monthly_breakdown(
        db: AsyncSession,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        year: Optional[int]
    ) -> list[dict]:
        """Get monthly breakdown of orders"""
        
        # Determine year range
        if year:
            years = [year]
        elif start_date and end_date:
            years = list(range(start_date.year, end_date.year + 1))
        else:
            years = [datetime.now().year]
        
        monthly_data = []
        
        for current_year in years:
            # Query for monthly data
            monthly_query = select(
                extract('month', Order.created_at).label('month'),
                Order.status,
                func.count(Order.id).label('count'),
                func.sum(
                    case(
                        (Order.status == OrderStatus.COMPLETED, Order.amount),
                        else_=0
                    )
                ).label('revenue')
            ).where(
                extract('year', Order.created_at) == current_year
            ).group_by('month', Order.status)
            
            # Apply date filters if provided
            if start_date:
                monthly_query = monthly_query.where(Order.created_at >= start_date)
            if end_date:
                monthly_query = monthly_query.where(Order.created_at <= end_date)
            
            results = await db.execute(monthly_query)
            
            # Organize data by month
            months_dict = {}
            for month_num in range(1, 13):
                month_date = datetime(current_year, month_num, 1)
                
                # Skip months outside date range
                if start_date and month_date < datetime(start_date.year, start_date.month, 1):
                    continue
                if end_date and month_date > datetime(end_date.year, end_date.month, 1):
                    continue
                
                months_dict[month_num] = {
                    "year": current_year,
                    "month": month_num,
                    "month_name": month_date.strftime('%B'),
                    "total": 0,
                    "pending": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "cancelled": 0,
                    "revenue": 0.0
                }
            
            # Fill in actual data
            for month, status, count, revenue in results:
                month_int = int(month)
                if month_int in months_dict:
                    months_dict[month_int]["total"] += count
                    months_dict[month_int][status.value] = count
                    if revenue:
                        months_dict[month_int]["revenue"] = float(revenue)
            
            monthly_data.extend(months_dict.values())
        
        return monthly_data
    
    @staticmethod
    async def _get_comparison(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """Compare current period with previous period"""
        
        period_length = end_date - start_date
        prev_start = start_date - period_length - timedelta(seconds=1)
        prev_end = start_date - timedelta(seconds=1)
        
        # Get previous period stats
        previous_stats = await OrderService._calculate_statistics(db, prev_start, prev_end)
        current_stats = await OrderService._calculate_statistics(db, start_date, end_date)
        
        def calc_change(prev: float, curr: float) -> dict:
            if prev == 0:
                percentage = 100.0 if curr > 0 else 0.0
            else:
                percentage = ((curr - prev) / prev) * 100
            
            return {
                "previous": prev,
                "current": curr,
                "change": curr - prev,
                "percentage_change": round(percentage, 2)
            }
        
        return {
            "total_orders": calc_change(previous_stats["total"], current_stats["total"]),
            "revenue": calc_change(previous_stats["total_revenue"], current_stats["total_revenue"]),
            "completed": calc_change(previous_stats["completed"], current_stats["completed"]),
            "average_order_value": calc_change(
                previous_stats["average_order_value"],
                current_stats["average_order_value"]
            )
        }
    
    @staticmethod
    async def _get_additional_metrics(
        db: AsyncSession,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> dict:
        """Calculate additional useful metrics"""
        
        filters = []
        if start_date:
            filters.append(Order.created_at >= start_date)
        if end_date:
            filters.append(Order.created_at <= end_date)
        
        # Completion rate
        total_query = select(func.count(Order.id))
        if filters:
            total_query = total_query.where(and_(*filters))
        
        total_result = await db.execute(total_query)
        total_orders = total_result.scalar_one_or_none() or 0
        
        completed_query = select(func.count(Order.id)).where(
            Order.status == OrderStatus.COMPLETED
        )
        if filters:
            completed_query = completed_query.where(and_(*filters))
        
        completed_result = await db.execute(completed_query)
        completed_orders = completed_result.scalar_one_or_none() or 0
        
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0.0
        
        # Cancellation rate
        cancelled_query = select(func.count(Order.id)).where(
            Order.status == OrderStatus.CANCELLED
        )
        if filters:
            cancelled_query = cancelled_query.where(and_(*filters))
        
        cancelled_result = await db.execute(cancelled_query)
        cancelled_orders = cancelled_result.scalar_one_or_none() or 0
        
        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0.0
        
        return {
            "completion_rate": round(completion_rate, 2),
            "cancellation_rate": round(cancellation_rate, 2),
            "in_progress_orders": total_orders - completed_orders - cancelled_orders
        }
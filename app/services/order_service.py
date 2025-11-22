from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from app.config.firebase import db
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.models.order import OrderStatus
from app.utils.helpers import generate_order_number

class OrderService:
    def __init__(self):
        self.collection = db.collection('orders')
        self.customer_collection = db.collection('customers')
        self.customer_service = db.collection('services')
    
    def _get_customer_data(self, customer_id: str) -> dict:
        """Fetch customer data"""
        customer_doc = self.customer_collection.document(customer_id).get()
        if not customer_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return {"id": customer_doc.id, **customer_doc.to_dict()}
    
    def _get_service_data(self, service_id: str) -> dict:
        """Fetch service data"""
        service_doc = self.customer_service.document(service_id).get()
        if not service_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        return {"id": service_doc.id, **service_doc.to_dict()}
    
    async def create_order(self, order: OrderCreate) -> OrderResponse:
        """Create a new order"""
        # Verify customer and service exist and fetch their data
        customer_data = self._get_customer_data(order.customer_id)
        service_data = self._get_service_data(order.service_id)
        
        order_data = {
            **order.model_dump(),
            "order_number": generate_order_number(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        doc_ref = self.collection.document()
        doc_ref.set(order_data)   
        return OrderResponse(
            id=doc_ref.id,
            order_number=order_data["order_number"],
            quantity=order.quantity,
            
            customer=customer_data,  
            customer_id=order.customer_id,
            service=service_data,
            service_id=order.service_id,
            description=order.description,
            amount=order.amount,
            status=order.status or OrderStatus.PENDING,
            progress_notes=order_data.get("progress_notes"),
            created_at=order_data["created_at"],
            updated_at=order_data["updated_at"],
            color=order.color,
            unit_price=order.unit_price,
        )
    
    async def get_order(self, order_id: str) -> OrderResponse:
        """Get order by ID"""
        doc = self.collection.document(order_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        data = doc.to_dict()
        
        # Fetch related customer and service data
        customer_data = self._get_customer_data(data["customer_id"])
        service_data = self._get_service_data(data["service_id"])
        
        return OrderResponse(
            id=doc.id,
            order_number=data["order_number"],
            customer_id=data["customer_id"],
            customer=customer_data,  # Attach customer data
            service_id=data["service_id"],
            service=service_data,  # Attach service data
            description=data.get("description"),
            amount=data["amount"],
            color=data.get("color"),
            unit_price=data.get("unit_price"),
            quantity=data.get("quantity"),
            status=OrderStatus(data["status"]),
            progress_notes=data.get("progress_notes"),
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )
    
    async def list_orders(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[OrderStatus] = None,
        customer_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[OrderResponse]:
        """List all orders with optional filters"""
        query = self.collection
        
        # Apply filters
        if status:
            query = query.where('status', '==', status.value)
        
        if customer_id:
            query = query.where('customer_id', '==', customer_id)
        
        if search:
            # Firebase doesn't support full-text search
            all_orders = query.stream()
            orders = []
            count = 0
            for doc in all_orders:
                data = doc.to_dict()
                if (search.lower() in data["order_number"].lower() or 
                    (data.get("description") and search.lower() in data["description"].lower())):
                    if count >= skip and len(orders) < limit:
                        # Fetch related data
                        customer_data = self._get_customer_data(data["customer_id"])
                        service_data = self._get_service_data(data["service_id"])
                        
                        orders.append(OrderResponse(
                            id=doc.id,
                            order_number=data["order_number"],
                            customer_id=data["customer_id"],
                            customer=customer_data,
                            service_id=data["service_id"],
                            service=service_data,
                            description=data.get("description"),
                            amount=data["amount"],
                            status=OrderStatus(data["status"]),
                            progress_notes=data.get("progress_notes"),
                            created_at=data["created_at"],
                            updated_at=data["updated_at"],
                            color=data.get("color"),
                            unit_price=data.get("unit_price"),
                            quantity=data.get("quantity"),
                        ))
                    count += 1
        else:
            docs = query.order_by('created_at', direction='DESCENDING').offset(skip).limit(limit).stream()
            orders = []
            for doc in docs:
                data = doc.to_dict()
                # Fetch related data
                customer_data = self._get_customer_data(data["customer_id"])
                service_data = self._get_service_data(data["service_id"])
                
                orders.append(OrderResponse(
                    id=doc.id,
                    order_number=data["order_number"],
                    customer_id=data["customer_id"],
                    customer=customer_data,
                    service_id=data["service_id"],
                    service=service_data,
                    description=data.get("description"),
                    amount=data["amount"],
                    status=OrderStatus(data["status"]),
                    progress_notes=data.get("progress_notes"),
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    color=data.get("color"),
                    unit_price=data.get("unit_price"),
                    quantity=data.get("quantity"),
                ))
        
        return orders
    
    async def update_order(self, order_id: str, order: OrderUpdate) -> OrderResponse:
        """Update order details"""
        doc_ref = self.collection.document(order_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        update_data = order.model_dump(exclude_unset=True)
        if "status" in update_data:
            update_data["status"] = update_data["status"].value
        update_data["updated_at"] = datetime.utcnow()
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        data = updated_doc.to_dict()
        
        # Fetch related data
        customer_data = self._get_customer_data(data["customer_id"])
        service_data = self._get_service_data(data["service_id"])
        
        return OrderResponse(
            id=updated_doc.id,
            order_number=data["order_number"],
            customer_id=data["customer_id"],
            customer=customer_data,
            service_id=data["service_id"],
            service=service_data,
            description=data.get("description"),
            amount=data["amount"],
            status=OrderStatus(data["status"]),
            progress_notes=data.get("progress_notes"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            color=data.get("color"),
            unit_price=data.get("unit_price"),
            quantity=data.get("quantity"),
        )
    
    async def delete_order(self, order_id: str) -> bool:
        """Delete order"""
        doc_ref = self.collection.document(order_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        doc_ref.delete()
        return True
    
    async def get_order_statistics(self) -> dict:
        """Get order statistics"""
        all_orders = self.collection.stream()
        
        stats = {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0,
            "total_revenue": 0.0
        }
        
        for doc in all_orders:
            data = doc.to_dict()
            stats["total"] += 1
            stats[data["status"]] += 1
            if data["status"] == OrderStatus.COMPLETED.value:
                stats["total_revenue"] += data["amount"]
        
        return stats
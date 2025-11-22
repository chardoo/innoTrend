from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from app.config.firebase import db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

class CustomerService:
    def __init__(self):
        self.collection = db.collection('customers')
    
    async def create_customer(self, customer: CustomerCreate) -> CustomerResponse:
        """Create a new customer"""
        # Check if customer exists
        existing = self.collection.where('email', '==', customer.email).limit(1).get()
        if list(existing):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this email already exists"
            )
        
        customer_data = {
            **customer.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        doc_ref = self.collection.document()
        doc_ref.set(customer_data)
        
        return CustomerResponse(
            id=doc_ref.id,
            **customer.model_dump(),
            created_at=customer_data["created_at"],
            updated_at=customer_data["updated_at"]
        )
    
    async def get_customer(self, customer_id: str) -> CustomerResponse:
        """Get customer by ID"""
        doc = self.collection.document(customer_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        data = doc.to_dict()
        return CustomerResponse(id=doc.id, **data)
    
    async def list_customers(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[CustomerResponse]:
        """List all customers with optional search"""
        query = self.collection
        
        if search:
            all_customers = query.stream()
            customers = []
            count = 0
            for doc in all_customers:
                data = doc.to_dict()
                if (search.lower() in data["name"].lower() or 
                    search.lower() in data["email"].lower() or
                    (data.get("phone") and search in data["phone"])):
                    if count >= skip and len(customers) < limit:
                        customers.append(CustomerResponse(id=doc.id, **data))
                    count += 1
        else:
            docs = query.offset(skip).limit(limit).stream()
            customers = [CustomerResponse(id=doc.id, **doc.to_dict()) for doc in docs]
        
        return customers
    
    async def update_customer(self, customer_id: str, customer: CustomerUpdate) -> CustomerResponse:
        """Update customer details"""
        doc_ref = self.collection.document(customer_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        update_data = customer.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        data = updated_doc.to_dict()
        return CustomerResponse(id=updated_doc.id, **data)
    
    async def delete_customer(self, customer_id: str) -> bool:
        """Delete customer"""
        doc_ref = self.collection.document(customer_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check if customer has orders
        orders = db.collection('orders').where('customer_id', '==', customer_id).limit(1).get()
        if list(orders):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete customer with existing orders"
            )
        
        doc_ref.delete()
        return True

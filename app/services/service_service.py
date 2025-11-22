from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from app.config.firebase import db
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse

class ServiceService:
    def __init__(self):
        self.collection = db.collection('services')
    
    async def create_service(self, service: ServiceCreate) -> ServiceResponse:
        """Create a new service"""
        service_data = {
            **service.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        doc_ref = self.collection.document()
        doc_ref.set(service_data)
        
        return ServiceResponse(id=doc_ref.id, **service_data)
    
    async def get_service(self, service_id: str) -> ServiceResponse:
        """Get service by ID"""
        doc = self.collection.document(service_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        data = doc.to_dict()
        return ServiceResponse(id=doc.id, **data)
    
    async def list_services(self, skip: int = 0, limit: int = 100, active_only: bool = False, search: Optional[str] = None) -> List[ServiceResponse]:
        """List all services"""
        query = self.collection
        
        if active_only:
            query = query.where('is_active', '==', True)
        
        if search:
            all_services = query.stream()
            services = []
            count = 0
            for doc in all_services:
                data = doc.to_dict()
                if (search.lower() in data["title"].lower() or 
                    search.lower() in data["description"].lower()):
                    if count >= skip and len(services) < limit:
                        services.append(ServiceResponse(id=doc.id, **data))
                    count += 1
        else:
            docs = query.offset(skip).limit(limit).stream()
            services = [ServiceResponse(id=doc.id, **doc.to_dict()) for doc in docs]
        
        return services
    
    async def update_service(self, service_id: str, service: ServiceUpdate) -> ServiceResponse:
        """Update service"""
        doc_ref = self.collection.document(service_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        update_data = service.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        data = updated_doc.to_dict()
        return ServiceResponse(id=updated_doc.id, **data)
    
    async def delete_service(self, service_id: str) -> bool:
        """Delete service"""
        doc_ref = self.collection.document(service_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        doc_ref.delete()
        return True


from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgress_model import Service
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse

class ServiceService:
    @staticmethod
    async def create_service(db: AsyncSession, service: ServiceCreate) -> ServiceResponse:
        """Create a new service"""
        db_service = Service(**service.model_dump())
        db.add(db_service)
        await db.commit()
        await db.refresh(db_service)
        
        return ServiceResponse.model_validate(db_service)
    
    @staticmethod
    async def get_service(db: AsyncSession, service_id: str) -> ServiceResponse:
        """Get service by ID"""
        result = await db.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        return ServiceResponse.model_validate(service)
    
    @staticmethod
    async def list_services(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        search: Optional[str] = None
    ) -> List[ServiceResponse]:
        """List all services with optional filters"""
        query = select(Service)
        
        if active_only:
            query = query.where(Service.is_active == True)
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                (Service.title.ilike(search_pattern)) |
                (Service.description.ilike(search_pattern))
            )
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        services = result.scalars().all()
        
        return [ServiceResponse.model_validate(s) for s in services]
    
    @staticmethod
    async def update_service(
        db: AsyncSession,
        service_id: str,
        service_update: ServiceUpdate
    ) -> ServiceResponse:
        """Update service"""
        result = await db.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        update_data = service_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service, field, value)
        
        await db.commit()
        await db.refresh(service)
        
        return ServiceResponse.model_validate(service)
    
    @staticmethod
    async def delete_service(db: AsyncSession, service_id: str) -> bool:
        """Delete service"""
        result = await db.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        await db.delete(service)
        await db.commit()
        return True
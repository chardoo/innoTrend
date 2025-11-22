from fastapi import APIRouter, Depends, status
from typing import List, Optional
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services.service_service import ServiceService
from app.middleware.auth_middleware import require_admin, get_optional_user

router = APIRouter(prefix="/api/services", tags=["Services"])

@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service: ServiceCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new service (Admin only)"""
    service_service = ServiceService()
    return await service_service.create_service(service)

@router.get("", response_model=List[ServiceResponse])
async def list_services(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    search: Optional[str] = None,
    current_user: dict = Depends(get_optional_user)
):
    """List all services (Public endpoint)"""
    service_service = ServiceService()
    # Non-admins can only see active services
    if not current_user or current_user.get("role") not in ["admin", "manager"]:
        active_only = True
    return await service_service.list_services(
        skip=skip,
        limit=limit,
        active_only=active_only,
        search=search
    )

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    current_user: dict = Depends(get_optional_user)
):
    """Get service by ID (Public endpoint)"""
    service_service = ServiceService()
    return await service_service.get_service(service_id)

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service: ServiceUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update service (Admin only)"""
    service_service = ServiceService()
    return await service_service.update_service(service_id, service)

@router.delete("/{service_id}")
async def delete_service(
    service_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete service (Admin only)"""
    service_service = ServiceService()
    await service_service.delete_service(service_id)
    return {"message": "Service deleted successfully"}

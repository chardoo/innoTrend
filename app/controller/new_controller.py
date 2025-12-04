
from fastapi import APIRouter, Depends, Query,status, BackgroundTasks
from typing import List, Optional

from app.config.firebase import get_db
from app.middleware.auth_middleware import require_admin
from sqlalchemy.ext.asyncio import  AsyncSession
from app.schemas.news import NewsCreate, NewsResponse, NewsUpdate
from app.services.news_service import NewsService

news_router = APIRouter(prefix="/news", tags=["News"])

@news_router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    news_data: NewsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new news item (Admin only)"""
    return await NewsService.create_news(db, news_data)

@news_router.get("/{news_id}", response_model=NewsResponse)
async def get_news(
    news_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get news by ID (Public)"""
    return await NewsService.get_news(db, news_id)

@news_router.get("/", response_model=List[NewsResponse])
async def get_all_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False, description="Show only active news"),
    current_only: bool = Query(False, description="Show only current news (active and within date range)"),
    db: AsyncSession = Depends(get_db)
):
    """Get all news with optional filters (Public)"""
    return await NewsService.get_all_news(db, skip, limit, active_only, current_only)

@news_router.put("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: str,
    news_data: NewsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update a news item (Admin only)"""
    return await NewsService.update_news(db, news_id, news_data)

@news_router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a news item (Admin only)"""
    await NewsService.delete_news(db, news_id)

@news_router.patch("/{news_id}/toggle", response_model=NewsResponse)
async def toggle_news_active(
    news_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Toggle active status of news (Admin only)"""
    return await NewsService.toggle_active(db, news_id)

@news_router.get("/statistics/summary")
async def get_news_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get news statistics (Admin only)"""
    return await NewsService.get_news_statistics(db)


# ========== SERVICES ==========
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, extract, and_, or_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.postgress_model import News
from app.schemas.news import NewsCreate, NewsUpdate
from app.services.expenses import to_naive_utc



class NewsService:
    @staticmethod
    async def create_news(db: AsyncSession, news_data: NewsCreate) -> News:
        """Create a new news item"""
        
        news_data.from_date = to_naive_utc(news_data.from_date)
        news_data.to_date = to_naive_utc(news_data.to_date)
        news = News(**news_data.model_dump())
        db.add(news)
        await db.commit()
        await db.refresh(news)
        return news
    
    @staticmethod
    async def get_news(db: AsyncSession, news_id: str) -> Optional[News]:
        """Get news by ID"""
        result = await db.execute(select(News).where(News.id == news_id))
        news = result.scalar_one_or_none()
        if not news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News not found"
            )
        return news
    
    @staticmethod
    async def get_all_news(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        current_only: bool = False
    ) -> List[News]:
        """Get all news with optional filters"""
        query = select(News).order_by(News.from_date.desc())
        
        filters = []
        if active_only:
            filters.append(News.active == True)
        
        if current_only:
            now = datetime.utcnow()
            filters.append(News.from_date <= now)
            filters.append(News.to_date >= now)
            filters.append(News.active == True)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_news(
        db: AsyncSession,
        news_id: str,
        news_data: NewsUpdate
    ) -> News:
        """Update a news item"""
        news = await NewsService.get_news(db, news_id)
        
        update_data = news_data.model_dump(exclude_unset=True)
        
        # Validate date range if both dates are being updated
        if 'from_date' in update_data and update_data['from_date']:
           update_data['from_date'] = to_naive_utc(update_data['from_date'])
        if 'to_date' in update_data and update_data['to_date']:
           update_data['to_date'] = to_naive_utc(update_data['to_date'])
    
    # Validate date range if both dates are being updated
        if 'from_date' in update_data or 'to_date' in update_data:
          from_date = update_data.get('from_date', news.from_date)
          to_date = update_data.get('to_date', news.to_date)
          if to_date <= from_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="to_date must be after from_date"
            )
        for field, value in update_data.items():
            setattr(news, field, value)
        
        news.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(news)
        return news
    
    @staticmethod
    async def delete_news(db: AsyncSession, news_id: str) -> bool:
        """Delete a news item"""
        news = await NewsService.get_news(db, news_id)
        await db.delete(news)
        await db.commit()
        return True
    
    @staticmethod
    async def toggle_active(db: AsyncSession, news_id: str) -> News:
        """Toggle active status of news"""
        news = await NewsService.get_news(db, news_id)
        news.active = not news.active
        news.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(news)
        return news
    
    @staticmethod
    async def get_news_statistics(db: AsyncSession) -> dict:
        """Get news statistics"""
        
        # Total counts
        total_query = select(func.count(News.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar_one_or_none() or 0
        
        # Active count
        active_query = select(func.count(News.id)).where(News.active == True)
        active_result = await db.execute(active_query)
        active = active_result.scalar_one_or_none() or 0
        
        # Current news (active and within date range)
        now = datetime.utcnow()
        current_query = select(func.count(News.id)).where(
            and_(
                News.active == True,
                News.from_date <= now,
                News.to_date >= now
            )
        )
        current_result = await db.execute(current_query)
        current = current_result.scalar_one_or_none() or 0
        
        # Upcoming news
        upcoming_query = select(func.count(News.id)).where(
            and_(
                News.active == True,
                News.from_date > now
            )
        )
        upcoming_result = await db.execute(upcoming_query)
        upcoming = upcoming_result.scalar_one_or_none() or 0
        
        # Expired news
        expired_query = select(func.count(News.id)).where(
            News.to_date < now
        )
        expired_result = await db.execute(expired_query)
        expired = expired_result.scalar_one_or_none() or 0
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "current": current,
            "upcoming": upcoming,
            "expired": expired
        }


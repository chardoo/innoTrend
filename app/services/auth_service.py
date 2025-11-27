from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgress_model import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.helpers import get_password_hash, verify_password

class AuthService:
    @staticmethod
    async def create_user(db: AsyncSession, user: UserCreate) -> UserResponse:
        """Create a new user"""
        # Check if user exists
        print( "Creating user:", user)
        
        result = await db.execute(
            select(User).where(User.email == user.email)
        )
        print("User existence check result:", result)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            password_hash=get_password_hash(user.password),
            is_active=True
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return UserResponse.model_validate(db_user)
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user and return user data"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        print("Fetching user with ID:", user_id)
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        print("Query result:", result)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: str, user_update: UserUpdate) -> UserResponse:
        """Update user details"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    @staticmethod
    async def list_users(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None
    ) -> list[UserResponse]:
        """List all users with optional search"""
        query = select(User)
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                (User.email.ilike(search_pattern)) | 
                (User.full_name.ilike(search_pattern))
            )
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active to False)"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await db.commit()
        return True
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin, Token
from app.services.auth_service import AuthService
from app.utils.helpers import create_access_token
from app.middleware.auth_middleware import get_current_user, require_admin, require_super_admin
from app.config.firebase import get_db
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user (Public endpoint for initial setup, should be protected in production)"""
    auth_service = AuthService()
    print("Registering user:", user)
    return await auth_service.create_user(db, user)

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access token"""
    auth_service = AuthService()
    user = await auth_service.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": (str(user.id))})
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info( db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    auth_service = AuthService()
    return await auth_service.get_user_by_id(db, current_user["id"])

@router.get("/users",  response_model=List[UserResponse],)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(require_admin)
):
    """List all users (Admin only)"""
    auth_service = AuthService()
    return await auth_service.list_users(db, skip=skip, limit=limit, search=search)

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_super_admin)
):
    """Create a new user with specific role (Super Admin only)"""
    print("Creating user:", user)
    auth_service = AuthService()
    return await auth_service.create_user(db, user)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get user by ID (Admin only)"""
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
     db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_super_admin)
):
    """Update user (Super Admin only)"""
    auth_service = AuthService()
    return await auth_service.update_user(db, user_id, user_update)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_super_admin)
):
    """Deactivate user (Super Admin only)"""
    auth_service = AuthService()
    await auth_service.delete_user(db, user_id)
    return {"message": "User deactivated successfully"}

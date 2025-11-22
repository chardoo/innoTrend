from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from app.config.firebase import db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.helpers import get_password_hash, verify_password, create_access_token
from app.models.user import UserRole

class AuthService:
    def __init__(self):
        self.collection = db.collection('users')
    
    async def create_user(self, user: UserCreate) -> UserResponse:
        """Create a new user"""
        # Check if user exists
        
        print("Creating user with email:", user.email)
        existing_user = self.collection.where('email', '==', user.email).limit(1).get()
        print("Checking existing user for email:", existing_user)
        if list(existing_user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
  
        user_data = {
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role.value,
            "password_hash": get_password_hash(user.password),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        print("User data to be stored:", user_data)
        
        doc_ref = self.collection.document()
        doc_ref.set(user_data)
        
        return UserResponse(
            id=doc_ref.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_active=True,
            created_at=user_data["created_at"]
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user and return user data"""
        users = self.collection.where('email', '==', email).limit(1).get()
        user_list = list(users)
        
        if not user_list:
            return None
        
        user_doc = user_list[0]
        user_data = user_doc.to_dict()
        
        if not verify_password(password, user_data.get("password_hash", "")):
            return None
        
        if not user_data.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return {
            "id": user_doc.id,
            **user_data
        }
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            return None
        
        user_data = doc.to_dict()
        return UserResponse(
            id=doc.id,
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone=user_data.get("phone"),
            role=UserRole(user_data["role"]),
            is_active=user_data["is_active"],
            created_at=user_data["created_at"]
        )
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        users = self.collection.where('email', '==', email).limit(1).get()
        user_list = list(users)
        
        if not user_list:
            return None
        
        user_doc = user_list[0]
        return {
            "id": user_doc.id,
            **user_doc.to_dict()
        }
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        """Update user details"""
        doc_ref = self.collection.document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_update.model_dump(exclude_unset=True)
        if "role" in update_data:
            update_data["role"] = update_data["role"].value
        update_data["updated_at"] = datetime.utcnow()
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        user_data = updated_doc.to_dict()
        
        return UserResponse(
            id=updated_doc.id,
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone=user_data.get("phone"),
            role=UserRole(user_data["role"]),
            is_active=user_data["is_active"],
            created_at=user_data["created_at"]
        )
    
    async def list_users(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> list[UserResponse]:
        """List all users with optional search"""
        query = self.collection
        
        if search:
            # Firebase doesn't support full-text search, so we'll filter in memory
            all_users = query.stream()
            users = []
            count = 0
            for doc in all_users:
                user_data = doc.to_dict()
                if (search.lower() in user_data["email"].lower() or 
                    search.lower() in user_data["full_name"].lower()):
                    if count >= skip and len(users) < limit:
                        users.append(UserResponse(
                            id=doc.id,
                            email=user_data["email"],
                            full_name=user_data["full_name"],
                            phone=user_data.get("phone"),
                            role=UserRole(user_data["role"]),
                            is_active=user_data["is_active"],
                            created_at=user_data["created_at"]
                        ))
                    count += 1
        else:
            docs = query.offset(skip).limit(limit).stream()
            users = [
                UserResponse(
                    id=doc.id,
                    email=doc.to_dict()["email"],
                    full_name=doc.to_dict()["full_name"],
                    phone=doc.to_dict().get("phone"),
                    role=UserRole(doc.to_dict()["role"]),
                    is_active=doc.to_dict()["is_active"],
                    created_at=doc.to_dict()["created_at"]
                )
                for doc in docs
            ]
        
        return users
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active to False)"""
        doc_ref = self.collection.document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        doc_ref.update({
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        return True
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Service(BaseModel):
    id: Optional[str] = None
    title: str  # Changed from 'name' based on your data
    description: str
    icon: str
    image_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    def get_info(self) -> str:
        return f"Service: {self.title}, Description: {self.description}, Active: {self.is_active}"
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, timezone

from app.services.expenses import to_naive_utc



class NewsBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    active: bool = True
    from_date: datetime
    to_date: datetime


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    active: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    


class NewsResponse(NewsBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
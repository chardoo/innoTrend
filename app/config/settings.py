# app/config/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import Field, AliasChoices, field_validator

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "FastAPI Firebase App"
    ENV: str = "dev"
    APP_DEBUG: bool = True
    
    # Database - IMPORTANT: Must include +asyncpg
    DATABASE_URL: str
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_DATABASE_URL: Optional[str] = None
    GoogleServiceAccount: Optional[str] = None
    GoogleConfig: Optional[str] = None
    FIREBASE_CREDENTIALS_B64: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("APP_FIREBASE_CREDENTIALS_B64", "googleconfig"),
    )
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("APP_GOOGLE_APPLICATION_CREDENTIALS", "googleserviceaccount"),
    )
    FIREBASE_PROJECT_ID: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("APP_FIREBASE_PROJECT_ID", "firebase_project_id"),
    )
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    ADMIN_PHONE_NUMBER: Optional[str] = None
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None
    ADMIN_EMAIL: Optional[str] = None
    
    # SMS
    Arkesel: str = 'cE9QRUkdjsjdfjkdsj9kdiieieififiw='
    Sender_id: str = 'innoTrend'
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    ALLOW_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    @property
    def origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Convert async DATABASE_URL to sync for Alembic migrations"""
        url = self.DATABASE_URL
        if "asyncpg" in url:
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif url.startswith("postgresql://") and "psycopg2" not in url:
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    
    @field_validator("ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
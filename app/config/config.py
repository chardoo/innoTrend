# app/core/config.py
from typing import List, Optional
from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Accept .env and ignore keys your model doesn't know
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

    APP_NAME: str = "FastAPI Starter"
    ENV: str = "dev"
    DEBUG: bool = True
    ALLOW_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://localhost",
        "https://innotrend.netlify.app"
    ]
    # Map your existing env names too (works with or without the APP_ prefix)
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

    @field_validator("ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

settings = Settings()

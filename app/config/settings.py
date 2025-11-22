from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str
    FIREBASE_DATABASE_URL: str
    GoogleServiceAccount: str
    APP_APP_NAME: str = "FastAPI Firebase App"
    APP_ALLOW_ORIGINS: str = "*"
    GoogleConfig: str
    APP_DEBUG: bool = True
    Arkesel: str = 'cE9QRUkdjsjdfjkdsj9kdiieieififiw='
    Sender_id: str = 'innoTrend'
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    ADMIN_PHONE_NUMBER: str
    
    # SendGrid
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    ADMIN_EMAIL: str
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

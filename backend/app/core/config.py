from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LeaveAI"
    DEBUG: bool = True
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = ""
    
    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@leaveai.com"
    EMAIL_FROM_NAME: str = "LeaveAI System"
    
    # AI Thresholds
    AI_MIN_CONFIDENCE_TO_APPROVE: int = 75
    AI_MIN_CONFIDENCE_TO_REJECT: int = 25
    AI_TIMEOUT_MS: int = 30000
    AI_FALLBACK_MODE: str = "MANUAL_REVIEW"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

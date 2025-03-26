import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "TAPBuddy AI Video Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    
    # API Keys and Services
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.environ.get("ELEVENLABS_API_KEY", "")
    RUNWAY_ML_API_KEY: str = os.environ.get("RUNWAY_ML_API_KEY", "")
    
    # Twilio Settings for WhatsApp
    TWILIO_ACCOUNT_SID: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.environ.get("TWILIO_PHONE_NUMBER", "")
    
    # Firebase Settings
    FIREBASE_CREDENTIALS: str = os.environ.get("FIREBASE_CREDENTIALS", "")
    FIREBASE_STORAGE_BUCKET: str = os.environ.get("FIREBASE_STORAGE_BUCKET", "")
    
    # Database Settings
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./tapbuddy.db")
    
    # Application Paths
    TEMP_DIR: str = os.environ.get("TEMP_DIR", "./temp")
    
    model_config = {
        "env_file": ".env"
    }


settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    """
    Returns the application settings.
    This function is cached to avoid loading the settings multiple times.
    
    Returns:
        Settings object with all configuration parameters
    """
    return settings

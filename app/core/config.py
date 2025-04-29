from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Serena AI Agent Dashboard"
    SUPABASE_URL: str
    SUPABASE_KEY: str
    # Allow all origins in production, localhost in development
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env.backend"

settings = Settings() 
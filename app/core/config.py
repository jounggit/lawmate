import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://lawmate.example.com"
    ]
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://user:password@localhost/lawmate"
    )
    
    # Claude API
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    
    # 법률 API
    LAW_API_KEY: str = os.getenv("LAW_API_KEY", "")
    CASE_API_KEY: str = os.getenv("CASE_API_KEY", "")
    
    class Config:
        env_file = ".env"

settings = Settings()
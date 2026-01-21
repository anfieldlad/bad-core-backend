"""Application configuration management using Pydantic Settings."""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_key: str
    allowed_origins: str = "http://localhost:3000"
    
    # Database Configuration
    database_url: str = "sqlite:///./ktp.db"
    
    # Gemini Configuration
    google_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    
    # Cache Configuration
    cache_ttl_days: int = 30
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()

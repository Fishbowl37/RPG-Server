from pydantic_settings import BaseSettings
from functools import lru_cache
import json


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://rpg_user:rpg_password@localhost:5432/rpg_game"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Server
    debug: bool = True
    cors_origins: str = '["http://localhost:3000"]'
    
    # Game settings
    max_characters_per_user: int = 3
    battle_session_expiry_seconds: int = 600  # 10 minutes
    
    @property
    def cors_origins_list(self) -> list[str]:
        return json.loads(self.cors_origins)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


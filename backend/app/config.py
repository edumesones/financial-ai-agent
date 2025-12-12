# backend/app/config.py
"""Configuración centralizada usando pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

# Buscar .env en múltiples ubicaciones
_env_file = None
for path in [Path(".env"), Path("../.env"), Path(__file__).parent.parent.parent.parent / ".env"]:
    if path.exists():
        _env_file = str(path)
        break


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://agente:agente_dev@localhost:5432/agente_financiero"
    database_url_sync: str = "postgresql://agente:agente_dev@localhost:5432/agente_financiero"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Hugging Face
    hf_token: str = ""
    hf_model_llm: str = "meta-llama/Llama-3.1-8B-Instruct"
    hf_model_embeddings: str = "BAAI/bge-m3"
    hf_model_vision: str = "Qwen/Qwen3-VL-8B-Instruct:novita"  
    
    # Poppler (para PDFs)
    poppler_path: str = r"C:\poppler\poppler-25.12.0\Library\bin"
    
    # JWT
    jwt_secret: str = "dev-secret-change-in-production-32chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Agentes
    conciliacion_auto_approve_threshold: float = 0.95
    clasificacion_review_threshold: float = 0.75
    
    class Config:
        env_file = _env_file
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

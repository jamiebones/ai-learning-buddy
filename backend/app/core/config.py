from pydantic_settings import BaseSettings
import os
import secrets
from typing import List, Union

print(os.getcwd())

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Learning Buddy Backend Application"
    API_PREFIX: str = "/api"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    VERSION: str = "1.0.0"
    
    # Server settings
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend default
        "http://localhost:8000",  # FastAPI backend default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:password@localhost:5432/your_db_name"
    )
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "default_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "default_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "default_db")

    # JWT Token settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security settings
    ENFORCE_HTTPS: bool = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
    ALLOWED_HOSTS: Union[str, List[str]] = "*"
    
    # Rate limiting
    ENABLE_RATE_LIMIT: bool = os.getenv("ENABLE_RATE_LIMIT", "false").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_TIMEFRAME: int = int(os.getenv("RATE_LIMIT_TIMEFRAME", "60"))

    # Lilypad API settings
    LILYPAD_API_URL: str = os.getenv("LILYPAD_API_URL", "https://api.lilypad.ai/v1")
    DEFAULT_LILYPAD_API_TOKEN: str = "sk-lilypad-api-00000000000000000000000000000000"
    LILYPAD_API_TOKEN: str = os.getenv("LILYPAD_API_TOKEN", DEFAULT_LILYPAD_API_TOKEN)
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS: int = 1000
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Vector Store settings
    VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", os.path.join(os.getcwd(), "backend", "chroma_db"))

    # OpenAI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "default_openai_api_key")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context):
        # Convert ALLOWED_HOSTS to list if it's a string
        if isinstance(self.ALLOWED_HOSTS, str):
            self.ALLOWED_HOSTS = [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
        super().model_post_init(__context)

settings = Settings()

# Export these variables for direct import
VECTOR_STORE_DIR = settings.VECTOR_STORE_DIR
DEFAULT_EMBEDDING_MODEL = settings.DEFAULT_EMBEDDING_MODEL


"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/maicrosoft"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # N8N
    n8n_api_url: str = "http://localhost:5678/api/v1"
    n8n_api_key: str = ""

    # Encryption
    encryption_key: str = "change-me-32-bytes-key-here!!"

    # Agent Zero MCP
    agent_zero_mcp_url: str = "http://194.181.240.37:50001/mcp/t-T7kevcXi6oDxfrhK/http"

    class Config:
        env_file = ".env"


settings = Settings()

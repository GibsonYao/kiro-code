"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "小灶AI家庭管家"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ─── Database (PostgreSQL async) ───────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_family_butler"

    # ─── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ─── Aliyun OSS ───────────────────────────────────────────────────────────
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""
    OSS_ENDPOINT: str = ""
    OSS_BASE_URL: str = ""  # Public access URL prefix for stored objects

    # ─── WeChat Mini Program ───────────────────────────────────────────────────
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # ─── SMS (短信验证码) ──────────────────────────────────────────────────────
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""

    # ─── AI Services ──────────────────────────────────────────────────────────
    # DashScope (通义千问 / 通义万相)
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # OpenAI-compatible
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Stable Diffusion
    SD_API_KEY: str = ""
    SD_BASE_URL: str = ""

    # ─── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ─── Encryption (AES-256 for API keys stored in DB) ────────────────────────
    ENCRYPTION_KEY: str = "change-me-32-byte-key-for-aes256"

    # ─── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]


# Singleton settings instance
settings = Settings()

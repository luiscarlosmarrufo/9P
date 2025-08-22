"""
Configuration settings for the 9P Social Analytics Platform
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application
    APP_NAME: str = "9P Social Analytics"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = Field(..., min_length=32)
    
    # API
    API_V1_STR: str = "/v1"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://localhost:8501"
    ]
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_TEST_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend URL")
    
    # AWS
    AWS_ACCESS_KEY_ID: str = Field(..., description="AWS access key")
    AWS_SECRET_ACCESS_KEY: str = Field(..., description="AWS secret key")
    AWS_DEFAULT_REGION: str = "us-west-2"
    S3_BUCKET_NAME: str = Field(..., description="S3 bucket for raw data")
    S3_PROCESSED_BUCKET: str = Field(..., description="S3 bucket for processed data")
    
    # Social Media APIs
    TWITTER_API_KEY: str = Field(..., description="Twitter API key")
    TWITTER_API_SECRET: str = Field(..., description="Twitter API secret")
    TWITTER_ACCESS_TOKEN: str = Field(..., description="Twitter access token")
    TWITTER_ACCESS_TOKEN_SECRET: str = Field(..., description="Twitter access token secret")
    TWITTER_BEARER_TOKEN: str = Field(..., description="Twitter bearer token")
    
    REDDIT_CLIENT_ID: str = Field(..., description="Reddit client ID")
    REDDIT_CLIENT_SECRET: str = Field(..., description="Reddit client secret")
    REDDIT_USER_AGENT: str = "9P-Analytics/1.0"
    
    # OpenAI/vLLM
    OPENAI_API_KEY: Optional[str] = None
    VLLM_API_BASE: str = "http://localhost:8000/v1"
    VLLM_MODEL_NAME: str = "meta-llama/Llama-2-7b-chat-hf"
    
    # ML Configuration
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.7
    SENTIMENT_CONFIDENCE_THRESHOLD: float = 0.6
    BATCH_SIZE: int = 32
    MAX_SEQUENCE_LENGTH: int = 512
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    METRICS_ENABLED: bool = True
    
    # Rate Limiting
    TWITTER_RATE_LIMIT_WINDOW: int = 900  # 15 minutes
    TWITTER_RATE_LIMIT_CALLS: int = 300
    REDDIT_RATE_LIMIT_WINDOW: int = 60    # 1 minute
    REDDIT_RATE_LIMIT_CALLS: int = 60
    
    # Worker Configuration
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300
    CELERY_TASK_TIME_LIMIT: int = 600


# Global settings instance
settings = Settings()

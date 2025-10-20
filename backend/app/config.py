"""Configuration settings for Astro MVP Backend."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = Field(default="Astro MVP Backend", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database settings
    database_url: str = Field(
        default="sqlite:///./astro.db",
        env="DATABASE_URL"
    )
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_redis_url: str = Field(
        default="redis://localhost:6379/1",
        env="RATE_LIMIT_REDIS_URL"
    )
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://192.168.1.3:8080",  # Allow LAN frontend
        ],
        env="CORS_ORIGINS"
    )
    
    # Authentication settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        env="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    
    # Ephemeris settings
    ephemeris_data_path: str = Field(
        default="./ephemeris",
        env="EPHEMERIS_DATA_PATH"
    )
    
    # Calculation settings
    max_calculation_timeout: int = Field(
        default=30,
        env="MAX_CALCULATION_TIMEOUT"
    )
    
    # JWT settings
    jwt_secret_key: str = Field(
        default="your-super-secret-jwt-key-here-change-this",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Encryption settings
    encryption_key: str = Field(
        default="your-super-secret-encryption-key-here-change-this",
        env="ENCRYPTION_KEY"
    )
    
    # Ephemeris settings
    ephemeris_path: str = Field(
        default="./ephemeris",
        env="EPHEMERIS_PATH"
    )
    ruleset_version: str = Field(
        default="1.0.0",
        env="RULESET_VERSION"
    )
    ephemeris_version: str = Field(
        default="sepl_18",
        env="EPHEMERIS_VERSION"
    )
    ayanamsa_default: str = Field(
        default="Lahiri",
        env="AYANAMSA_DEFAULT"
    )
    house_system_default: str = Field(
        default="WholeSign",
        env="HOUSE_SYSTEM_DEFAULT"
    )
    
    # LLM settings
    llm_model: str = Field(
        default="gpt-4o",
        env="LLM_MODEL"
    )
    llm_temperature: float = Field(
        default=0.7,
        env="LLM_TEMPERATURE"
    )
    llm_max_tokens: int = Field(
        default=3000,  # Updated for GPT-5 compatibility
        env="LLM_MAX_TOKENS"
    )
    llm_seed: int = Field(
        default=7,
        env="LLM_SEED"
    )
    llm_timeout_ms: int = Field(
        default=60000,  # 60 seconds for GPT-5
        env="LLM_TIMEOUT_MS"
    )
    llm_streaming_enabled: bool = Field(
        default=False,
        env="LLM_STREAMING_ENABLED"
    )
    
    # Cache settings
    cache_ttl_hours: int = Field(
        default=24,
        env="CACHE_TTL_HOURS"
    )
    
    # Validation settings
    min_birth_year: int = Field(
        default=1900,
        env="MIN_BIRTH_YEAR"
    )
    max_birth_year: int = Field(
        default=2100,
        env="MAX_BIRTH_YEAR"
    )
    max_uncertainty_minutes: int = Field(
        default=10,
        env="MAX_UNCERTAINTY_MINUTES"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()

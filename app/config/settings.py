"""
Application settings and configuration management.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI Configuration
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field("2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment_name: str = Field("gpt-4", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    
    # Google Cloud Configuration
    google_cloud_project: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    bigquery_dataset: str = Field(..., env="BIGQUERY_DATASET")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Application Configuration
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    environment: str = Field("development", env="ENVIRONMENT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./agentic_app.db", env="DATABASE_URL")
    
    # Agent Configuration
    max_agent_iterations: int = Field(5, env="MAX_AGENT_ITERATIONS")
    agent_timeout_seconds: int = Field(300, env="AGENT_TIMEOUT_SECONDS")
    enable_query_optimization: bool = Field(True, env="ENABLE_QUERY_OPTIMIZATION")
    enable_impact_analysis: bool = Field(True, env="ENABLE_IMPACT_ANALYSIS")
    
    # BigQuery Configuration
    bigquery_max_results: int = Field(10000, env="BIGQUERY_MAX_RESULTS")
    bigquery_timeout_seconds: int = Field(60, env="BIGQUERY_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()

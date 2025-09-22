"""
Configuration management for Brebot.
Handles environment variables and application settings.
"""

import os
from pathlib import Path
from typing import Optional, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1:8b", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", env="OLLAMA_EMBEDDING_MODEL")
    
    # OpenAI Configuration (alternative)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # CrewAI Configuration
    agent_verbose: bool = Field(default=True, env="AGENT_VERBOSE")
    agent_max_iter: int = Field(default=3, env="AGENT_MAX_ITER")
    agent_memory: bool = Field(default=True, env="AGENT_MEMORY")
    
    # File Organization Settings
    default_work_dir: str = Field(default="/Users/bre/Desktop", env="DEFAULT_WORK_DIR")
    default_organized_dir: str = Field(default="/Users/bre/Desktop/Organized", env="DEFAULT_ORGANIZED_DIR")
    default_backup_dir: str = Field(default="/Users/bre/Desktop/Backup", env="DEFAULT_BACKUP_DIR")
    
    max_files_per_folder: int = Field(default=50, env="MAX_FILES_PER_FOLDER")
    create_backup: bool = Field(default=True, env="CREATE_BACKUP")
    dry_run: bool = Field(default=False, env="DRY_RUN")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/brebot.log", env="LOG_FILE")
    log_max_size: str = Field(default="10MB", env="LOG_MAX_SIZE")
    log_retention: int = Field(default=7, env="LOG_RETENTION")
    
    # Docker Configuration
    docker_compose_file: str = Field(default="docker/docker-compose.yml", env="DOCKER_COMPOSE_FILE")
    ollama_container_name: str = Field(default="brebot-ollama", env="OLLAMA_CONTAINER_NAME")
    ollama_port: int = Field(default=11434, env="OLLAMA_PORT")
    
    # LlamaIndex Configuration
    vector_store_path: str = Field(default="./data/vector_store", env="VECTOR_STORE_PATH")
    chunk_size: int = Field(default=1024, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    
    # Security
    secret_key: Optional[str] = Field(default=None, env="SECRET_KEY")
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    @validator('default_work_dir', 'default_organized_dir', 'default_backup_dir')
    def validate_directories(cls, v):
        """Ensure directories exist or can be created."""
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create directory {v}: {e}")
        return str(path.absolute())
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings() -> Settings:
    """
    Load application settings from environment variables.
    
    Returns:
        Settings: Configured settings object
        
    Raises:
        ValueError: If required settings are missing or invalid
    """
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    try:
        settings = Settings()
        
        # Validate critical settings
        if not settings.ollama_base_url:
            raise ValueError("OLLAMA_BASE_URL is required")
        
        # Ensure log directory exists
        log_dir = Path(settings.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return settings
        
    except Exception as e:
        raise ValueError(f"Failed to load settings: {e}")


def get_llm_config(settings: Settings) -> dict:
    """
    Get LLM configuration based on settings.
    
    Args:
        settings: Application settings
        
    Returns:
        dict: LLM configuration
    """
    if settings.openai_api_key:
        return {
            "provider": "openai",
            "api_key": settings.openai_api_key,
            "model": settings.openai_model,
            "base_url": None
        }
    else:
        return {
            "provider": "ollama",
            "api_key": None,
            "model": settings.ollama_model,
            "base_url": settings.ollama_base_url
        }


def get_embedding_config(settings: Settings) -> dict:
    """
    Get embedding configuration based on settings.
    
    Args:
        settings: Application settings
        
    Returns:
        dict: Embedding configuration
    """
    return {
        "provider": "ollama",
        "model": settings.ollama_embedding_model,
        "base_url": settings.ollama_base_url
    }


# Global settings instance
settings = load_settings()

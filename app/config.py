"""
Configuration settings for the application.
"""
import os
from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables with defaults."""
    
    # API settings
    API_HOST: str = Field("0.0.0.0", description="API host")
    API_PORT: int = Field(8000, description="API port")
    API_WORKERS: int = Field(4, description="Number of API workers")
    API_LOG_LEVEL: str = Field("info", description="API log level")
    
    # Model paths
    WHISPER_MODEL_PATH: str = Field("/workspace/Agent/workspace/Agent/app/models/whisper/ggml-large.bin", description="Path to Whisper model")
    TTS_MODEL_PATH: str = Field("/workspace/Agent/workspace/Agent/app/models/tts/en-us-kathleen-high.onnx", description="Path to TTS model")
    
    # Ollama settings
    OLLAMA_HOST: str = Field("localhost", description="Ollama host")
    OLLAMA_PORT: int = Field(11434, description="Ollama port")
    OLLAMA_MODEL: str = Field("agent-model:latest", description="Ollama model name")
    
    # RunPod settings
    RUNPOD_TIMEOUT: int = Field(120, description="RunPod API timeout in seconds")
    RUNPOD_RETRY_COUNT: int = Field(3, description="Number of retries for RunPod API")
    RUNPOD_STREAMING_SUPPORTED: bool = Field(True, description="Whether RunPod endpoint supports streaming")
    RUNPOD_ENDPOINT_ID: Optional[str] = Field(None, description="RunPod endpoint ID")
    
    # Performance settings
    WHISPER_THREADS: int = Field(4, description="Number of threads for Whisper")
    TTS_THREADS: int = Field(4, description="Number of threads for TTS")
    
    # Security settings
    API_KEY_ENABLED: bool = Field(True, description="Enable API key authentication")
    API_KEY: Optional[str] = Field(None, description="API key for authentication")
    
    # Monitoring settings
    ENABLE_METRICS: bool = Field(True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(9090, description="Prometheus metrics port")
    
    # Paths
    BASE_DIR: Path = Path("/workspace/Agent/app")
    TEMP_DIR: Path = Field(Path("/workspace/temp-ai-agent"), description="Temporary directory for processing")
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Ensure temp directory exists
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

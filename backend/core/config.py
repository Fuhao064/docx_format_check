from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "Scriptor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # 文件路径
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    CACHE_DIR: str = os.path.join(BASE_DIR, "caches")
    CONFIG_DIR: str = os.path.join(BASE_DIR, "configs")

    # LLM 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    DEFAULT_MODEL: str = "gpt-4"

    # 处理配置
    MAX_WORKERS: int = 4
    MAX_CONCURRENT_DOCS: int = 3
    CONTEXT_TTL_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CACHE_DIR, exist_ok=True)
os.makedirs(settings.CONFIG_DIR, exist_ok=True)

"""
应用配置模块
"""
import os
from typing import Optional, List, Any
from pydantic import validator
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """应用设置"""
    
    # 基本配置
    app_name: str = "招标投标规范智能审核系统"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8090
    
    # 安全配置
    secret_key: str = "your_super_secret_key_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 数据库配置 - 开发阶段使用SQLite
    database_url: str = "sqlite:///./zaobiao.db"
    test_database_url: str = "sqlite:///./test_zaobiao.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600
    cache_prefix: str = "zaobiao:"
    
    # Neo4j配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # MongoDB配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "zaobiao_mongo"
    
    # 数据库开关控制（开发环境）
    enable_neo4j: bool = False  # 开发环境默认关闭
    enable_mongodb: bool = False  # 开发环境默认关闭
    
    # DeepSeek API配置
    deepseek_api_key: str = "your_deepseek_api_key"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 4000
    deepseek_temperature: float = 0.7
    
    # TextIn API配置
    textin_api_key: str = "your_textin_api_key"
    textin_base_url: str = "https://api.textin.com"
    textin_app_id: str = "your_textin_app_id"
    textin_timeout: int = 300
    textin_max_file_size: int = 50  # MB
    
    # 文件配置
    upload_dir: str = "./uploads"
    max_file_size: str = "50MB"
    allowed_file_types: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/jpeg",
        "image/png",
        "image/gif"
    ]
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API配置
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    
    # 限流配置
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # CORS配置
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    @validator("max_file_size")
    def parse_max_file_size(cls, v):
        """解析文件大小限制"""
        if isinstance(v, str):
            if v.upper().endswith("MB"):
                return int(v[:-2]) * 1024 * 1024
            elif v.upper().endswith("KB"):
                return int(v[:-2]) * 1024
            elif v.upper().endswith("GB"):
                return int(v[:-2]) * 1024 * 1024 * 1024
        return int(v)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# 创建全局设置实例
settings = AppSettings()


def get_settings() -> AppSettings:
    """获取应用设置"""
    return settings

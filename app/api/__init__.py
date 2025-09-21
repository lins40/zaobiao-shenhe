"""
API模块
"""
from fastapi import APIRouter

from app.api.endpoints import documents, health

# 创建API路由器
api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(health.router, prefix="/health", tags=["系统监控"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档管理"])

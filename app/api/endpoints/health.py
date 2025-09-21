"""
系统健康检查端点
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import time
import asyncio

from app.core.database import get_redis, get_neo4j, get_mongodb
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get("/", summary="系统健康检查")
async def health_check() -> Dict[str, Any]:
    """
    系统健康检查
    
    检查各个组件的连接状态：
    - 应用状态
    - 数据库连接
    - Redis连接  
    - Neo4j连接
    - MongoDB连接
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": settings.app_name,
        "version": settings.version,
        "components": {}
    }
    
    # 检查Redis连接
    try:
        redis_client = get_redis()
        redis_client.ping()
        health_status["components"]["redis"] = {"status": "healthy", "message": "连接正常"}
    except Exception as e:
        health_status["components"]["redis"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"
    
    # 检查Neo4j连接
    try:
        neo4j_graph = get_neo4j()
        neo4j_graph.run("RETURN 1")
        health_status["components"]["neo4j"] = {"status": "healthy", "message": "连接正常"}
    except Exception as e:
        health_status["components"]["neo4j"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"
    
    # 检查MongoDB连接
    try:
        mongo_db = await get_mongodb()
        await mongo_db.list_collection_names()
        health_status["components"]["mongodb"] = {"status": "healthy", "message": "连接正常"}
    except Exception as e:
        health_status["components"]["mongodb"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/detailed", summary="详细健康检查")
async def detailed_health_check() -> Dict[str, Any]:
    """
    详细的系统健康检查
    
    包含更多系统信息：
    - 内存使用情况
    - 磁盘空间
    - 网络连接
    - 配置状态
    """
    import psutil
    import os
    
    detailed_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": settings.app_name,
        "version": settings.version,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "processes": len(psutil.pids()),
            "boot_time": psutil.boot_time()
        },
        "config": {
            "debug": settings.debug,
            "log_level": settings.log_level,
            "upload_dir": settings.upload_dir,
            "max_file_size": settings.max_file_size
        },
        "components": {}
    }
    
    # 基本健康检查
    basic_health = await health_check()
    detailed_status["components"] = basic_health["components"]
    
    # 检查上传目录
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        if os.access(settings.upload_dir, os.W_OK):
            detailed_status["components"]["upload_dir"] = {
                "status": "healthy", 
                "message": "上传目录可写"
            }
        else:
            detailed_status["components"]["upload_dir"] = {
                "status": "unhealthy", 
                "message": "上传目录不可写"
            }
            detailed_status["status"] = "degraded"
    except Exception as e:
        detailed_status["components"]["upload_dir"] = {
            "status": "unhealthy", 
            "message": str(e)
        }
        detailed_status["status"] = "degraded"
    
    return detailed_status


@router.get("/readiness", summary="就绪检查")  
async def readiness_check() -> Dict[str, Any]:
    """
    应用就绪检查
    
    检查应用是否准备好接收请求
    """
    readiness_status = {
        "ready": True,
        "timestamp": time.time(),
        "checks": {}
    }
    
    # 检查必要的数据库连接
    try:
        redis_client = get_redis()
        redis_client.ping()
        readiness_status["checks"]["redis"] = True
    except Exception:
        readiness_status["checks"]["redis"] = False
        readiness_status["ready"] = False
    
    return readiness_status


@router.get("/liveness", summary="存活检查")
async def liveness_check() -> Dict[str, Any]:
    """
    应用存活检查
    
    检查应用是否正在运行
    """
    return {
        "alive": True,
        "timestamp": time.time(),
        "uptime": time.time() - psutil.Process().create_time()
    }

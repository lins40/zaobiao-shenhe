"""
FastAPI主应用入口
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import traceback
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_databases, close_databases
from app.core.logging import configure_logging, request_logger, error_logger
from app.api import api_router

settings = get_settings()

# 配置日志
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_databases()
    print(f"🚀 {settings.app_name} v{settings.version} 启动成功")
    yield
    # 关闭时清理资源
    await close_databases()
    print("✅ 应用关闭，资源清理完成")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="基于AI大模型的招标投标规范智能审核系统",
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# 添加可信主机中间件
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", settings.host]
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    # 记录请求日志
    request_logger.log_request(
        method=request.method,
        url=str(request.url),
        headers=dict(request.headers),
        user_id=getattr(request.state, 'user_id', None)
    )
    
    try:
        response = await call_next(request)
        
        # 记录响应日志
        process_time = time.time() - start_time
        request_logger.log_response(
            status_code=response.status_code,
            response_time=process_time,
            user_id=getattr(request.state, 'user_id', None)
        )
        
        # 添加响应时间头
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        # 记录错误日志
        error_logger.log_api_error(
            api_name=f"{request.method} {request.url.path}",
            error=e,
            request_data={
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers)
            }
        )
        
        # 返回错误响应
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "服务器内部错误，请稍后重试",
                "timestamp": time.time()
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    error_logger.log_api_error(
        api_name=f"{request.method} {request.url.path}",
        error=exc,
        request_data={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
    )
    
    if settings.debug:
        # 开发环境返回详细错误信息
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "timestamp": time.time()
            }
        )
    else:
        # 生产环境返回通用错误信息
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "服务器内部错误，请稍后重试",
                "timestamp": time.time()
            }
        )


# 健康检查端点
@app.get("/health", tags=["系统监控"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "timestamp": time.time()
    }


@app.get("/", tags=["系统监控"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用{settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }


# 包含API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

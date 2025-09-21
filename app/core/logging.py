"""
日志配置模块
"""
import structlog
import logging
import sys
from typing import Any, Dict
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()


def configure_logging():
    """配置结构化日志"""
    
    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.debug 
            else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """获取结构化日志器"""
    return structlog.get_logger(name)


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("request")
    
    def log_request(self, method: str, url: str, headers: Dict[str, Any] = None, 
                   body: Any = None, user_id: str = None):
        """记录请求日志"""
        self.logger.info(
            "API request",
            method=method,
            url=url,
            headers=headers or {},
            body=body,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_response(self, status_code: int, response_time: float, 
                    response_size: int = None, user_id: str = None):
        """记录响应日志"""
        self.logger.info(
            "API response",
            status_code=status_code,
            response_time_ms=response_time * 1000,
            response_size=response_size,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )


class BusinessLogger:
    """业务日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("business")
    
    def log_document_upload(self, document_id: str, filename: str, 
                           file_size: int, user_id: str):
        """记录文档上传日志"""
        self.logger.info(
            "Document uploaded",
            document_id=document_id,
            filename=filename,
            file_size=file_size,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_document_parse(self, document_id: str, parse_time: float, 
                          success: bool, error: str = None):
        """记录文档解析日志"""
        self.logger.info(
            "Document parsed",
            document_id=document_id,
            parse_time_seconds=parse_time,
            success=success,
            error=error,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_audit_start(self, audit_id: str, document_id: str, user_id: str):
        """记录审核开始日志"""
        self.logger.info(
            "Audit started",
            audit_id=audit_id,
            document_id=document_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_audit_complete(self, audit_id: str, score: float, 
                          issue_count: int, audit_time: float):
        """记录审核完成日志"""
        self.logger.info(
            "Audit completed",
            audit_id=audit_id,
            score=score,
            issue_count=issue_count,
            audit_time_seconds=audit_time,
            timestamp=datetime.utcnow().isoformat()
        )


class ErrorLogger:
    """错误日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("error")
    
    def log_api_error(self, api_name: str, error: Exception, 
                     request_data: Any = None):
        """记录API错误日志"""
        self.logger.error(
            "API error",
            api_name=api_name,
            error_type=type(error).__name__,
            error_message=str(error),
            request_data=request_data,
            timestamp=datetime.utcnow().isoformat(),
            exc_info=True
        )
    
    def log_database_error(self, operation: str, error: Exception, 
                          table: str = None):
        """记录数据库错误日志"""
        self.logger.error(
            "Database error",
            operation=operation,
            table=table,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.utcnow().isoformat(),
            exc_info=True
        )
    
    def log_external_api_error(self, service: str, endpoint: str, 
                              error: Exception, retry_count: int = 0):
        """记录外部API错误日志"""
        self.logger.error(
            "External API error",
            service=service,
            endpoint=endpoint,
            error_type=type(error).__name__,
            error_message=str(error),
            retry_count=retry_count,
            timestamp=datetime.utcnow().isoformat(),
            exc_info=True
        )


# 全局日志器实例
request_logger = RequestLogger()
business_logger = BusinessLogger()
error_logger = ErrorLogger()

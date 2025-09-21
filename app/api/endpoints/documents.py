"""
文档管理API接口 - Week 3 增强版本
集成了文件存储服务、解析服务、任务管理等功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import uuid
import os
import time
from datetime import datetime

from app.services.document_service import document_service
from app.services.file_storage_service import file_storage_service
from app.utils.cache_manager import RateLimiter
from app.core.config import get_settings
from app.core.logging import business_logger, error_logger

settings = get_settings()
router = APIRouter()

# 创建限流器
upload_limiter = RateLimiter(max_requests=10, window_seconds=60)


@router.get("/", summary="获取文档列表")
async def get_documents(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    status: Optional[str] = Query(None, description="文档状态过滤"),
    uploaded_by: Optional[str] = Query(None, description="上传者过滤")
) -> Dict[str, Any]:
    """
    获取文档列表
    
    支持分页和筛选：
    - 按状态筛选
    - 按上传者筛选
    - 分页查询
    """
    try:
        documents = document_service.get_documents(
            skip=skip,
            limit=limit,
            status=status,
            uploaded_by=uploaded_by
        )
        
        # 转换为响应格式
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "filename": doc.original_filename,
                "file_size": doc.file_size,
                "content_type": doc.content_type,
                "status": doc.status,
                "audit_status": doc.audit_status,
                "audit_score": doc.audit_score,
                "issue_count": doc.issue_count,
                "risk_level": doc.risk_level,
                "page_count": doc.page_count,
                "parse_time": doc.parse_time,
                "uploaded_by": doc.uploaded_by,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "parsed_at": doc.parsed_at.isoformat() if doc.parsed_at else None,
                "audited_at": doc.audited_at.isoformat() if doc.audited_at else None
            })
        
        return {
            "success": True,
            "data": {
                "documents": document_list,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": len(document_list)
                }
            }
        }
    
    except Exception as e:
        error_logger.log_api_error(
            api_name="get_documents",
            error=e,
            request_data={"skip": skip, "limit": limit, "status": status}
        )
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.post("/upload", summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Query(None, description="上传者ID")
) -> Dict[str, Any]:
    """
    上传文档文件
    
    支持的文件格式：
    - PDF
    - Word (doc, docx)
    - Excel (xls, xlsx)
    - PowerPoint (ppt, pptx)
    - 图片 (jpg, png, gif, bmp, tiff)
    """
    try:
        # 限流检查
        client_id = f"upload_{uploaded_by or 'anonymous'}"
        allowed, rate_info = upload_limiter.is_allowed(client_id)
        
        if not allowed:
            raise HTTPException(
                status_code=429, 
                detail=f"上传频率限制，请{rate_info['reset_time']}秒后重试"
            )
        
        # 验证文件类型
        content_type = file.content_type
        if content_type not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {content_type}"
            )
        
        # 读取文件内容并验证大小
        file_content = await file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 ({settings.max_file_size} bytes)"
            )
        
        # 上传文档
        document = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            content_type=content_type,
            uploaded_by=uploaded_by
        )
        
        # 记录业务日志
        business_logger.log_document_upload(
            document_id=document.id,
            filename=file.filename,
            file_size=len(file_content),
            user_id=uploaded_by or "anonymous"
        )
        
        return {
            "success": True,
            "message": "文档上传成功，正在解析中...",
            "data": {
                "id": document.id,
                "filename": document.original_filename,
                "file_size": document.file_size,
                "content_type": document.content_type,
                "status": document.status,
                "created_at": document.created_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_api_error(
            api_name="upload_document",
            error=e,
            request_data={"filename": file.filename if file else "unknown"}
        )
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/{document_id}", summary="获取文档详情")
async def get_document(document_id: str) -> Dict[str, Any]:
    """
    获取指定文档的详细信息
    """
    try:
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            "success": True,
            "data": {
                "id": document.id,
                "filename": document.original_filename,
                "file_size": document.file_size,
                "content_type": document.content_type,
                "status": document.status,
                "audit_status": document.audit_status,
                "page_count": document.page_count,
                "audit_score": document.audit_score,
                "issue_count": document.issue_count,
                "risk_level": document.risk_level,
                "parse_time": document.parse_time,
                "parse_error": document.parse_error,
                "uploaded_by": document.uploaded_by,
                "metadata_json": document.metadata_json,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                "parsed_at": document.parsed_at.isoformat() if document.parsed_at else None,
                "audited_at": document.audited_at.isoformat() if document.audited_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_api_error(
            api_name="get_document",
            error=e,
            request_data={"document_id": document_id}
        )
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")


@router.get("/{document_id}/content", summary="获取文档内容")
async def get_document_content(document_id: str) -> Dict[str, Any]:
    """
    获取文档的解析内容
    """
    try:
        content = document_service.get_document_content(document_id)
        if not content:
            raise HTTPException(status_code=404, detail="文档内容不存在或未解析完成")
        
        return {
            "success": True,
            "data": content
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_api_error(
            api_name="get_document_content",
            error=e,
            request_data={"document_id": document_id}
        )
        raise HTTPException(status_code=500, detail=f"获取文档内容失败: {str(e)}")


@router.post("/{document_id}/audit", summary="开始审核文档")
async def start_audit(
    document_id: str,
    rules: List[str] = Query([], description="审核规则列表")
) -> Dict[str, Any]:
    """
    开始审核文档
    
    使用DeepSeek API进行智能合规性分析
    """
    try:
        # 检查文档是否存在
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 默认规则
        if not rules:
            rules = [
                "检查是否包含完整的招标公告内容",
                "验证投标截止时间是否合理",
                "检查资质要求是否明确",
                "验证评标方法是否规范",
                "检查是否存在歧视性条款",
                "验证保证金要求是否合规",
                "检查开标时间地点是否明确",
                "验证联系方式信息完整性"
            ]
        
        # 开始审核
        success = await document_service.start_audit(document_id, rules)
        
        if success:
            # 记录业务日志
            business_logger.log_document_parse(
                document_id=document_id,
                parse_time=0,
                success=True,
                message="审核任务启动成功"
            )
            
            return {
                "success": True,
                "message": "审核任务已启动，请稍后查看结果",
                "data": {
                    "document_id": document_id,
                    "rules_count": len(rules),
                    "rules": rules
                }
            }
        else:
            raise HTTPException(status_code=400, detail="审核启动失败，请检查文档状态")
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_api_error(
            api_name="start_audit",
            error=e,
            request_data={"document_id": document_id, "rules_count": len(rules)}
        )
        raise HTTPException(status_code=500, detail=f"启动审核失败: {str(e)}")


@router.get("/{document_id}/audit", summary="获取审核结果")
async def get_audit_result(document_id: str) -> Dict[str, Any]:
    """
    获取文档的审核结果
    """
    try:
        result = document_service.get_audit_result(document_id)
        if not result:
            raise HTTPException(status_code=404, detail="审核结果不存在或审核未完成")
        
        return {
            "success": True,
            "data": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_api_error(
            api_name="get_audit_result",
            error=e,
            request_data={"document_id": document_id}
        )
        raise HTTPException(status_code=500, detail=f"获取审核结果失败: {str(e)}")


@router.delete("/{document_id}", summary="删除文档")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """
    删除指定文档及其相关数据
    """
    try:
        success = document_service.delete_document(document_id)
        if success:
            return {
                "success": True,
                "message": "文档删除成功",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_api_error(
            api_name="delete_document",
            error=e,
            request_data={"document_id": document_id}
        )
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.get("/statistics/overview", summary="获取文档统计信息")
async def get_statistics() -> Dict[str, Any]:
    """
    获取文档系统的统计信息
    """
    try:
        stats = document_service.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        error_logger.log_api_error(
            api_name="get_statistics",
            error=e,
            request_data={}
        )
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 后台任务函数保留兼容性
async def parse_document_task(document_id: str):
    """
    文档解析后台任务（兼容性保留）
    实际解析由document_service.parse_document_async处理
    """
    try:
        start_time = time.time()
        
        # 调用服务层的异步解析
        success = await document_service.parse_document_async(document_id)
        
        parse_time = time.time() - start_time
        
        business_logger.log_document_parse(
            document_id=document_id,
            parse_time=parse_time,
            success=success
        )
        
    except Exception as e:
        error_logger.log_api_error(
            api_name="parse_document_task",
            error=e,
            request_data={"document_id": document_id}
        )
        
        business_logger.log_document_parse(
            document_id=document_id,
            parse_time=0,
            success=False,
            error=str(e)
        )


# ========== Week 3 新增API端点 ==========

@router.get("/storage/stats", summary="获取存储统计信息")
async def get_storage_stats() -> Dict[str, Any]:
    """
    获取文件存储统计信息
    """
    try:
        stats = file_storage_service.get_storage_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        error_logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")


@router.get("/supported-types", summary="获取支持的文件类型")
async def get_supported_file_types() -> Dict[str, Any]:
    """
    获取系统支持的文件类型信息
    """
    from app.services.file_storage_service import FileTypeValidator
    
    try:
        return {
            "success": True,
            "data": {
                "extensions": FileTypeValidator.get_supported_extensions(),
                "categories": FileTypeValidator.get_supported_categories(),
                "max_file_size": settings.max_file_size,
                "max_file_size_mb": settings.max_file_size / (1024 * 1024)
            }
        }
    except Exception as e:
        error_logger.error(f"获取支持文件类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取支持文件类型失败: {str(e)}")


@router.post("/validate", summary="验证文件类型")
async def validate_file_type(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    验证文件类型是否支持（不保存文件）
    """
    try:
        # 读取文件内容进行验证
        content = await file.read()
        
        from app.services.file_storage_service import FileTypeValidator
        validation_result = FileTypeValidator.validate_file_type(file.filename, content)
        
        return {
            "success": True,
            "data": validation_result
        }
        
    except Exception as e:
        error_logger.error(f"文件类型验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件类型验证失败: {str(e)}")


@router.get("/duplicates/{file_hash}", summary="检查文件是否重复")
async def check_file_duplicate(file_hash: str) -> Dict[str, Any]:
    """
    基于文件hash检查是否为重复文件
    """
    try:
        existing_path = await file_storage_service.check_file_exists(file_hash)
        
        return {
            "success": True,
            "data": {
                "is_duplicate": existing_path is not None,
                "existing_path": existing_path
            }
        }
        
    except Exception as e:
        error_logger.error(f"检查文件重复失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查文件重复失败: {str(e)}")


@router.post("/batch/upload", summary="批量上传文档")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    uploaded_by: Optional[str] = Query(None, description="上传者")
) -> Dict[str, Any]:
    """
    批量上传多个文档
    """
    if len(files) > 10:  # 限制批量上传数量
        raise HTTPException(status_code=400, detail="批量上传文件数量不能超过10个")
    
    results = []
    
    for file in files:
        try:
            # 限流检查
            allowed, info = upload_limiter.is_allowed(f"batch_upload_{uploaded_by or 'anonymous'}")
            if not allowed:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"上传限流，请{info['retry_after']}秒后重试"
                })
                continue
            
            # 读取文件内容
            file_content = await file.read()
            
            # 上传文档
            document = await document_service.upload_document(
                file_content=file_content,
                filename=file.filename,
                content_type=file.content_type,
                uploaded_by=uploaded_by
            )
            
            results.append({
                "filename": file.filename,
                "success": True,
                "document_id": document.id,
                "stored_filename": document.filename
            })
            
        except Exception as e:
            error_logger.error(f"批量上传文件失败: {file.filename}, {e}")
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    return {
        "success": True,
        "data": {
            "results": results,
            "summary": {
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count
            }
        }
    }
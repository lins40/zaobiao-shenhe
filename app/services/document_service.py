"""
文档服务层
集成文档管理、解析、审核等功能
"""
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
import asyncio
import time
from datetime import datetime

from app.models.document import Document, DocumentStatus, AuditStatus
from app.services.external.textin_client import get_textin_client, ParseResult
from app.services.external.deepseek_client import get_deepseek_client
from app.utils.database_base import DatabaseBase
from app.utils.cache_manager import cache_manager, cached
from app.core.config import get_settings

settings = get_settings()


class DocumentService:
    """文档服务"""
    
    def __init__(self):
        self.db = DatabaseBase(Document)
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        uploaded_by: Optional[str] = None
    ) -> Document:
        """上传文档"""
        # 生成唯一文件名
        timestamp = int(time.time())
        file_ext = Path(filename).suffix
        unique_filename = f"{timestamp}_{filename}"
        file_path = self.upload_dir / unique_filename
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 创建文档记录
        document_data = {
            "filename": unique_filename,
            "original_filename": filename,
            "file_path": str(file_path),
            "file_size": len(file_content),
            "content_type": content_type,
            "status": DocumentStatus.UPLOADED,
            "uploaded_by": uploaded_by
        }
        
        document = self.db.create(document_data)
        
        # 异步触发解析
        asyncio.create_task(self.parse_document_async(document.id))
        
        return document
    
    async def parse_document_async(self, document_id: str) -> bool:
        """异步解析文档"""
        try:
            # 更新状态为解析中
            self.db.update(document_id, {"status": DocumentStatus.PARSING})
            
            # 获取文档信息
            document = self.db.get(document_id)
            if not document:
                return False
            
            # 调用TextIn API解析
            textin_client = await get_textin_client()
            parse_result = await textin_client.parse_document(document.file_path)
            
            if parse_result.success:
                # 更新解析结果
                update_data = {
                    "status": DocumentStatus.PARSED,
                    "parsed_content": parse_result.content,
                    "markdown_content": parse_result.markdown,
                    "page_count": parse_result.page_count,
                    "metadata_json": str(parse_result.metadata),
                    "parse_time": parse_result.processing_time,
                    "parsed_at": datetime.now()
                }
                
                self.db.update(document_id, update_data)
                
                # 缓存解析结果
                cache_key = f"document_content:{document_id}"
                cache_manager.set(cache_key, {
                    "content": parse_result.content,
                    "markdown": parse_result.markdown,
                    "metadata": parse_result.metadata
                }, ttl=3600)
                
                return True
            else:
                # 解析失败
                self.db.update(document_id, {
                    "status": DocumentStatus.PARSE_ERROR,
                    "parse_error": parse_result.error_message
                })
                return False
        
        except Exception as e:
            # 解析异常
            self.db.update(document_id, {
                "status": DocumentStatus.PARSE_ERROR,
                "parse_error": str(e)
            })
            return False
    
    @cached(ttl=1800, key_prefix="doc_list:")
    def get_documents(
        self, 
        skip: int = 0, 
        limit: int = 20,
        status: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> List[Document]:
        """获取文档列表"""
        filters = {}
        if status:
            filters["status"] = status
        if uploaded_by:
            filters["uploaded_by"] = uploaded_by
        
        return self.db.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="created_at",
            desc_order=True
        )
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """获取单个文档"""
        return self.db.get(document_id)
    
    def get_document_content(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档内容（优先从缓存）"""
        # 尝试从缓存获取
        cache_key = f"document_content:{document_id}"
        cached_content = cache_manager.get(cache_key)
        
        if cached_content:
            return cached_content
        
        # 从数据库获取
        document = self.db.get(document_id)
        if not document or document.status != DocumentStatus.PARSED:
            return None
        
        content = {
            "content": document.parsed_content,
            "markdown": document.markdown_content,
            "metadata": {
                "page_count": document.page_count,
                "file_size": document.file_size,
                "content_type": document.content_type,
                "parsed_at": document.parsed_at.isoformat() if document.parsed_at else None
            }
        }
        
        # 缓存内容
        cache_manager.set(cache_key, content, ttl=3600)
        
        return content
    
    async def start_audit(self, document_id: str, rules: List[str]) -> bool:
        """开始审核文档"""
        try:
            # 检查文档状态
            document = self.db.get(document_id)
            if not document or document.status != DocumentStatus.PARSED:
                return False
            
            # 更新审核状态
            self.db.update(document_id, {
                "audit_status": AuditStatus.IN_PROGRESS,
                "status": DocumentStatus.AUDITING
            })
            
            # 获取文档内容
            content = self.get_document_content(document_id)
            if not content:
                return False
            
            # 调用DeepSeek API进行合规性分析
            deepseek_client = await get_deepseek_client()
            audit_response = await deepseek_client.analyze_document_compliance(
                content["content"], 
                rules
            )
            
            if audit_response.success:
                # 解析审核结果
                import json
                try:
                    audit_data = json.loads(audit_response.content)
                    
                    # 更新审核结果
                    update_data = {
                        "status": DocumentStatus.AUDITED,
                        "audit_status": AuditStatus.COMPLETED,
                        "audit_score": audit_data.get("overall_score", 0),
                        "issue_count": len(audit_data.get("compliance_issues", [])),
                        "risk_level": audit_data.get("risk_level", "unknown"),
                        "audited_at": datetime.now()
                    }
                    
                    self.db.update(document_id, update_data)
                    
                    # 缓存审核结果
                    cache_key = f"audit_result:{document_id}"
                    cache_manager.set(cache_key, audit_data, ttl=7200)
                    
                    return True
                
                except json.JSONDecodeError:
                    # JSON解析失败
                    self.db.update(document_id, {
                        "status": DocumentStatus.AUDIT_ERROR,
                        "audit_status": AuditStatus.ERROR
                    })
                    return False
            
            else:
                # 审核失败
                self.db.update(document_id, {
                    "status": DocumentStatus.AUDIT_ERROR,
                    "audit_status": AuditStatus.ERROR
                })
                return False
        
        except Exception as e:
            # 审核异常
            self.db.update(document_id, {
                "status": DocumentStatus.AUDIT_ERROR,
                "audit_status": AuditStatus.ERROR
            })
            return False
    
    def get_audit_result(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取审核结果"""
        # 尝试从缓存获取
        cache_key = f"audit_result:{document_id}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # 检查文档审核状态
        document = self.db.get(document_id)
        if not document or document.audit_status != AuditStatus.COMPLETED:
            return None
        
        # 返回基本审核信息
        return {
            "overall_score": document.audit_score,
            "risk_level": document.risk_level,
            "issue_count": document.issue_count,
            "audited_at": document.audited_at.isoformat() if document.audited_at else None
        }
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            # 获取文档信息
            document = self.db.get(document_id)
            if not document:
                return False
            
            # 删除文件
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # 删除数据库记录
            self.db.delete(document_id)
            
            # 清除相关缓存
            cache_manager.delete(f"document_content:{document_id}")
            cache_manager.delete(f"audit_result:{document_id}")
            cache_manager.clear_pattern(f"doc_list:*")
            
            return True
        
        except Exception as e:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        cache_key = "document_statistics"
        cached_stats = cache_manager.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # 计算统计信息
        total_count = self.db.count()
        parsed_count = self.db.count({"status": DocumentStatus.PARSED})
        audited_count = self.db.count({"audit_status": AuditStatus.COMPLETED})
        error_count = self.db.count({"status": DocumentStatus.PARSE_ERROR})
        
        stats = {
            "total_documents": total_count,
            "parsed_documents": parsed_count,
            "audited_documents": audited_count,
            "error_documents": error_count,
            "parse_success_rate": round(parsed_count / total_count * 100, 2) if total_count > 0 else 0,
            "audit_success_rate": round(audited_count / parsed_count * 100, 2) if parsed_count > 0 else 0
        }
        
        # 缓存统计信息
        cache_manager.set(cache_key, stats, ttl=300)
        
        return stats


# 全局服务实例
document_service = DocumentService()

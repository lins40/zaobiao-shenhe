"""
TextIn API客户端封装
提供文档解析服务，支持PDF、Word、Excel、图片等格式转换为Markdown
"""
import httpx
import json
import asyncio
import base64
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
import time

from app.core.config import get_settings

settings = get_settings()


@dataclass
class TextInResponse:
    """TextIn API响应数据结构"""
    success: bool
    task_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Dict] = None
    markdown_content: Optional[str] = None
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    processing_time: Optional[float] = None


@dataclass
class ParseResult:
    """文档解析结果"""
    success: bool
    content: str
    markdown: str
    page_count: int
    metadata: Dict[str, Any]
    processing_time: float
    error_message: Optional[str] = None


class TextInClient:
    """TextIn API客户端"""
    
    def __init__(self):
        self.api_key = settings.textin_api_key
        self.base_url = settings.textin_base_url
        self.timeout = 300  # 5分钟超时
        self.max_retries = 3
        self.poll_interval = 2  # 轮询间隔(秒)
        
        # HTTP客户端配置
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "x-ti-app-id": settings.textin_app_id,
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def _upload_file(self, file_path: Union[str, Path], file_content: Optional[bytes] = None) -> TextInResponse:
        """上传文件到TextIn"""
        try:
            if file_content is None:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            
            # 将文件内容转换为base64
            file_b64 = base64.b64encode(file_content).decode('utf-8')
            file_name = Path(file_path).name if isinstance(file_path, (str, Path)) else "document"
            
            request_data = {
                "file": {
                    "name": file_name,
                    "content": file_b64
                },
                "options": {
                    "output_format": "markdown",
                    "extract_table": True,
                    "extract_image": True,
                    "preserve_layout": True
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/documents/parse",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return TextInResponse(
                    success=True,
                    task_id=data.get("task_id"),
                    status="submitted"
                )
            else:
                error_msg = f"文件上传失败: {response.status_code} - {response.text}"
                return TextInResponse(
                    success=False,
                    error_message=error_msg
                )
        
        except Exception as e:
            return TextInResponse(
                success=False,
                error_message=f"文件上传异常: {str(e)}"
            )
    
    async def _check_task_status(self, task_id: str) -> TextInResponse:
        """检查任务状态"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/tasks/{task_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                result = TextInResponse(
                    success=True,
                    task_id=task_id,
                    status=status
                )
                
                if status == "completed":
                    # 提取解析结果
                    result.result = data.get("result", {})
                    result.markdown_content = result.result.get("markdown", "")
                    result.page_count = result.result.get("page_count", 0)
                    result.processing_time = data.get("processing_time", 0)
                
                elif status == "failed":
                    result.error_message = data.get("error", "解析失败")
                    result.success = False
                
                return result
            
            else:
                return TextInResponse(
                    success=False,
                    error_message=f"状态查询失败: {response.status_code}"
                )
        
        except Exception as e:
            return TextInResponse(
                success=False,
                error_message=f"状态查询异常: {str(e)}"
            )
    
    async def _wait_for_completion(self, task_id: str, max_wait_time: int = 300) -> TextInResponse:
        """等待任务完成"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = await self._check_task_status(task_id)
            
            if not status_response.success:
                return status_response
            
            if status_response.status == "completed":
                return status_response
            
            elif status_response.status == "failed":
                return status_response
            
            elif status_response.status in ["submitted", "processing"]:
                await asyncio.sleep(self.poll_interval)
                continue
            
            else:
                return TextInResponse(
                    success=False,
                    error_message=f"未知状态: {status_response.status}"
                )
        
        return TextInResponse(
            success=False,
            error_message="任务超时"
        )
    
    async def parse_document(self, file_path: Union[str, Path], file_content: Optional[bytes] = None) -> ParseResult:
        """解析文档 - 主要接口"""
        start_time = time.time()
        
        # 1. 上传文件
        upload_response = await self._upload_file(file_path, file_content)
        if not upload_response.success:
            return ParseResult(
                success=False,
                content="",
                markdown="",
                page_count=0,
                metadata={},
                processing_time=time.time() - start_time,
                error_message=upload_response.error_message
            )
        
        # 2. 等待解析完成
        task_id = upload_response.task_id
        completion_response = await self._wait_for_completion(task_id)
        
        processing_time = time.time() - start_time
        
        if not completion_response.success:
            return ParseResult(
                success=False,
                content="",
                markdown="",
                page_count=0,
                metadata={},
                processing_time=processing_time,
                error_message=completion_response.error_message
            )
        
        # 3. 提取结果
        result_data = completion_response.result or {}
        markdown_content = completion_response.markdown_content or ""
        
        # 提取纯文本内容（去除markdown格式）
        plain_content = self._extract_plain_text(markdown_content)
        
        # 构建元数据
        metadata = {
            "task_id": task_id,
            "page_count": completion_response.page_count or 0,
            "file_name": Path(file_path).name if isinstance(file_path, (str, Path)) else "document",
            "processing_time": completion_response.processing_time or 0,
            "api_version": "v1",
            "extracted_at": time.time()
        }
        
        # 添加TextIn特定的元数据
        if result_data:
            metadata.update({
                "has_tables": result_data.get("table_count", 0) > 0,
                "has_images": result_data.get("image_count", 0) > 0,
                "confidence_score": result_data.get("confidence", 0),
                "language": result_data.get("language", "unknown")
            })
        
        return ParseResult(
            success=True,
            content=plain_content,
            markdown=markdown_content,
            page_count=completion_response.page_count or 0,
            metadata=metadata,
            processing_time=processing_time
        )
    
    def _extract_plain_text(self, markdown_content: str) -> str:
        """从Markdown内容中提取纯文本"""
        if not markdown_content:
            return ""
        
        # 简单的Markdown格式清理
        import re
        
        # 移除标题标记
        text = re.sub(r'^#+\s*', '', markdown_content, flags=re.MULTILINE)
        
        # 移除粗体和斜体标记
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # 移除链接格式
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # 移除代码块
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 移除表格分隔符
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'^[-\s\|]+$', '', text, flags=re.MULTILINE)
        
        # 清理多余的空白字符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    async def parse_document_batch(self, file_paths: List[Union[str, Path]]) -> List[ParseResult]:
        """批量解析文档"""
        tasks = []
        for file_path in file_paths:
            task = self.parse_document(file_path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ParseResult(
                    success=False,
                    content="",
                    markdown="",
                    page_count=0,
                    metadata={},
                    processing_time=0,
                    error_message=f"批量处理异常: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/formats")
            if response.status_code == 200:
                data = response.json()
                return data.get("supported_formats", [])
            return []
        except Exception:
            # 返回默认支持的格式
            return [
                "pdf", "doc", "docx", "xls", "xlsx", 
                "ppt", "pptx", "txt", "rtf",
                "jpg", "jpeg", "png", "bmp", "tiff"
            ]
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """获取API使用统计"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/usage")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局客户端实例
textin_client = TextInClient()


async def get_textin_client() -> TextInClient:
    """获取TextIn客户端实例"""
    return textin_client

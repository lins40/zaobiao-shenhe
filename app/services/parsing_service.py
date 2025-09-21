"""
文档解析服务 - Week 3 新增
提供文档解析任务管理、状态跟踪、批量处理等功能
"""
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

from app.services.external.textin_client import TextInClient
from app.services.external.deepseek_client import DeepSeekClient
from app.utils.cache_manager import cache_manager
from app.utils.database_base import DatabaseBase
from app.models.document import Document
from app.core.config import get_settings
from app.core.logging import business_logger, error_logger

settings = get_settings()


class ParseStatus(Enum):
    """解析状态枚举"""
    PENDING = "pending"           # 等待解析
    PROCESSING = "processing"     # 解析中
    COMPLETED = "completed"       # 解析完成
    FAILED = "failed"            # 解析失败
    TIMEOUT = "timeout"          # 解析超时
    CANCELLED = "cancelled"      # 已取消


class ParseTask:
    """解析任务"""
    
    def __init__(
        self,
        task_id: str,
        document_id: int,
        file_path: str,
        file_type: str,
        priority: int = 5,
        options: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.document_id = document_id
        self.file_path = file_path
        self.file_type = file_type
        self.priority = priority
        self.options = options or {}
        
        self.status = ParseStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.progress: int = 0
        
        # 回调函数
        self.callbacks: List[Callable] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'document_id': self.document_id,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'priority': self.priority,
            'options': self.options,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'result': self.result,
            'progress': self.progress
        }
    
    def add_callback(self, callback: Callable):
        """添加回调函数"""
        self.callbacks.append(callback)
    
    async def execute_callbacks(self):
        """执行回调函数"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    callback(self)
            except Exception as e:
                error_logger.error(f"回调函数执行失败: {e}")


class ParsingQueue:
    """解析任务队列"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.pending_tasks: List[ParseTask] = []
        self.processing_tasks: Dict[str, ParseTask] = {}
        self.completed_tasks: Dict[str, ParseTask] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
    
    async def add_task(self, task: ParseTask) -> str:
        """添加解析任务"""
        async with self._lock:
            # 按优先级插入（优先级高的在前）
            inserted = False
            for i, existing_task in enumerate(self.pending_tasks):
                if task.priority > existing_task.priority:
                    self.pending_tasks.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.pending_tasks.append(task)
            
            business_logger.info(f"解析任务已添加: {task.task_id}")
            return task.task_id
    
    async def get_next_task(self) -> Optional[ParseTask]:
        """获取下一个待处理任务"""
        async with self._lock:
            if self.pending_tasks:
                task = self.pending_tasks.pop(0)
                self.processing_tasks[task.task_id] = task
                return task
            return None
    
    async def complete_task(self, task_id: str, result: Dict[str, Any]):
        """标记任务完成"""
        async with self._lock:
            if task_id in self.processing_tasks:
                task = self.processing_tasks.pop(task_id)
                task.status = ParseStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                self.completed_tasks[task_id] = task
                await task.execute_callbacks()
                business_logger.info(f"解析任务完成: {task_id}")
    
    async def fail_task(self, task_id: str, error_message: str):
        """标记任务失败"""
        async with self._lock:
            if task_id in self.processing_tasks:
                task = self.processing_tasks.pop(task_id)
                task.status = ParseStatus.FAILED
                task.completed_at = datetime.now()
                task.error_message = error_message
                self.completed_tasks[task_id] = task
                await task.execute_callbacks()
                error_logger.error(f"解析任务失败: {task_id}, 错误: {error_message}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查各个队列
        for task_dict in [
            {task.task_id: task for task in self.pending_tasks},
            self.processing_tasks,
            self.completed_tasks
        ]:
            if task_id in task_dict:
                return task_dict[task_id].to_dict()
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        return {
            'pending_count': len(self.pending_tasks),
            'processing_count': len(self.processing_tasks),
            'completed_count': len(self.completed_tasks),
            'max_concurrent': self.max_concurrent,
            'total_tasks': len(self.pending_tasks) + len(self.processing_tasks) + len(self.completed_tasks)
        }


class DocumentParsingService:
    """文档解析服务"""
    
    def __init__(self):
        self.textin_client = TextInClient()
        self.deepseek_client = DeepSeekClient()
        self.db = DatabaseBase(Document)
        self.queue = ParsingQueue(max_concurrent=getattr(settings, 'max_concurrent_parsing', 3))
        self.is_running = False
        self._worker_tasks: List[asyncio.Task] = []
    
    async def start_workers(self):
        """启动工作线程"""
        if self.is_running:
            return
        
        self.is_running = True
        # 启动多个工作协程
        for i in range(self.queue.max_concurrent):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        business_logger.info(f"文档解析服务启动，工作线程数: {self.queue.max_concurrent}")
    
    async def stop_workers(self):
        """停止工作线程"""
        self.is_running = False
        
        # 取消所有工作任务
        for task in self._worker_tasks:
            task.cancel()
        
        # 等待所有任务完成
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        
        business_logger.info("文档解析服务已停止")
    
    async def _worker(self, worker_name: str):
        """工作协程"""
        business_logger.info(f"解析工作线程启动: {worker_name}")
        
        while self.is_running:
            try:
                # 获取信号量
                async with self.queue.semaphore:
                    # 获取下一个任务
                    task = await self.queue.get_next_task()
                    if not task:
                        await asyncio.sleep(1)  # 没有任务时休眠
                        continue
                    
                    # 执行解析任务
                    await self._execute_parse_task(task, worker_name)
                
            except asyncio.CancelledError:
                business_logger.info(f"解析工作线程已取消: {worker_name}")
                break
            except Exception as e:
                error_logger.error(f"解析工作线程异常 {worker_name}: {e}")
                await asyncio.sleep(5)  # 异常后休眠
    
    async def _execute_parse_task(self, task: ParseTask, worker_name: str):
        """执行解析任务"""
        try:
            business_logger.info(f"开始解析任务: {task.task_id} (worker: {worker_name})")
            
            # 更新任务状态
            task.status = ParseStatus.PROCESSING
            task.started_at = datetime.now()
            
            # 更新数据库状态
            await self._update_document_status(task.document_id, "parsing")
            
            # 执行具体的解析逻辑
            parse_result = await self._parse_document(task)
            
            # 任务完成
            await self.queue.complete_task(task.task_id, parse_result)
            
            # 更新数据库
            await self._update_document_result(task.document_id, parse_result)
            
        except Exception as e:
            error_logger.error(f"解析任务执行失败: {task.task_id}, 错误: {e}")
            await self.queue.fail_task(task.task_id, str(e))
            await self._update_document_status(task.document_id, "failed")
    
    async def _parse_document(self, task: ParseTask) -> Dict[str, Any]:
        """执行文档解析"""
        result = {
            'task_id': task.task_id,
            'document_id': task.document_id,
            'success': False,
            'parsed_content': None,
            'extracted_text': None,
            'metadata': {},
            'entities': [],
            'processing_time': 0,
            'error': None
        }
        
        start_time = datetime.now()
        
        try:
            # 1. 使用TextIn解析文档
            business_logger.info(f"开始TextIn解析: {task.file_path}")
            
            with open(task.file_path, 'rb') as f:
                file_content = f.read()
            
            # 调用TextIn API
            textin_result = await self.textin_client.parse_document_to_markdown(
                file_content,
                Path(task.file_path).name
            )
            
            if textin_result['success']:
                result['extracted_text'] = textin_result['markdown_content']
                result['metadata'].update(textin_result.get('metadata', {}))
                task.progress = 50
                
                # 2. 使用DeepSeek进行内容分析（可选）
                if task.options.get('enable_ai_analysis', False):
                    business_logger.info(f"开始AI内容分析: {task.task_id}")
                    
                    ai_analysis = await self.deepseek_client.analyze_document_content(
                        textin_result['markdown_content']
                    )
                    
                    if ai_analysis['success']:
                        result['entities'] = ai_analysis.get('entities', [])
                        result['metadata'].update(ai_analysis.get('metadata', {}))
                        task.progress = 80
                
                # 3. 缓存解析结果
                cache_key = f"parsed_doc:{task.document_id}"
                await cache_manager.set(cache_key, result, ttl=3600)
                
                result['success'] = True
                task.progress = 100
                
            else:
                result['error'] = textin_result.get('error', 'TextIn解析失败')
            
        except Exception as e:
            result['error'] = f"解析异常: {str(e)}"
            error_logger.error(f"文档解析异常: {task.task_id}, {e}")
        
        finally:
            end_time = datetime.now()
            result['processing_time'] = (end_time - start_time).total_seconds()
        
        return result
    
    async def _update_document_status(self, document_id: int, status: str):
        """更新文档状态"""
        try:
            self.db.update(document_id, {'status': status})
        except Exception as e:
            error_logger.error(f"更新文档状态失败: {document_id}, {e}")
    
    async def _update_document_result(self, document_id: int, parse_result: Dict[str, Any]):
        """更新文档解析结果"""
        try:
            update_data = {
                'status': 'parsed' if parse_result['success'] else 'parse_failed',
                'parsed_content': parse_result.get('extracted_text'),
                'parsing_metadata': json.dumps(parse_result.get('metadata', {})),
                'updated_at': datetime.now()
            }
            
            self.db.update(document_id, update_data)
            business_logger.info(f"文档解析结果已更新: {document_id}")
            
        except Exception as e:
            error_logger.error(f"更新文档解析结果失败: {document_id}, {e}")
    
    async def submit_parse_task(
        self,
        document_id: int,
        file_path: str,
        file_type: str,
        priority: int = 5,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """提交解析任务"""
        task_id = str(uuid.uuid4())
        
        task = ParseTask(
            task_id=task_id,
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
            priority=priority,
            options=options
        )
        
        await self.queue.add_task(task)
        
        # 缓存任务信息
        cache_key = f"parse_task:{task_id}"
        await cache_manager.set(cache_key, task.to_dict(), ttl=7200)
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 首先从队列中查找
        status = self.queue.get_task_status(task_id)
        if status:
            return status
        
        # 然后从缓存中查找
        cache_key = f"parse_task:{task_id}"
        cached_status = await cache_manager.get(cache_key)
        return cached_status
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消解析任务"""
        async with self.queue._lock:
            # 从待处理队列中移除
            for i, task in enumerate(self.queue.pending_tasks):
                if task.task_id == task_id:
                    task.status = ParseStatus.CANCELLED
                    self.queue.pending_tasks.pop(i)
                    self.queue.completed_tasks[task_id] = task
                    business_logger.info(f"解析任务已取消: {task_id}")
                    return True
            
            # 如果任务正在处理中，则无法取消
            if task_id in self.queue.processing_tasks:
                business_logger.warning(f"任务正在处理中，无法取消: {task_id}")
                return False
        
        return False
    
    async def batch_parse_documents(
        self,
        document_ids: List[int],
        options: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """批量解析文档"""
        task_ids = []
        
        for document_id in document_ids:
            try:
                # 获取文档信息
                doc = self.db.get(document_id)
                if not doc:
                    error_logger.warning(f"文档不存在: {document_id}")
                    continue
                
                # 提交解析任务
                task_id = await self.submit_parse_task(
                    document_id=document_id,
                    file_path=doc.file_path,
                    file_type=doc.content_type,
                    priority=3,  # 批量任务使用较低优先级
                    options=options
                )
                
                task_ids.append(task_id)
                
            except Exception as e:
                error_logger.error(f"提交批量解析任务失败: {document_id}, {e}")
        
        business_logger.info(f"批量解析任务已提交: {len(task_ids)}个任务")
        return task_ids
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        return self.queue.get_queue_stats()
    
    async def cleanup_completed_tasks(self, older_than_hours: int = 24):
        """清理已完成的任务"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleaned_count = 0
        
        async with self.queue._lock:
            tasks_to_remove = []
            for task_id, task in self.queue.completed_tasks.items():
                if task.completed_at and task.completed_at < cutoff_time:
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.queue.completed_tasks[task_id]
                cleaned_count += 1
        
        business_logger.info(f"清理已完成任务: {cleaned_count}个")
        return cleaned_count


# 创建全局解析服务实例
parsing_service = DocumentParsingService()

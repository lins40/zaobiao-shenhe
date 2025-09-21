"""
文件存储服务 - Week 3 新增
提供统一的文件存储管理，支持本地存储和云存储
"""
import os
import uuid
import shutil
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import hashlib
import magic

from app.core.config import get_settings
from app.core.logging import business_logger, error_logger

settings = get_settings()


class FileTypeValidator:
    """文件类型验证器"""
    
    # 支持的文件类型及其MIME类型
    SUPPORTED_TYPES = {
        # PDF文档
        'pdf': ['application/pdf'],
        
        # Word文档
        'word': [
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ],
        
        # Excel表格
        'excel': [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ],
        
        # PowerPoint演示文稿
        'powerpoint': [
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ],
        
        # 图片文件
        'image': [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp'
        ],
        
        # 文本文件
        'text': [
            'text/plain',
            'text/markdown',
            'text/csv',
            'application/rtf'
        ],
        
        # 压缩文件
        'archive': [
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed'
        ]
    }
    
    # 文件扩展名映射
    EXTENSION_MAPPING = {
        '.pdf': 'pdf',
        '.doc': 'word',
        '.docx': 'word',
        '.xls': 'excel',
        '.xlsx': 'excel',
        '.ppt': 'powerpoint',
        '.pptx': 'powerpoint',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.tiff': 'image',
        '.webp': 'image',
        '.txt': 'text',
        '.md': 'text',
        '.csv': 'text',
        '.rtf': 'text',
        '.zip': 'archive',
        '.rar': 'archive',
        '.7z': 'archive'
    }
    
    @classmethod
    def validate_file_type(cls, filename: str, content: bytes) -> Dict[str, Any]:
        """
        验证文件类型
        
        Args:
            filename: 文件名
            content: 文件内容
            
        Returns:
            验证结果字典
        """
        result = {
            'is_valid': False,
            'file_type': None,
            'mime_type': None,
            'extension': None,
            'category': None,
            'error': None
        }
        
        try:
            # 获取文件扩展名
            file_path = Path(filename)
            extension = file_path.suffix.lower()
            result['extension'] = extension
            
            # 检查扩展名是否支持
            if extension not in cls.EXTENSION_MAPPING:
                result['error'] = f"不支持的文件扩展名: {extension}"
                return result
            
            # 获取预期的文件类型
            expected_category = cls.EXTENSION_MAPPING[extension]
            result['category'] = expected_category
            
            # 使用python-magic检测实际MIME类型
            try:
                detected_mime = magic.from_buffer(content, mime=True)
                result['mime_type'] = detected_mime
            except Exception as e:
                business_logger.warning(f"MIME类型检测失败: {e}")
                # 降级到基于文件名的检测
                detected_mime, _ = mimetypes.guess_type(filename)
                result['mime_type'] = detected_mime
            
            # 验证MIME类型是否匹配
            expected_mimes = cls.SUPPORTED_TYPES.get(expected_category, [])
            if detected_mime in expected_mimes:
                result['is_valid'] = True
                result['file_type'] = expected_category
            else:
                result['error'] = f"文件内容与扩展名不匹配。检测到: {detected_mime}, 期望: {expected_mimes}"
            
            return result
            
        except Exception as e:
            error_logger.error(f"文件类型验证失败: {e}")
            result['error'] = f"文件类型验证异常: {str(e)}"
            return result
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """获取支持的文件扩展名列表"""
        return list(cls.EXTENSION_MAPPING.keys())
    
    @classmethod
    def get_supported_categories(cls) -> List[str]:
        """获取支持的文件类型分类"""
        return list(cls.SUPPORTED_TYPES.keys())


class FileStorageService:
    """文件存储服务"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.max_file_size = settings.max_file_size
        self.validator = FileTypeValidator()
        
        # 确保上传目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录结构
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        subdirs = ['documents', 'images', 'temp', 'archives']
        for subdir in subdirs:
            (self.upload_dir / subdir).mkdir(exist_ok=True)
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """计算文件hash值，用于重复检测"""
        return hashlib.sha256(content).hexdigest()
    
    def _generate_unique_filename(self, original_filename: str, file_hash: str) -> str:
        """生成唯一的文件名"""
        file_path = Path(original_filename)
        extension = file_path.suffix.lower()
        
        # 使用时间戳和hash生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        hash_prefix = file_hash[:8]
        
        return f"{timestamp}_{unique_id}_{hash_prefix}{extension}"
    
    def _get_storage_path(self, file_category: str, filename: str) -> Path:
        """获取文件存储路径"""
        category_mapping = {
            'pdf': 'documents',
            'word': 'documents',
            'excel': 'documents',
            'powerpoint': 'documents',
            'text': 'documents',
            'image': 'images',
            'archive': 'archives'
        }
        
        subdir = category_mapping.get(file_category, 'documents')
        return self.upload_dir / subdir / filename
    
    async def save_file(
        self,
        filename: str,
        content: bytes,
        uploaded_by: str = 'system'
    ) -> Dict[str, Any]:
        """
        保存文件到存储系统
        
        Args:
            filename: 原始文件名
            content: 文件内容
            uploaded_by: 上传者
            
        Returns:
            保存结果信息
        """
        result = {
            'success': False,
            'file_info': {},
            'error': None
        }
        
        try:
            # 1. 文件大小检查
            file_size = len(content)
            if file_size > self.max_file_size:
                result['error'] = f"文件大小超过限制 ({file_size} > {self.max_file_size})"
                return result
            
            # 2. 文件类型验证
            validation_result = self.validator.validate_file_type(filename, content)
            if not validation_result['is_valid']:
                result['error'] = validation_result['error']
                return result
            
            # 3. 计算文件hash
            file_hash = self._calculate_file_hash(content)
            
            # 4. 生成唯一文件名
            unique_filename = self._generate_unique_filename(filename, file_hash)
            
            # 5. 确定存储路径
            storage_path = self._get_storage_path(validation_result['category'], unique_filename)
            
            # 6. 保存文件
            with open(storage_path, 'wb') as f:
                f.write(content)
            
            # 7. 构建文件信息
            file_info = {
                'original_filename': filename,
                'stored_filename': unique_filename,
                'file_path': str(storage_path),
                'relative_path': str(storage_path.relative_to(self.upload_dir)),
                'file_size': file_size,
                'file_hash': file_hash,
                'mime_type': validation_result['mime_type'],
                'file_category': validation_result['category'],
                'file_extension': validation_result['extension'],
                'uploaded_by': uploaded_by,
                'upload_time': datetime.now().isoformat(),
                'storage_type': 'local'
            }
            
            result['success'] = True
            result['file_info'] = file_info
            
            business_logger.info(f"文件保存成功: {filename} -> {unique_filename}")
            return result
            
        except Exception as e:
            error_logger.error(f"文件保存失败: {e}")
            result['error'] = f"文件保存异常: {str(e)}"
            return result
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            删除结果
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                result['success'] = True
                business_logger.info(f"文件删除成功: {file_path}")
            else:
                result['error'] = f"文件不存在: {file_path}"
            
        except Exception as e:
            error_logger.error(f"文件删除失败: {e}")
            result['error'] = f"文件删除异常: {str(e)}"
        
        return result
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat_info = path.stat()
            return {
                'file_path': str(path),
                'file_size': stat_info.st_size,
                'created_time': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'is_file': path.is_file(),
                'exists': True
            }
            
        except Exception as e:
            error_logger.error(f"获取文件信息失败: {e}")
            return None
    
    async def check_file_exists(self, file_hash: str) -> Optional[str]:
        """
        检查文件是否已存在（基于hash）
        
        Args:
            file_hash: 文件hash值
            
        Returns:
            如果存在返回文件路径，否则返回None
        """
        try:
            # 搜索所有子目录中包含该hash的文件
            for subdir in self.upload_dir.iterdir():
                if subdir.is_dir():
                    for file_path in subdir.glob(f"*{file_hash[:8]}*"):
                        if file_path.is_file():
                            return str(file_path)
            return None
            
        except Exception as e:
            error_logger.error(f"检查文件存在性失败: {e}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_category': {},
            'upload_dir': str(self.upload_dir)
        }
        
        try:
            for subdir in self.upload_dir.iterdir():
                if subdir.is_dir():
                    category_stats = {
                        'files': 0,
                        'size': 0
                    }
                    
                    for file_path in subdir.rglob('*'):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            category_stats['files'] += 1
                            category_stats['size'] += file_size
                            stats['total_files'] += 1
                            stats['total_size'] += file_size
                    
                    stats['by_category'][subdir.name] = category_stats
            
        except Exception as e:
            error_logger.error(f"获取存储统计失败: {e}")
        
        return stats


# 创建全局文件存储服务实例
file_storage_service = FileStorageService()

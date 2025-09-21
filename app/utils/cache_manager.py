"""
缓存管理工具
提供Redis缓存的封装和常用操作
"""
import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import asyncio
import logging
from functools import wraps

from app.core.database import redis_client
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.default_ttl = settings.cache_ttl
        self.prefix = settings.cache_prefix
    
    def _make_key(self, key: str) -> str:
        """构造缓存键名"""
        return f"{self.prefix}{key}"
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize_method: str = "json"
    ) -> bool:
        """设置缓存"""
        try:
            cache_key = self._make_key(key)
            ttl = ttl or self.default_ttl
            
            # 序列化数据
            if serialize_method == "json":
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            elif serialize_method == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置缓存
            result = self.redis_client.get_client().setex(
                cache_key, 
                ttl, 
                serialized_value
            )
            
            logger.debug(f"缓存设置成功: {key}, TTL: {ttl}")
            return result
        
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
            return False
    
    def get(
        self, 
        key: str, 
        default: Any = None,
        deserialize_method: str = "json"
    ) -> Any:
        """获取缓存"""
        try:
            cache_key = self._make_key(key)
            cached_value = self.redis_client.get_client().get(cache_key)
            
            if cached_value is None:
                return default
            
            # 反序列化数据
            if deserialize_method == "json":
                return json.loads(cached_value)
            elif deserialize_method == "pickle":
                return pickle.loads(cached_value)
            else:
                return cached_value.decode('utf-8') if isinstance(cached_value, bytes) else cached_value
        
        except Exception as e:
            logger.error(f"获取缓存失败: {key}, 错误: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_key = self._make_key(key)
            result = self.redis_client.get_client().delete(cache_key)
            logger.debug(f"缓存删除: {key}")
            return bool(result)
        
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            cache_key = self._make_key(key)
            return bool(self.redis_client.get_client().exists(cache_key))
        
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {key}, 错误: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            cache_key = self._make_key(key)
            return bool(self.redis_client.get_client().expire(cache_key, ttl))
        
        except Exception as e:
            logger.error(f"设置缓存过期时间失败: {key}, 错误: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取缓存剩余时间"""
        try:
            cache_key = self._make_key(key)
            return self.redis_client.get_client().ttl(cache_key)
        
        except Exception as e:
            logger.error(f"获取缓存TTL失败: {key}, 错误: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1) -> int:
        """原子性递增"""
        try:
            cache_key = self._make_key(key)
            return self.redis_client.get_client().incrby(cache_key, amount)
        
        except Exception as e:
            logger.error(f"缓存递增失败: {key}, 错误: {e}")
            return 0
    
    def decrement(self, key: str, amount: int = 1) -> int:
        """原子性递减"""
        try:
            cache_key = self._make_key(key)
            return self.redis_client.get_client().decrby(cache_key, amount)
        
        except Exception as e:
            logger.error(f"缓存递减失败: {key}, 错误: {e}")
            return 0
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批量设置缓存"""
        try:
            # 构造键值对
            cache_mapping = {}
            for key, value in mapping.items():
                cache_key = self._make_key(key)
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
                cache_mapping[cache_key] = serialized_value
            
            # 批量设置
            result = self.redis_client.get_client().mset(cache_mapping)
            
            # 如果需要设置TTL
            if ttl:
                pipe = self.redis_client.get_client().pipeline()
                for cache_key in cache_mapping.keys():
                    pipe.expire(cache_key, ttl)
                pipe.execute()
            
            return result
        
        except Exception as e:
            logger.error(f"批量设置缓存失败: 错误: {e}")
            return False
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存"""
        try:
            cache_keys = [self._make_key(key) for key in keys]
            values = self.redis_client.get_client().mget(cache_keys)
            
            result = {}
            for i, key in enumerate(keys):
                value = values[i]
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value.decode('utf-8') if isinstance(value, bytes) else value
                else:
                    result[key] = None
            
            return result
        
        except Exception as e:
            logger.error(f"批量获取缓存失败: 错误: {e}")
            return {}
    
    def clear_pattern(self, pattern: str) -> int:
        """按模式清除缓存"""
        try:
            cache_pattern = self._make_key(pattern)
            keys = self.redis_client.get_client().keys(cache_pattern)
            if keys:
                return self.redis_client.get_client().delete(*keys)
            return 0
        
        except Exception as e:
            logger.error(f"按模式清除缓存失败: {pattern}, 错误: {e}")
            return 0
    
    def get_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        try:
            info = self.redis_client.get_client().info()
            return {
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses")
            }
        
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}


# 全局缓存管理器实例
cache_manager = CacheManager()


def cached(
    ttl: int = None,
    key_prefix: str = "",
    serialize_method: str = "json"
):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 构造缓存键
            func_name = f"{func.__module__}.{func.__name__}"
            args_str = str(args) + str(sorted(kwargs.items()))
            cache_key = f"{key_prefix}{func_name}:{hash(args_str)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(
                cache_key, 
                deserialize_method=serialize_method
            )
            
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(
                cache_key, 
                result, 
                ttl=ttl or settings.cache_ttl,
                serialize_method=serialize_method
            )
            
            logger.debug(f"缓存设置: {cache_key}")
            return result
        
        return wrapper
    return decorator


async def async_cached(
    ttl: int = None,
    key_prefix: str = "",
    serialize_method: str = "json"
):
    """异步缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构造缓存键
            func_name = f"{func.__module__}.{func.__name__}"
            args_str = str(args) + str(sorted(kwargs.items()))
            cache_key = f"{key_prefix}{func_name}:{hash(args_str)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(
                cache_key, 
                deserialize_method=serialize_method
            )
            
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行异步函数并缓存结果
            result = await func(*args, **kwargs)
            cache_manager.set(
                cache_key, 
                result, 
                ttl=ttl or settings.cache_ttl,
                serialize_method=serialize_method
            )
            
            logger.debug(f"缓存设置: {cache_key}")
            return result
        
        return wrapper
    return decorator


class RateLimiter:
    """基于Redis的限流器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cache_manager = cache_manager
    
    def is_allowed(self, identifier: str) -> tuple[bool, Dict[str, Any]]:
        """检查是否允许请求"""
        key = f"rate_limit:{identifier}"
        
        try:
            # 获取当前计数
            current_count = self.cache_manager.get(key, 0, deserialize_method="raw")
            current_count = int(current_count) if current_count else 0
            
            if current_count >= self.max_requests:
                ttl = self.cache_manager.ttl(key)
                return False, {
                    "allowed": False,
                    "current_count": current_count,
                    "max_requests": self.max_requests,
                    "reset_time": ttl,
                    "window_seconds": self.window_seconds
                }
            
            # 递增计数
            new_count = self.cache_manager.increment(key, 1)
            
            # 如果是第一次请求，设置过期时间
            if new_count == 1:
                self.cache_manager.expire(key, self.window_seconds)
            
            ttl = self.cache_manager.ttl(key)
            
            return True, {
                "allowed": True,
                "current_count": new_count,
                "max_requests": self.max_requests,
                "reset_time": ttl,
                "window_seconds": self.window_seconds
            }
        
        except Exception as e:
            logger.error(f"限流检查失败: {e}")
            # 发生错误时允许请求
            return True, {
                "allowed": True,
                "error": str(e)
            }

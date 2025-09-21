"""
数据库操作基类
提供通用的CRUD操作和数据库会话管理
"""
from typing import Type, TypeVar, Generic, List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func
from contextlib import asynccontextmanager
import logging

from app.core.database import SessionLocal, Base

logger = logging.getLogger(__name__)

# 定义泛型类型
ModelType = TypeVar("ModelType", bound=Base)


class DatabaseBase(Generic[ModelType]):
    """数据库操作基类"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()
    
    @asynccontextmanager
    async def get_async_session(self):
        """异步获取数据库会话"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def create(self, obj_in: Dict[str, Any], session: Optional[Session] = None) -> ModelType:
        """创建对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            db_obj = self.model(**obj_in)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"创建对象失败: {e}")
            raise
        finally:
            if should_close:
                session.close()
    
    def get(self, id: Union[str, int], session: Optional[Session] = None) -> Optional[ModelType]:
        """根据ID获取对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            return session.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"查询对象失败: {e}")
            return None
        finally:
            if should_close:
                session.close()
    
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc_order: bool = False,
        session: Optional[Session] = None
    ) -> List[ModelType]:
        """获取多个对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            query = session.query(self.model)
            
            # 应用过滤条件
            if filters:
                filter_conditions = []
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        attr = getattr(self.model, field)
                        if isinstance(value, list):
                            filter_conditions.append(attr.in_(value))
                        elif isinstance(value, dict):
                            # 支持范围查询: {"gte": 10, "lte": 20}
                            if "gte" in value:
                                filter_conditions.append(attr >= value["gte"])
                            if "lte" in value:
                                filter_conditions.append(attr <= value["lte"])
                            if "gt" in value:
                                filter_conditions.append(attr > value["gt"])
                            if "lt" in value:
                                filter_conditions.append(attr < value["lt"])
                            if "like" in value:
                                filter_conditions.append(attr.like(f"%{value['like']}%"))
                        else:
                            filter_conditions.append(attr == value)
                
                if filter_conditions:
                    query = query.filter(and_(*filter_conditions))
            
            # 应用排序
            if order_by and hasattr(self.model, order_by):
                attr = getattr(self.model, order_by)
                if desc_order:
                    query = query.order_by(desc(attr))
                else:
                    query = query.order_by(asc(attr))
            
            # 应用分页
            return query.offset(skip).limit(limit).all()
        
        except SQLAlchemyError as e:
            logger.error(f"查询多个对象失败: {e}")
            return []
        finally:
            if should_close:
                session.close()
    
    def update(
        self, 
        id: Union[str, int], 
        obj_in: Dict[str, Any], 
        session: Optional[Session] = None
    ) -> Optional[ModelType]:
        """更新对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            if not db_obj:
                return None
            
            # 更新字段
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            session.commit()
            session.refresh(db_obj)
            return db_obj
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新对象失败: {e}")
            raise
        finally:
            if should_close:
                session.close()
    
    def delete(self, id: Union[str, int], session: Optional[Session] = None) -> bool:
        """删除对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            if not db_obj:
                return False
            
            session.delete(db_obj)
            session.commit()
            return True
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"删除对象失败: {e}")
            raise
        finally:
            if should_close:
                session.close()
    
    def count(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        session: Optional[Session] = None
    ) -> int:
        """统计对象数量"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            query = session.query(func.count(self.model.id))
            
            # 应用过滤条件
            if filters:
                filter_conditions = []
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        attr = getattr(self.model, field)
                        if isinstance(value, list):
                            filter_conditions.append(attr.in_(value))
                        else:
                            filter_conditions.append(attr == value)
                
                if filter_conditions:
                    query = query.filter(and_(*filter_conditions))
            
            return query.scalar() or 0
        
        except SQLAlchemyError as e:
            logger.error(f"统计对象数量失败: {e}")
            return 0
        finally:
            if should_close:
                session.close()
    
    def exists(
        self, 
        filters: Dict[str, Any], 
        session: Optional[Session] = None
    ) -> bool:
        """检查对象是否存在"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            query = session.query(self.model)
            
            # 应用过滤条件
            filter_conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    attr = getattr(self.model, field)
                    filter_conditions.append(attr == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
            
            return query.first() is not None
        
        except SQLAlchemyError as e:
            logger.error(f"检查对象存在性失败: {e}")
            return False
        finally:
            if should_close:
                session.close()
    
    def bulk_create(
        self, 
        objects: List[Dict[str, Any]], 
        session: Optional[Session] = None
    ) -> List[ModelType]:
        """批量创建对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            db_objects = [self.model(**obj_data) for obj_data in objects]
            session.add_all(db_objects)
            session.commit()
            
            # 刷新对象以获取ID
            for obj in db_objects:
                session.refresh(obj)
            
            return db_objects
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"批量创建对象失败: {e}")
            raise
        finally:
            if should_close:
                session.close()
    
    def bulk_update(
        self, 
        updates: List[Dict[str, Any]], 
        session: Optional[Session] = None
    ) -> bool:
        """批量更新对象"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            for update_data in updates:
                if "id" not in update_data:
                    continue
                
                obj_id = update_data.pop("id")
                session.query(self.model).filter(
                    self.model.id == obj_id
                ).update(update_data)
            
            session.commit()
            return True
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"批量更新对象失败: {e}")
            raise
        finally:
            if should_close:
                session.close()
    
    def search(
        self, 
        search_term: str, 
        search_fields: List[str], 
        skip: int = 0, 
        limit: int = 100,
        session: Optional[Session] = None
    ) -> List[ModelType]:
        """全文搜索"""
        should_close = session is None
        if session is None:
            session = self.get_session()
        
        try:
            query = session.query(self.model)
            
            # 构建搜索条件
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    attr = getattr(self.model, field)
                    search_conditions.append(attr.like(f"%{search_term}%"))
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
            
            return query.offset(skip).limit(limit).all()
        
        except SQLAlchemyError as e:
            logger.error(f"搜索对象失败: {e}")
            return []
        finally:
            if should_close:
                session.close()


class TransactionManager:
    """事务管理器"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.error(f"事务回滚: {exc_val}")
        else:
            self.session.commit()
        self.session.close()


def get_db_session():
    """获取数据库会话 - 依赖注入使用"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

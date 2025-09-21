"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import redis
from py2neo import Graph
# from motor.motor_asyncio import AsyncIOMotorClient  # 临时注释，等待兼容性修复
import asyncio

from app.core.config import get_settings

settings = get_settings()

# PostgreSQL 数据库配置
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Base
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis 连接
class RedisClient:
    """Redis客户端"""
    
    def __init__(self):
        self.redis_client = None
    
    def get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return self.redis_client
    
    def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            self.redis_client.close()


# Neo4j 图数据库连接
class Neo4jClient:
    """Neo4j客户端"""
    
    def __init__(self):
        self.graph = None
    
    def get_graph(self) -> Graph:
        """获取Neo4j图数据库连接"""
        if self.graph is None:
            self.graph = Graph(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return self.graph
    
    def close(self):
        """关闭Neo4j连接"""
        if self.graph:
            self.graph = None


# MongoDB 异步客户端 - 临时禁用，等待Motor兼容性修复
class MongoClient:
    """MongoDB异步客户端"""
    
    def __init__(self):
        self.client = None
        self.database = None
    
    async def get_database(self):
        """获取MongoDB数据库"""
        # 临时返回None，等待Motor兼容性修复
        print("⚠️  MongoDB暂时禁用，等待Motor兼容性修复")
        return None
    
    async def close(self):
        """关闭MongoDB连接"""
        print("⚠️  MongoDB连接关闭（暂时禁用）")


# 全局客户端实例
redis_client = RedisClient()
neo4j_client = Neo4jClient()
mongo_client = MongoClient()


def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    return redis_client.get_client()


def get_neo4j() -> Graph:
    """获取Neo4j图数据库连接"""
    return neo4j_client.get_graph()


async def get_mongodb():
    """获取MongoDB数据库"""
    return await mongo_client.get_database()


async def init_databases():
    """初始化所有数据库连接"""
    print("🚀 数据库初始化开始...")
    
    # 暂时跳过PostgreSQL初始化
    try:
        # Base.metadata.create_all(bind=engine)  # 临时注释
        print("⚠️  PostgreSQL初始化暂时跳过")
    except Exception as e:
        print(f"❌ PostgreSQL初始化失败: {e}")
    
    # 测试Redis连接
    try:
        redis_client.get_client().ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
    
    # 测试Neo4j连接
    try:
        neo4j_client.get_graph().run("RETURN 1")
        print("✅ Neo4j connection successful")
    except Exception as e:
        print(f"⚠️  Neo4j connection failed: {e}")
    
    # 测试MongoDB连接 - 临时跳过
    try:
        db = await mongo_client.get_database()
        if db:
            print("✅ MongoDB connection successful")
        else:
            print("⚠️  MongoDB暂时禁用")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
    
    print("✅ 数据库初始化完成（部分组件暂时禁用）")


async def close_databases():
    """关闭所有数据库连接"""
    redis_client.close()
    neo4j_client.close()
    await mongo_client.close()
    print("✅ All database connections closed")

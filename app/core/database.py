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
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

from app.core.config import get_settings

settings = get_settings()

# SQLite 数据库配置 (开发阶段)
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=settings.debug,
    # SQLite特定配置
    connect_args={"check_same_thread": False}
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


# MongoDB 异步客户端
class MongoClient:
    """MongoDB异步客户端"""
    
    def __init__(self):
        self.client = None
        self.database = None
    
    async def get_database(self):
        """获取MongoDB数据库"""
        if self.client is None:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_db_name]
        return self.database
    
    async def close(self):
        """关闭MongoDB连接"""
        if self.client:
            self.client.close()


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
    
    # 创建SQLite数据库表
    try:
        # 导入所有模型以确保表被创建
        from app.models import Document, User, AuditTask, AuditResult, Rule, RuleCategory
        
        Base.metadata.create_all(bind=engine)
        print("✅ SQLite数据库表创建成功")
    except Exception as e:
        print(f"❌ SQLite数据库初始化失败: {e}")
        raise e  # 主数据库失败则终止启动
    
    # 测试Redis连接（开发环境可选）
    try:
        redis_client.get_client().ping()
        print("✅ Redis连接成功")
    except Exception as e:
        print(f"⚠️  Redis连接失败（开发环境可继续）: {e}")
    
    # Neo4j连接（开发环境暂时跳过）
    try:
        if settings.enable_neo4j:
            neo4j_client.get_graph().run("RETURN 1")
            print("✅ Neo4j连接成功")
        else:
            print("⚠️  Neo4j暂时禁用（等待服务安装）")
    except Exception as e:
        print(f"⚠️  Neo4j连接失败（开发环境跳过）: {e}")
    
    # MongoDB连接（开发环境暂时跳过）
    try:
        if settings.enable_mongodb:
            db = await mongo_client.get_database()
            await db.list_collection_names()
            print("✅ MongoDB连接成功")
        else:
            print("⚠️  MongoDB暂时禁用（等待服务安装）")
    except Exception as e:
        print(f"⚠️  MongoDB连接失败（开发环境跳过）: {e}")
    
    print("✅ 数据库初始化完成")


async def close_databases():
    """关闭所有数据库连接"""
    try:
        redis_client.close()
        print("✅ Redis连接已关闭")
    except Exception as e:
        print(f"⚠️  Redis关闭异常: {e}")
    
    try:
        neo4j_client.close()
        print("✅ Neo4j连接已关闭")
    except Exception as e:
        print(f"⚠️  Neo4j关闭异常: {e}")
    
    try:
        await mongo_client.close()
        print("✅ MongoDB连接已关闭")
    except Exception as e:
        print(f"⚠️  MongoDB关闭异常: {e}")
    
    print("✅ 所有数据库连接已关闭")

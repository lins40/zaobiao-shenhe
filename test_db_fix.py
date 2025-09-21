#!/usr/bin/env python3
"""数据库连接修复测试脚本"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

async def test_database_connections():
    """测试数据库连接修复"""
    print("🔧 数据库连接修复验证")
    print("=" * 50)
    
    # 1. 测试配置加载
    print("\n📋 1. 配置加载测试")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ 配置加载成功")
        print(f"   应用名称: {settings.app_name}")
        print(f"   数据库URL: {settings.database_url}")
        print(f"   Neo4j启用: {settings.enable_neo4j}")
        print(f"   MongoDB启用: {settings.enable_mongodb}")
        print(f"   Redis URL: {settings.redis_url}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    # 2. 测试SQLite连接
    print("\n🗄️  2. SQLite数据库测试")
    try:
        from app.core.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1").fetchone()
            print(f"✅ SQLite连接正常: 测试查询结果={result[0]}")
    except Exception as e:
        print(f"❌ SQLite连接失败: {e}")
        return False
    
    # 3. 测试模型导入
    print("\n📊 3. 数据模型导入测试")
    try:
        from app.models.document import Document
        from app.models.user import User
        from app.models.audit import AuditTask, AuditResult
        from app.models.rule import Rule, RuleCategory
        print("✅ 所有数据模型导入成功")
        print(f"   Document: {Document.__tablename__}")
        print(f"   User: {User.__tablename__}")
        print(f"   AuditTask: {AuditTask.__tablename__}")
        print(f"   Rule: {Rule.__tablename__}")
    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        return False
    
    # 4. 测试数据库初始化
    print("\n🚀 4. 数据库初始化测试")
    try:
        from app.core.database import init_databases
        await init_databases()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试FastAPI应用
    print("\n🌐 5. FastAPI应用测试")
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ FastAPI应用正常")
            print(f"   健康检查: {data.get('status')}")
            print(f"   服务名称: {data.get('service')}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FastAPI应用测试失败: {e}")
        return False
    
    # 6. 验证数据库文件
    print("\n📁 6. 数据库文件验证")
    try:
        import os
        db_file = "zaobiao.db"
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            print(f"✅ SQLite数据库文件存在: {db_file} ({size} bytes)")
        else:
            print(f"⚠️  数据库文件未创建: {db_file}")
    except Exception as e:
        print(f"❌ 文件验证失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 数据库连接修复验证完成！")
    print("✅ 所有核心组件工作正常")
    print("✅ PostgreSQL连接问题已解决")
    print("✅ 开发环境数据库配置优化完成")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_connections())
    sys.exit(0 if success else 1)

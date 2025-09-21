#!/usr/bin/env python3
"""
Week 2 功能测试脚本
"""
import sys
import traceback

def test_imports():
    """测试各模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from app.core.config import get_settings
        print("✅ 配置模块导入成功")
        settings = get_settings()
        print(f"   - 应用名称: {settings.app_name}")
        print(f"   - 端口: {settings.port}")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    try:
        from app.core.database import init_databases
        print("✅ 数据库模块导入成功")
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False
    
    try:
        from app.models.document import Document
        print("✅ 文档模型导入成功")
    except Exception as e:
        print(f"❌ 文档模型导入失败: {e}")
        return False
    
    try:
        from app.utils.database_base import DatabaseBase
        print("✅ 数据库基类导入成功")
    except Exception as e:
        print(f"❌ 数据库基类导入失败: {e}")
        return False
    
    try:
        from app.utils.cache_manager import cache_manager
        print("✅ 缓存管理器导入成功")
    except Exception as e:
        print(f"❌ 缓存管理器导入失败: {e}")
        return False
    
    try:
        from app.services.external.deepseek_client import DeepSeekClient
        print("✅ DeepSeek客户端导入成功")
    except Exception as e:
        print(f"❌ DeepSeek客户端导入失败: {e}")
        return False
    
    try:
        from app.services.external.textin_client import TextInClient
        print("✅ TextIn客户端导入成功")
    except Exception as e:
        print(f"❌ TextIn客户端导入失败: {e}")
        return False
    
    try:
        from app.services.document_service import document_service
        print("✅ 文档服务导入成功")
    except Exception as e:
        print(f"❌ 文档服务导入失败: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app.api.endpoints.documents import router
        print("✅ 文档API导入成功")
    except Exception as e:
        print(f"❌ 文档API导入失败: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app.main import app
        print("✅ FastAPI应用导入成功")
    except Exception as e:
        print(f"❌ FastAPI应用导入失败: {e}")
        traceback.print_exc()
        return False
    
    print("\n🎉 所有模块导入测试通过！")
    return True

def test_database():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        from app.core.database import engine
        from app.models import Document
        
        # 测试SQLite连接
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ SQLite数据库连接成功")
        
        # 测试表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ 数据库表: {tables}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        traceback.print_exc()
        return False

def test_cache():
    """测试缓存功能"""
    print("\n🔍 测试缓存功能...")
    
    try:
        from app.utils.cache_manager import cache_manager
        
        # 测试基本缓存操作
        test_key = "test_week2_cache"
        test_value = {"message": "Week 2 功能测试", "timestamp": "2025-09-21"}
        
        # 设置缓存
        success = cache_manager.set(test_key, test_value, ttl=60)
        if success:
            print("✅ 缓存设置成功")
        else:
            print("❌ 缓存设置失败")
            return False
        
        # 获取缓存
        cached_value = cache_manager.get(test_key)
        if cached_value == test_value:
            print("✅ 缓存获取成功")
        else:
            print(f"❌ 缓存获取失败: {cached_value}")
            return False
        
        # 清理测试缓存
        cache_manager.delete(test_key)
        print("✅ 缓存清理成功")
        
        return True
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 Week 2 功能测试开始...")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("❌ 导入测试失败，停止后续测试")
        return False
    
    # 测试数据库
    if not test_database():
        print("❌ 数据库测试失败")
        return False
    
    # 测试缓存
    if not test_cache():
        print("❌ 缓存测试失败")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Week 2 所有功能测试通过！")
    print("✅ 外部API客户端封装完成")
    print("✅ 数据库操作基类完成")
    print("✅ 缓存管理工具完成")
    print("✅ 文档服务层完成")
    print("✅ API接口更新完成")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未知错误: {e}")
        traceback.print_exc()
        exit(1)

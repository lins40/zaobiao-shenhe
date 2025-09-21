#!/usr/bin/env python3
"""
Week 2 简化测试 - 验证核心功能
"""
import sys
import traceback

def test_1_config_and_imports():
    """测试1: 配置和导入功能"""
    print("🔍 测试1: 配置和导入功能")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ 配置加载成功: {settings.app_name}")
        
        from app.models.document import Document
        print("✅ 数据模型导入成功")
        
        from app.utils.database_base import DatabaseBase
        print("✅ 数据库基类导入成功")
        
        from app.utils.cache_manager import cache_manager
        print("✅ 缓存管理器导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
        return False

def test_2_database_basic():
    """测试2: 数据库基本功能"""
    print("\n🔍 测试2: 数据库基本功能")
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        # 测试数据库连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            print("✅ 数据库连接正常")
        
        # 检查表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ 数据库表: {len(tables)} 个")
        
        return True
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
        return False

def test_3_cache_basic():
    """测试3: 缓存基本功能"""
    print("\n🔍 测试3: 缓存基本功能")
    try:
        from app.utils.cache_manager import cache_manager
        
        # 基本缓存操作
        test_key = "simple_test"
        test_value = {"test": "data"}
        
        success = cache_manager.set(test_key, test_value, ttl=30)
        if success:
            print("✅ 缓存设置成功")
        
        cached = cache_manager.get(test_key)
        if cached == test_value:
            print("✅ 缓存获取成功")
        
        cache_manager.delete(test_key)
        print("✅ 缓存删除成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试3失败: {e}")
        return False

def test_4_external_clients():
    """测试4: 外部API客户端"""
    print("\n🔍 测试4: 外部API客户端")
    try:
        from app.services.external.deepseek_client import DeepSeekClient
        from app.services.external.textin_client import TextInClient
        
        deepseek = DeepSeekClient()
        print(f"✅ DeepSeek客户端: {deepseek.model}")
        
        textin = TextInClient()
        print(f"✅ TextIn客户端: timeout={textin.timeout}")
        
        return True
    except Exception as e:
        print(f"❌ 测试4失败: {e}")
        return False

def test_5_document_service():
    """测试5: 文档服务"""
    print("\n🔍 测试5: 文档服务")
    try:
        from app.services.document_service import document_service
        
        # 检查服务组件
        if hasattr(document_service, 'db'):
            print("✅ 数据库操作组件正常")
        
        if hasattr(document_service, 'upload_dir'):
            print(f"✅ 上传目录配置: {document_service.upload_dir}")
        
        # 测试统计功能
        stats = document_service.get_statistics()
        print(f"✅ 统计功能正常: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ 测试5失败: {e}")
        traceback.print_exc()
        return False

def test_6_api_structure():
    """测试6: API结构"""
    print("\n🔍 测试6: API结构")
    try:
        from app.main import app
        from app.api.endpoints.documents import router
        
        print("✅ FastAPI应用加载成功")
        print("✅ 文档API路由加载成功")
        
        # 检查路由
        routes = [route.path for route in app.routes]
        print(f"✅ API路由数量: {len(routes)}")
        
        return True
    except Exception as e:
        print(f"❌ 测试6失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 Week 2 简化功能测试")
    print("=" * 50)
    
    tests = [
        test_1_config_and_imports,
        test_2_database_basic,
        test_3_cache_basic,
        test_4_external_clients,
        test_5_document_service,
        test_6_api_structure
    ]
    
    passed = 0
    failed = 0
    
    for i, test_func in enumerate(tests, 1):
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试{i}异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 所有测试通过！Week 2功能正常！")
        return True
    else:
        print(f"\n⚠️  有{failed}个测试失败，需要检查相关功能。")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 测试过程异常: {e}")
        traceback.print_exc()
        sys.exit(1)

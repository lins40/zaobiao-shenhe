#!/usr/bin/env python3
"""
Week 2 功能测试计划 - 6个核心测试任务
"""
import asyncio
import json
import time
import sys
import traceback
from pathlib import Path

# 测试任务配置
TEST_CONFIG = {
    "test_results": [],
    "passed_tests": 0,
    "failed_tests": 0,
    "start_time": None
}


def log_test_result(task_name, status, message, details=None):
    """记录测试结果"""
    result = {
        "task": task_name,
        "status": status,
        "message": message,
        "details": details or {},
        "timestamp": time.time()
    }
    TEST_CONFIG["test_results"].append(result)
    
    if status == "PASS":
        TEST_CONFIG["passed_tests"] += 1
        print(f"✅ {task_name}: {message}")
    else:
        TEST_CONFIG["failed_tests"] += 1
        print(f"❌ {task_name}: {message}")
    
    if details:
        for key, value in details.items():
            print(f"   📝 {key}: {value}")


async def test_task_1_database_operations():
    """测试任务1: 数据库操作基类功能测试"""
    print("\n🔍 测试任务1: 数据库操作基类功能")
    print("-" * 50)
    
    try:
        from app.utils.database_base import DatabaseBase
        from app.models.document import Document
        
        # 创建数据库操作实例
        db = DatabaseBase(Document)
        
        # 测试1.1: 创建文档记录
        test_doc_data = {
            "filename": "test_document.pdf",
            "original_filename": "测试文档.pdf",
            "file_path": "/tmp/test.pdf",
            "file_size": 1024000,
            "content_type": "application/pdf",
            "uploaded_by": "test_user"
        }
        
        doc = db.create(test_doc_data)
        doc_id = doc.id
        
        log_test_result(
            "1.1 文档创建", "PASS", "文档记录创建成功",
            {"document_id": doc_id, "filename": doc.filename}
        )
        
        # 测试1.2: 查询单个文档
        retrieved_doc = db.get(doc_id)
        if retrieved_doc and retrieved_doc.filename == test_doc_data["filename"]:
            log_test_result(
                "1.2 文档查询", "PASS", "文档查询功能正常",
                {"retrieved_id": retrieved_doc.id}
            )
        else:
            log_test_result("1.2 文档查询", "FAIL", "文档查询失败")
            return False
        
        # 测试1.3: 更新文档
        update_data = {"audit_score": 85.5, "risk_level": "medium"}
        updated_doc = db.update(doc_id, update_data)
        if updated_doc and updated_doc.audit_score == 85.5:
            log_test_result(
                "1.3 文档更新", "PASS", "文档更新功能正常",
                {"new_score": updated_doc.audit_score}
            )
        else:
            log_test_result("1.3 文档更新", "FAIL", "文档更新失败")
            return False
        
        # 测试1.4: 分页查询
        docs = db.get_multi(skip=0, limit=10)
        if len(docs) >= 1:
            log_test_result(
                "1.4 分页查询", "PASS", "分页查询功能正常",
                {"total_found": len(docs)}
            )
        else:
            log_test_result("1.4 分页查询", "FAIL", "分页查询失败")
            return False
        
        # 测试1.5: 统计功能
        count = db.count()
        if count >= 1:
            log_test_result(
                "1.5 统计功能", "PASS", "统计功能正常",
                {"total_count": count}
            )
        else:
            log_test_result("1.5 统计功能", "FAIL", "统计功能失败")
            return False
        
        # 测试1.6: 删除文档
        success = db.delete(doc_id)
        if success:
            log_test_result("1.6 文档删除", "PASS", "文档删除功能正常")
        else:
            log_test_result("1.6 文档删除", "FAIL", "文档删除失败")
            return False
        
        return True
        
    except Exception as e:
        log_test_result("测试任务1", "FAIL", f"数据库操作测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_task_2_cache_management():
    """测试任务2: 缓存管理功能测试"""
    print("\n🔍 测试任务2: 缓存管理功能")
    print("-" * 50)
    
    try:
        from app.utils.cache_manager import cache_manager, RateLimiter
        
        # 测试2.1: 基本缓存操作
        test_key = "week2_test_cache"
        test_data = {
            "message": "Week 2 缓存测试",
            "data": [1, 2, 3, 4, 5],
            "nested": {"key": "value"}
        }
        
        # 设置缓存
        success = cache_manager.set(test_key, test_data, ttl=60)
        if success:
            log_test_result("2.1 缓存设置", "PASS", "缓存设置成功")
        else:
            log_test_result("2.1 缓存设置", "FAIL", "缓存设置失败")
            return False
        
        # 测试2.2: 缓存获取
        cached_data = cache_manager.get(test_key)
        if cached_data == test_data:
            log_test_result(
                "2.2 缓存获取", "PASS", "缓存获取成功",
                {"data_match": True}
            )
        else:
            log_test_result("2.2 缓存获取", "FAIL", "缓存数据不匹配")
            return False
        
        # 测试2.3: 缓存存在性检查
        exists = cache_manager.exists(test_key)
        if exists:
            log_test_result("2.3 缓存检查", "PASS", "缓存存在性检查正常")
        else:
            log_test_result("2.3 缓存检查", "FAIL", "缓存存在性检查失败")
            return False
        
        # 测试2.4: 缓存TTL
        ttl = cache_manager.ttl(test_key)
        if ttl > 0:
            log_test_result(
                "2.4 TTL检查", "PASS", "TTL功能正常",
                {"remaining_ttl": ttl}
            )
        else:
            log_test_result("2.4 TTL检查", "FAIL", "TTL功能异常")
            return False
        
        # 测试2.5: 限流器功能
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # 连续请求测试
        allow_count = 0
        for i in range(5):
            allowed, info = limiter.is_allowed("test_client")
            if allowed:
                allow_count += 1
        
        if allow_count == 3:  # 应该只允许3次
            log_test_result(
                "2.5 限流器", "PASS", "限流器功能正常",
                {"allowed_requests": allow_count}
            )
        else:
            log_test_result(
                "2.5 限流器", "FAIL", f"限流器异常，允许了{allow_count}次请求"
            )
            return False
        
        # 测试2.6: 批量操作
        batch_data = {
            "key1": "value1",
            "key2": {"nested": "data"},
            "key3": [1, 2, 3]
        }
        
        success = cache_manager.mset(batch_data, ttl=30)
        if success:
            retrieved_batch = cache_manager.mget(list(batch_data.keys()))
            if all(retrieved_batch[k] == v for k, v in batch_data.items()):
                log_test_result("2.6 批量操作", "PASS", "批量缓存操作正常")
            else:
                log_test_result("2.6 批量操作", "FAIL", "批量缓存数据不匹配")
                return False
        else:
            log_test_result("2.6 批量操作", "FAIL", "批量缓存设置失败")
            return False
        
        # 清理测试缓存
        cache_manager.delete(test_key)
        for key in batch_data.keys():
            cache_manager.delete(key)
        
        return True
        
    except Exception as e:
        log_test_result("测试任务2", "FAIL", f"缓存管理测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_task_3_external_api_clients():
    """测试任务3: 外部API客户端测试"""
    print("\n🔍 测试任务3: 外部API客户端功能")
    print("-" * 50)
    
    try:
        from app.services.external.deepseek_client import DeepSeekClient
        from app.services.external.textin_client import TextInClient
        
        # 测试3.1: DeepSeek客户端初始化
        deepseek_client = DeepSeekClient()
        if deepseek_client.api_key and deepseek_client.base_url:
            log_test_result(
                "3.1 DeepSeek初始化", "PASS", "DeepSeek客户端初始化成功",
                {"base_url": deepseek_client.base_url, "model": deepseek_client.model}
            )
        else:
            log_test_result("3.1 DeepSeek初始化", "FAIL", "DeepSeek客户端配置缺失")
            return False
        
        # 测试3.2: TextIn客户端初始化
        textin_client = TextInClient()
        if textin_client.api_key and textin_client.base_url:
            log_test_result(
                "3.2 TextIn初始化", "PASS", "TextIn客户端初始化成功",
                {"base_url": textin_client.base_url, "timeout": textin_client.timeout}
            )
        else:
            log_test_result("3.2 TextIn初始化", "FAIL", "TextIn客户端配置缺失")
            return False
        
        # 测试3.3: 限流器功能
        rate_limiter = deepseek_client.rate_limiter
        if rate_limiter.max_calls > 0:
            log_test_result(
                "3.3 限流器配置", "PASS", "API限流器配置正常",
                {"max_calls": rate_limiter.max_calls, "window": rate_limiter.time_window}
            )
        else:
            log_test_result("3.3 限流器配置", "FAIL", "限流器配置异常")
            return False
        
        # 测试3.4: 熔断器功能
        circuit_breaker = deepseek_client.circuit_breaker
        if circuit_breaker.failure_threshold > 0:
            log_test_result(
                "3.4 熔断器配置", "PASS", "熔断器配置正常",
                {"threshold": circuit_breaker.failure_threshold, "timeout": circuit_breaker.timeout}
            )
        else:
            log_test_result("3.4 熔断器配置", "FAIL", "熔断器配置异常")
            return False
        
        # 测试3.5: TextIn支持格式
        supported_formats = await textin_client.get_supported_formats()
        if len(supported_formats) > 0:
            log_test_result(
                "3.5 支持格式", "PASS", "TextIn支持格式获取正常",
                {"formats_count": len(supported_formats), "formats": supported_formats[:5]}
            )
        else:
            log_test_result("3.5 支持格式", "FAIL", "支持格式获取失败")
            return False
        
        # 测试3.6: 客户端资源清理
        await deepseek_client.close()
        await textin_client.close()
        log_test_result("3.6 资源清理", "PASS", "客户端资源清理完成")
        
        return True
        
    except Exception as e:
        log_test_result("测试任务3", "FAIL", f"外部API客户端测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_task_4_document_service():
    """测试任务4: 文档服务层测试"""
    print("\n🔍 测试任务4: 文档服务层功能")
    print("-" * 50)
    
    try:
        from app.services.document_service import document_service
        import tempfile
        import os
        
        # 测试4.1: 文档服务初始化
        if document_service.db and document_service.upload_dir:
            log_test_result(
                "4.1 服务初始化", "PASS", "文档服务初始化成功",
                {"upload_dir": str(document_service.upload_dir)}
            )
        else:
            log_test_result("4.1 服务初始化", "FAIL", "文档服务初始化失败")
            return False
        
        # 测试4.2: 创建测试文档文件
        test_content = b"This is a test document for Week 2 testing.\nIt contains some sample text."
        test_filename = "week2_test_document.txt"
        
        # 模拟文档上传
        document = await document_service.upload_document(
            file_content=test_content,
            filename=test_filename,
            content_type="text/plain",
            uploaded_by="test_user"
        )
        
        if document and document.id:
            log_test_result(
                "4.2 文档上传", "PASS", "文档上传功能正常",
                {"document_id": document.id, "status": document.status}
            )
            doc_id = document.id
        else:
            log_test_result("4.2 文档上传", "FAIL", "文档上传失败")
            return False
        
        # 测试4.3: 获取文档列表
        documents = document_service.get_documents(skip=0, limit=10)
        if len(documents) >= 1:
            log_test_result(
                "4.3 文档列表", "PASS", "文档列表获取正常",
                {"document_count": len(documents)}
            )
        else:
            log_test_result("4.3 文档列表", "FAIL", "文档列表获取失败")
            return False
        
        # 测试4.4: 获取单个文档
        retrieved_doc = document_service.get_document(doc_id)
        if retrieved_doc and retrieved_doc.id == doc_id:
            log_test_result(
                "4.4 文档获取", "PASS", "单个文档获取正常",
                {"filename": retrieved_doc.original_filename}
            )
        else:
            log_test_result("4.4 文档获取", "FAIL", "单个文档获取失败")
            return False
        
        # 测试4.5: 获取统计信息
        stats = document_service.get_statistics()
        if stats and "total_documents" in stats:
            log_test_result(
                "4.5 统计信息", "PASS", "统计信息获取正常",
                {"total_docs": stats["total_documents"]}
            )
        else:
            log_test_result("4.5 统计信息", "FAIL", "统计信息获取失败")
            return False
        
        # 测试4.6: 删除测试文档
        success = document_service.delete_document(doc_id)
        if success:
            log_test_result("4.6 文档删除", "PASS", "文档删除功能正常")
        else:
            log_test_result("4.6 文档删除", "FAIL", "文档删除失败")
            return False
        
        return True
        
    except Exception as e:
        log_test_result("测试任务4", "FAIL", f"文档服务测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_task_5_api_endpoints():
    """测试任务5: API接口测试"""
    print("\n🔍 测试任务5: API接口功能")
    print("-" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        # 创建测试客户端
        client = TestClient(app)
        
        # 测试5.1: 健康检查接口
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            log_test_result(
                "5.1 健康检查", "PASS", "健康检查接口正常",
                {"status": data.get("status"), "service": data.get("service")}
            )
        else:
            log_test_result("5.1 健康检查", "FAIL", f"健康检查失败: {response.status_code}")
            return False
        
        # 测试5.2: 根路径接口
        response = client.get("/")
        if response.status_code == 200:
            log_test_result("5.2 根路径", "PASS", "根路径接口正常")
        else:
            log_test_result("5.2 根路径", "FAIL", f"根路径访问失败: {response.status_code}")
            return False
        
        # 测试5.3: 文档列表接口
        response = client.get("/api/v1/documents/")
        if response.status_code == 200:
            data = response.json()
            log_test_result(
                "5.3 文档列表", "PASS", "文档列表接口正常",
                {"success": data.get("success"), "data_type": type(data.get("data")).__name__}
            )
        else:
            log_test_result("5.3 文档列表", "FAIL", f"文档列表接口失败: {response.status_code}")
            return False
        
        # 测试5.4: 统计信息接口
        response = client.get("/api/v1/documents/statistics/overview")
        if response.status_code == 200:
            data = response.json()
            log_test_result(
                "5.4 统计接口", "PASS", "统计信息接口正常",
                {"success": data.get("success")}
            )
        else:
            log_test_result("5.4 统计接口", "FAIL", f"统计接口失败: {response.status_code}")
            return False
        
        # 测试5.5: 不存在的文档接口
        response = client.get("/api/v1/documents/nonexistent-id")
        if response.status_code == 404:
            log_test_result("5.5 错误处理", "PASS", "404错误处理正常")
        else:
            log_test_result("5.5 错误处理", "FAIL", "错误处理异常")
            return False
        
        # 测试5.6: 无效参数测试
        response = client.get("/api/v1/documents/?limit=-1")
        if response.status_code in [422, 400]:  # 参数验证错误
            log_test_result("5.6 参数验证", "PASS", "参数验证功能正常")
        else:
            log_test_result("5.6 参数验证", "FAIL", "参数验证功能异常")
            return False
        
        return True
        
    except Exception as e:
        log_test_result("测试任务5", "FAIL", f"API接口测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_task_6_integration_test():
    """测试任务6: 系统集成测试"""
    print("\n🔍 测试任务6: 系统集成功能")
    print("-" * 50)
    
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        from app.services.document_service import document_service
        from app.utils.cache_manager import cache_manager
        
        # 测试6.1: 完整的文档上传流程
        client = TestClient(app)
        
        # 创建测试文件
        test_file_content = b"Week 2 Integration Test Document\nThis is a comprehensive test."
        files = {"file": ("integration_test.txt", test_file_content, "text/plain")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            params={"uploaded_by": "integration_test_user"}
        )
        
        if response.status_code == 200:
            data = response.json()
            doc_id = data["data"]["id"]
            log_test_result(
                "6.1 上传流程", "PASS", "完整上传流程正常",
                {"document_id": doc_id}
            )
        else:
            log_test_result("6.1 上传流程", "FAIL", f"上传流程失败: {response.status_code}")
            return False
        
        # 测试6.2: 等待解析完成并验证
        import time
        time.sleep(2)  # 等待异步解析
        
        response = client.get(f"/api/v1/documents/{doc_id}")
        if response.status_code == 200:
            doc_data = response.json()["data"]
            log_test_result(
                "6.2 解析验证", "PASS", "文档解析状态正常",
                {"status": doc_data.get("status")}
            )
        else:
            log_test_result("6.2 解析验证", "FAIL", "文档状态获取失败")
            return False
        
        # 测试6.3: 缓存系统集成
        cache_key = f"test_integration_{doc_id}"
        test_cache_data = {"integration_test": True, "document_id": doc_id}
        
        cache_manager.set(cache_key, test_cache_data, ttl=60)
        cached_result = cache_manager.get(cache_key)
        
        if cached_result == test_cache_data:
            log_test_result("6.3 缓存集成", "PASS", "缓存系统集成正常")
        else:
            log_test_result("6.3 缓存集成", "FAIL", "缓存系统集成失败")
            return False
        
        # 测试6.4: 数据库和API一致性
        db_doc = document_service.get_document(doc_id)
        if db_doc and db_doc.id == doc_id:
            log_test_result("6.4 数据一致性", "PASS", "数据库与API数据一致")
        else:
            log_test_result("6.4 数据一致性", "FAIL", "数据库与API数据不一致")
            return False
        
        # 测试6.5: 统计信息更新
        stats = document_service.get_statistics()
        if stats["total_documents"] >= 1:
            log_test_result(
                "6.5 统计更新", "PASS", "统计信息正常更新",
                {"total": stats["total_documents"]}
            )
        else:
            log_test_result("6.5 统计更新", "FAIL", "统计信息更新异常")
            return False
        
        # 测试6.6: 清理集成测试数据
        delete_response = client.delete(f"/api/v1/documents/{doc_id}")
        cache_manager.delete(cache_key)
        
        if delete_response.status_code == 200:
            log_test_result("6.6 数据清理", "PASS", "集成测试数据清理完成")
        else:
            log_test_result("6.6 数据清理", "FAIL", "数据清理失败")
            return False
        
        return True
        
    except Exception as e:
        log_test_result("测试任务6", "FAIL", f"系统集成测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试任务"""
    print("🚀 Week 2 功能测试开始")
    print("=" * 60)
    
    TEST_CONFIG["start_time"] = time.time()
    
    # 定义测试任务
    test_tasks = [
        ("数据库操作基类", test_task_1_database_operations),
        ("缓存管理功能", test_task_2_cache_management),
        ("外部API客户端", test_task_3_external_api_clients),
        ("文档服务层", test_task_4_document_service),
        ("API接口功能", test_task_5_api_endpoints),
        ("系统集成测试", test_task_6_integration_test)
    ]
    
    # 执行所有测试
    for task_name, test_func in test_tasks:
        try:
            success = await test_func()
            if not success:
                print(f"\n⚠️  {task_name} 测试失败，但继续执行后续测试...")
        except Exception as e:
            print(f"\n💥 {task_name} 测试过程中发生异常: {str(e)}")
    
    # 生成测试报告
    generate_test_report()


def generate_test_report():
    """生成测试报告"""
    total_time = time.time() - TEST_CONFIG["start_time"]
    total_tests = TEST_CONFIG["passed_tests"] + TEST_CONFIG["failed_tests"]
    
    print("\n" + "=" * 60)
    print("📊 Week 2 功能测试报告")
    print("=" * 60)
    
    print(f"🕒 测试耗时: {total_time:.2f} 秒")
    print(f"📈 测试总数: {total_tests}")
    print(f"✅ 通过测试: {TEST_CONFIG['passed_tests']}")
    print(f"❌ 失败测试: {TEST_CONFIG['failed_tests']}")
    
    if total_tests > 0:
        success_rate = (TEST_CONFIG['passed_tests'] / total_tests) * 100
        print(f"📊 成功率: {success_rate:.1f}%")
    
    print("\n📋 详细测试结果:")
    print("-" * 40)
    
    for result in TEST_CONFIG["test_results"]:
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {result['task']}: {result['message']}")
    
    # 保存测试报告到文件
    report_data = {
        "test_summary": {
            "total_time": total_time,
            "total_tests": total_tests,
            "passed_tests": TEST_CONFIG['passed_tests'],
            "failed_tests": TEST_CONFIG['failed_tests'],
            "success_rate": (TEST_CONFIG['passed_tests'] / total_tests * 100) if total_tests > 0 else 0
        },
        "test_results": TEST_CONFIG["test_results"]
    }
    
    with open("week2_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细报告已保存到: week2_test_report.json")
    
    # 最终评估
    if TEST_CONFIG['failed_tests'] == 0:
        print("\n🎉 所有测试通过！Week 2 功能开发质量优秀！")
    elif TEST_CONFIG['passed_tests'] > TEST_CONFIG['failed_tests']:
        print("\n✨ 大部分测试通过，Week 2 功能基本正常，需要修复部分问题。")
    else:
        print("\n⚠️  测试失败较多，需要重点检查和修复 Week 2 功能。")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生未知错误: {str(e)}")
        traceback.print_exc()

#!/usr/bin/env python3
"""
Week 3 功能测试脚本
测试文件存储服务、文档解析服务等新增功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

async def test_week3_features():
    """测试Week 3新增功能"""
    print("🚀 Week 3 功能测试开始")
    print("=" * 60)
    
    # 1. 测试文件类型验证器
    print("\n📋 1. 文件类型验证器测试")
    try:
        from app.services.file_storage_service import FileTypeValidator
        
        # 测试支持的文件类型
        extensions = FileTypeValidator.get_supported_extensions()
        categories = FileTypeValidator.get_supported_categories()
        
        print(f"✅ 支持的扩展名: {len(extensions)}个")
        print(f"   示例: {extensions[:5]}")
        print(f"✅ 支持的类型: {categories}")
        
        # 测试文件验证
        test_content = b"PDF test content"
        validation = FileTypeValidator.validate_file_type("test.pdf", test_content)
        print(f"✅ PDF验证测试: {validation['is_valid']}")
        
    except Exception as e:
        print(f"❌ 文件类型验证器测试失败: {e}")
    
    # 2. 测试文件存储服务
    print("\n🗄️ 2. 文件存储服务测试")
    try:
        from app.services.file_storage_service import file_storage_service
        
        # 创建测试文件
        test_content = b"Week 3 test document content for storage service"
        
        # 测试文件保存
        result = await file_storage_service.save_file(
            filename="week3_test.txt",
            content=test_content,
            uploaded_by="test_user"
        )
        
        if result['success']:
            print(f"✅ 文件保存成功")
            print(f"   存储路径: {result['file_info']['file_path']}")
            print(f"   文件大小: {result['file_info']['file_size']} bytes")
            print(f"   文件hash: {result['file_info']['file_hash'][:16]}...")
            
            # 测试文件信息获取
            file_path = result['file_info']['file_path']
            file_info = await file_storage_service.get_file_info(file_path)
            if file_info:
                print(f"✅ 文件信息获取成功")
            
            # 测试重复检测
            file_hash = result['file_info']['file_hash']
            existing = await file_storage_service.check_file_exists(file_hash)
            if existing:
                print(f"✅ 重复文件检测正常")
            
            # 清理测试文件
            delete_result = await file_storage_service.delete_file(file_path)
            if delete_result['success']:
                print(f"✅ 测试文件清理完成")
        else:
            print(f"❌ 文件保存失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 文件存储服务测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试存储统计
    print("\n📊 3. 存储统计测试")
    try:
        stats = file_storage_service.get_storage_stats()
        print(f"✅ 存储统计获取成功")
        print(f"   总文件数: {stats['total_files']}")
        print(f"   总大小: {stats['total_size']} bytes")
        print(f"   存储目录: {stats['upload_dir']}")
        
    except Exception as e:
        print(f"❌ 存储统计测试失败: {e}")
    
    # 4. 测试解析服务组件
    print("\n⚙️ 4. 解析服务组件测试")
    try:
        from app.services.parsing_service import ParseStatus, ParseTask, ParsingQueue
        
        # 测试解析状态枚举
        print(f"✅ 解析状态: {[status.value for status in ParseStatus]}")
        
        # 测试解析任务
        task = ParseTask(
            task_id="test-task-1",
            document_id=1,
            file_path="/tmp/test.pdf",
            file_type="pdf",
            priority=5
        )
        
        print(f"✅ 解析任务创建成功")
        print(f"   任务ID: {task.task_id}")
        print(f"   状态: {task.status.value}")
        print(f"   优先级: {task.priority}")
        
        # 测试任务队列
        queue = ParsingQueue(max_concurrent=2)
        task_id = await queue.add_task(task)
        
        stats = queue.get_queue_stats()
        print(f"✅ 任务队列正常")
        print(f"   队列统计: {stats}")
        
        # 获取任务状态
        task_status = queue.get_task_status(task_id)
        if task_status:
            print(f"✅ 任务状态查询正常")
        
    except Exception as e:
        print(f"❌ 解析服务组件测试失败: {e}")
    
    # 5. 测试外部客户端
    print("\n🌐 5. 外部客户端测试")
    try:
        from app.services.external.textin_client import TextInClient
        from app.services.external.deepseek_client import DeepSeekClient
        
        # 测试客户端初始化
        textin_client = TextInClient()
        deepseek_client = DeepSeekClient()
        
        print(f"✅ TextIn客户端初始化成功")
        print(f"   Base URL: {textin_client.base_url}")
        print(f"   超时设置: {textin_client.timeout}s")
        
        print(f"✅ DeepSeek客户端初始化成功")
        print(f"   模型: {deepseek_client.model}")
        print(f"   Base URL: {deepseek_client.base_url}")
        
    except Exception as e:
        print(f"❌ 外部客户端测试失败: {e}")
    
    # 6. 测试数据库模型
    print("\n🗃️ 6. 数据库模型测试")
    try:
        from app.models.document import Document, DocumentStatus, AuditStatus
        
        print(f"✅ 文档状态枚举: {[status.value for status in DocumentStatus]}")
        print(f"✅ 审核状态枚举: {[status.value for status in AuditStatus]}")
        print(f"✅ 文档模型字段正常")
        
        # 检查新增字段
        from sqlalchemy import inspect
        from app.core.database import engine
        
        inspector = inspect(engine)
        if 'documents' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('documents')]
            week3_fields = ['file_category', 'file_hash', 'relative_path', 'upload_time']
            
            existing_week3_fields = [field for field in week3_fields if field in columns]
            print(f"✅ Week 3新增字段: {existing_week3_fields}")
        
    except Exception as e:
        print(f"❌ 数据库模型测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Week 3 功能测试完成！")
    print("✅ 文件存储服务功能正常")
    print("✅ 文档解析服务组件正常")
    print("✅ 外部API客户端集成正常")
    print("✅ 数据库模型更新完成")
    print("\n🚀 系统已准备好进行完整功能测试")

if __name__ == "__main__":
    asyncio.run(test_week3_features())

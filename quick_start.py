#!/usr/bin/env python3
"""
招标投标规范智能审核系统 - 快速启动脚本
简化版本，专注于快速启动后端服务
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

def print_header():
    """打印标题"""
    print("\n" + "="*60)
    print("🚀 招标投标规范智能审核系统 - 快速启动")
    print("   Tender Specification Compliance Review System")
    print("="*60)
    print(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 {Path.cwd()}")
    print()

def check_environment():
    """检查环境"""
    print("🔍 检查环境...")
    
    # 检查虚拟环境
    venv_path = Path("zaobiao_env")
    if not venv_path.exists():
        print("❌ 虚拟环境不存在")
        print("💡 请先运行: python -m venv zaobiao_env")
        print("💡 然后运行: pip install -r requirements.txt")
        return False
    
    print("✅ 虚拟环境存在")
    return True

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    
    try:
        # 根据操作系统选择命令
        if os.name == 'nt':  # Windows
            cmd = [
                "cmd", "/c",
                "zaobiao_env\\Scripts\\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload"
            ]
        else:  # Unix/Linux/macOS
            cmd = [
                "bash", "-c",
                "source zaobiao_env/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload"
            ]
        
        # 启动进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 监控输出
        def monitor_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[后端] {line.strip()}")
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(5)
        
        # 检查服务是否启动成功
        try:
            import requests
            response = requests.get("http://127.0.0.1:8090/health", timeout=3)
            if response.status_code == 200:
                print("✅ 后端服务启动成功!")
                return process
        except:
            pass
        
        print("⚠️ 服务可能还在启动中...")
        return process
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def create_frontend_page():
    """创建简单的前端页面"""
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>招标投标规范智能审核系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .container { 
            text-align: center; 
            background: rgba(255,255,255,0.1);
            padding: 50px;
            border-radius: 20px;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 90%;
        }
        .title { 
            font-size: 3em; 
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            font-size: 1.3em;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .status-card { 
            background: rgba(76, 175, 80, 0.8); 
            padding: 20px; 
            border-radius: 12px; 
            margin: 25px 0;
            font-weight: bold;
            font-size: 1.1em;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature-card {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .api-link { 
            display: inline-block;
            background: rgba(33, 150, 243, 0.8);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px;
            transition: all 0.3s;
            font-weight: bold;
        }
        .api-link:hover { 
            background: rgba(33, 150, 243, 1);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
        }
        .version-info {
            margin-top: 40px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">🚀 招标投标规范智能审核系统</h1>
        <p class="subtitle">Tender Specification Compliance Review System</p>
        
        <div class="status-card">
            ✅ 后端服务运行中 (Port: 8090)
        </div>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>📄 文档管理</h3>
                <p>智能文件验证<br>高性能解析队列</p>
            </div>
            <div class="feature-card">
                <h3>🤖 AI集成</h3>
                <p>DeepSeek API<br>TextIn 文档解析</p>
            </div>
            <div class="feature-card">
                <h3>🗄️ 存储优化</h3>
                <p>模块化架构<br>缓存管理</p>
            </div>
            <div class="feature-card">
                <h3>🔗 API接口</h3>
                <p>RESTful设计<br>完整文档</p>
            </div>
        </div>
        
        <div>
            <a href="http://127.0.0.1:8090/docs" class="api-link" target="_blank">
                📚 API文档 (Swagger)
            </a>
            <a href="http://127.0.0.1:8090/health" class="api-link" target="_blank">
                💓 健康检查
            </a>
            <a href="http://127.0.0.1:8090/api/v1/documents/" class="api-link" target="_blank">
                📋 文档管理
            </a>
            <a href="http://127.0.0.1:8090/api/v1/documents/supported-types" class="api-link" target="_blank">
                📋 支持文件类型
            </a>
        </div>
        
        <div class="version-info">
            <strong>🎯 Week 3 里程碑完成!</strong><br>
            ✅ 文档管理模块 | ✅ 文件存储服务 | ✅ 解析队列<br>
            ✅ API接口增强 | ✅ 数据模型优化 | ✅ 测试验证<br><br>
            <em>前端开发计划: Week 10 - React + TypeScript + Ant Design Pro</em>
        </div>
    </div>
    
    <script>
        // 每30秒检查一次后端状态
        setInterval(async () => {
            try {
                const response = await fetch('http://127.0.0.1:8090/health');
                if (response.ok) {
                    console.log('✅ 后端服务正常');
                } else {
                    console.log('⚠️ 后端服务异常');
                }
            } catch (error) {
                console.log('❌ 后端服务连接失败');
            }
        }, 30000);
    </script>
</body>
</html>"""
    
    # 写入文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ 前端页面已创建: index.html")

def open_browser():
    """打开浏览器"""
    def delayed_open():
        time.sleep(3)
        try:
            webbrowser.open("http://127.0.0.1:8090/docs")
            print("🌐 已自动打开API文档")
        except:
            pass
    
    threading.Thread(target=delayed_open, daemon=True).start()

def main():
    """主函数"""
    print_header()
    
    # 检查环境
    if not check_environment():
        input("按Enter键退出...")
        return
    
    # 启动后端
    process = start_backend()
    if not process:
        input("按Enter键退出...")
        return
    
    # 创建前端页面
    create_frontend_page()
    
    # 自动打开浏览器
    open_browser()
    
    # 显示状态
    print("\n" + "="*60)
    print("🎉 服务启动完成!")
    print("🌐 访问地址:")
    print("  - API文档: http://127.0.0.1:8090/docs")
    print("  - 健康检查: http://127.0.0.1:8090/health")
    print("  - 文档管理: http://127.0.0.1:8090/api/v1/documents/")
    print("  - 本地页面: file://" + str(Path.cwd() / "index.html"))
    print("="*60)
    print("📝 按 Ctrl+C 停止服务")
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在关闭服务...")
        process.terminate()
        
        # 清理文件
        if Path("index.html").exists():
            os.remove("index.html")
        
        print("✅ 服务已关闭")

if __name__ == "__main__":
    main()

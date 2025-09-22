#!/usr/bin/env python3
"""
招标投标规范智能审核系统 - 自动启动脚本
支持前后端服务的自动启动、监控和管理
"""

import os
import sys
import time
import signal
import subprocess
import platform
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

class Colors:
    """终端颜色类"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.backend_port = 8090
        self.frontend_port = 3000
        self.processes: Dict[str, subprocess.Popen] = {}
        self.is_running = True
        
        # 服务配置
        self.services = {
            'backend': {
                'name': '后端服务',
                'port': self.backend_port,
                'health_endpoint': f'http://127.0.0.1:{self.backend_port}/health',
                'start_command': self._get_backend_command(),
                'cwd': str(self.project_root),
                'env': self._get_backend_env()
            },
            'frontend': {
                'name': '前端服务',
                'port': self.frontend_port,
                'health_endpoint': f'http://127.0.0.1:{self.frontend_port}',
                'start_command': self._get_frontend_command(),
                'cwd': str(self.project_root / 'frontend'),
                'env': self._get_frontend_env()
            }
        }
    
    def _get_backend_command(self) -> List[str]:
        """获取后端启动命令"""
        if platform.system() == "Windows":
            return [
                "cmd", "/c",
                "zaobiao_env\\Scripts\\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload"
            ]
        else:
            return [
                "bash", "-c",
                "source zaobiao_env/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload"
            ]
    
    def _get_frontend_command(self) -> List[str]:
        """获取前端启动命令"""
        frontend_dir = self.project_root / 'frontend'
        
        if not frontend_dir.exists():
            # 如果前端目录不存在，创建一个简单的提示服务
            return self._create_frontend_placeholder()
        
        # 检查是否是React项目
        package_json = frontend_dir / 'package.json'
        if package_json.exists():
            if platform.system() == "Windows":
                return ["cmd", "/c", "npm start"]
            else:
                return ["npm", "start"]
        
        # 如果没有前端项目，创建占位符
        return self._create_frontend_placeholder()
    
    def _create_frontend_placeholder(self) -> List[str]:
        """创建前端占位符服务"""
        placeholder_script = self.project_root / 'frontend_placeholder.py'
        
        placeholder_content = f"""#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = {self.frontend_port}

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>招标投标规范智能审核系统</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0; 
            padding: 0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh;
            color: white;
        }}
        .container {{ 
            text-align: center; 
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        .title {{ 
            font-size: 2.5em; 
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .subtitle {{ 
            font-size: 1.2em; 
            margin-bottom: 30px;
            opacity: 0.9;
        }}
        .status {{ 
            background: rgba(76, 175, 80, 0.8); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            font-weight: bold;
        }}
        .api-link {{ 
            display: inline-block;
            background: rgba(33, 150, 243, 0.8);
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px;
            transition: all 0.3s;
        }}
        .api-link:hover {{ 
            background: rgba(33, 150, 243, 1);
            transform: translateY(-2px);
        }}
        .feature-list {{
            text-align: left;
            max-width: 400px;
            margin: 30px auto;
        }}
        .feature-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">🚀 招标投标规范智能审核系统</h1>
        <p class="subtitle">Tender Specification Compliance Review System</p>
        
        <div class="status">
            ✅ 后端服务运行中 (Port: {self.backend_port})
        </div>
        
        <div class="feature-list">
            <div class="feature-item">📄 Week 3: 文档管理模块 ✅</div>
            <div class="feature-item">🔍 智能文件类型验证</div>
            <div class="feature-item">⚡ 高性能解析队列</div>
            <div class="feature-item">🗄️ 模块化存储架构</div>
            <div class="feature-item">🔗 TextIn & DeepSeek集成</div>
        </div>
        
        <div>
            <a href="http://127.0.0.1:{self.backend_port}/docs" class="api-link" target="_blank">
                📚 API文档
            </a>
            <a href="http://127.0.0.1:{self.backend_port}/health" class="api-link" target="_blank">
                💓 健康检查
            </a>
            <a href="http://127.0.0.1:{self.backend_port}/api/v1/documents/" class="api-link" target="_blank">
                📋 文档管理
            </a>
        </div>
        
        <p style="margin-top: 30px; opacity: 0.7;">
            前端开发中... 预计Week 10完成 React + TypeScript + Ant Design Pro
        </p>
    </div>
</body>
</html>
            '''.encode('utf-8')
            self.wfile.write(html_content)
        else:
            super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        print(f"前端占位符服务启动: http://127.0.0.1:{{PORT}}")
        httpd.serve_forever()
"""
        
        with open(placeholder_script, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
        
        return [sys.executable, str(placeholder_script)]
    
    def _get_backend_env(self) -> Dict[str, str]:
        """获取后端环境变量"""
        env = os.environ.copy()
        env.update({
            'PYTHONPATH': str(self.project_root),
            'UVICORN_PORT': str(self.backend_port),
            'UVICORN_HOST': '127.0.0.1'
        })
        return env
    
    def _get_frontend_env(self) -> Dict[str, str]:
        """获取前端环境变量"""
        env = os.environ.copy()
        env.update({
            'PORT': str(self.frontend_port),
            'REACT_APP_API_URL': f'http://127.0.0.1:{self.backend_port}'
        })
        return env
    
    def print_banner(self):
        """打印启动横幅"""
        banner = f"""
{Colors.HEADER}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 招标投标规范智能审核系统 - 服务启动器                      ║
║        Tender Specification Compliance Review System        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.OKGREEN}📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}
{Colors.OKBLUE}📂 项目目录: {self.project_root}{Colors.ENDC}
{Colors.OKCYAN}🔧 Python版本: {sys.version.split()[0]}{Colors.ENDC}
"""
        print(banner)
    
    def check_dependencies(self) -> bool:
        """检查依赖"""
        print(f"{Colors.OKCYAN}🔍 检查系统依赖...{Colors.ENDC}")
        
        # 检查Python虚拟环境
        venv_path = self.project_root / 'zaobiao_env'
        if not venv_path.exists():
            print(f"{Colors.FAIL}❌ 虚拟环境不存在: {venv_path}{Colors.ENDC}")
            print(f"{Colors.WARNING}💡 请先创建虚拟环境: python -m venv zaobiao_env{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✅ 虚拟环境检查通过{Colors.ENDC}")
        
        # 检查requirements.txt
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            print(f"{Colors.WARNING}⚠️  requirements.txt 不存在{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✅ requirements.txt 存在{Colors.ENDC}")
        
        # 检查端口占用
        for service_name, config in self.services.items():
            if self._is_port_in_use(config['port']):
                print(f"{Colors.WARNING}⚠️  端口 {config['port']} 已被占用 ({config['name']}){Colors.ENDC}")
            else:
                print(f"{Colors.OKGREEN}✅ 端口 {config['port']} 可用 ({config['name']}){Colors.ENDC}")
        
        return True
    
    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    
    def start_service(self, service_name: str) -> bool:
        """启动单个服务"""
        config = self.services[service_name]
        print(f"{Colors.OKCYAN}🚀 启动{config['name']}...{Colors.ENDC}")
        
        try:
            # 创建工作目录
            os.makedirs(config['cwd'], exist_ok=True)
            
            # 启动进程
            process = subprocess.Popen(
                config['start_command'],
                cwd=config['cwd'],
                env=config['env'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[service_name] = process
            
            # 启动日志监控线程
            log_thread = threading.Thread(
                target=self._monitor_service_logs,
                args=(service_name, process),
                daemon=True
            )
            log_thread.start()
            
            # 等待服务启动
            if self._wait_for_service(service_name):
                print(f"{Colors.OKGREEN}✅ {config['name']}启动成功 (PID: {process.pid}){Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}❌ {config['name']}启动失败{Colors.ENDC}")
                return False
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ 启动{config['name']}时出错: {e}{Colors.ENDC}")
            return False
    
    def _monitor_service_logs(self, service_name: str, process: subprocess.Popen):
        """监控服务日志"""
        config = self.services[service_name]
        
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            # 过滤和着色日志
            line = line.strip()
            if line:
                if 'ERROR' in line or 'FAIL' in line or 'Exception' in line:
                    print(f"{Colors.FAIL}[{service_name}] {line}{Colors.ENDC}")
                elif 'WARNING' in line or 'WARN' in line:
                    print(f"{Colors.WARNING}[{service_name}] {line}{Colors.ENDC}")
                elif 'SUCCESS' in line or '✅' in line or 'startup complete' in line:
                    print(f"{Colors.OKGREEN}[{service_name}] {line}{Colors.ENDC}")
                elif 'INFO' in line:
                    print(f"{Colors.OKBLUE}[{service_name}] {line}{Colors.ENDC}")
                else:
                    print(f"[{service_name}] {line}")
    
    def _wait_for_service(self, service_name: str, timeout: int = 30) -> bool:
        """等待服务启动"""
        config = self.services[service_name]
        
        print(f"{Colors.OKCYAN}⏳ 等待{config['name']}启动...{Colors.ENDC}")
        
        for i in range(timeout):
            try:
                response = requests.get(config['health_endpoint'], timeout=1)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            if i % 5 == 0:
                print(f"{Colors.OKCYAN}⏳ 仍在等待{config['name']}... ({i}/{timeout}){Colors.ENDC}")
        
        return False
    
    def start_all_services(self):
        """启动所有服务"""
        print(f"\n{Colors.BOLD}📡 开始启动所有服务...{Colors.ENDC}\n")
        
        # 先启动后端
        if self.start_service('backend'):
            print(f"{Colors.OKGREEN}✅ 后端服务启动成功{Colors.ENDC}")
            
            # 再启动前端
            if self.start_service('frontend'):
                print(f"{Colors.OKGREEN}✅ 前端服务启动成功{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  前端服务启动失败，但后端正常运行{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ 后端服务启动失败，取消启动前端{Colors.ENDC}")
            return False
        
        return True
    
    def print_service_status(self):
        """打印服务状态"""
        print(f"\n{Colors.BOLD}📊 服务状态摘要:{Colors.ENDC}")
        print("=" * 60)
        
        for service_name, config in self.services.items():
            process = self.processes.get(service_name)
            if process and process.poll() is None:
                status = f"{Colors.OKGREEN}✅ 运行中{Colors.ENDC}"
                pid = f"PID: {process.pid}"
            else:
                status = f"{Colors.FAIL}❌ 已停止{Colors.ENDC}"
                pid = "PID: N/A"
            
            print(f"  {config['name']:12} | {status} | 端口: {config['port']} | {pid}")
        
        print("=" * 60)
        print(f"{Colors.OKCYAN}🌐 访问地址:{Colors.ENDC}")
        print(f"  前端: http://127.0.0.1:{self.frontend_port}")
        print(f"  后端: http://127.0.0.1:{self.backend_port}")
        print(f"  API文档: http://127.0.0.1:{self.backend_port}/docs")
        print("=" * 60)
    
    def setup_signal_handlers(self):
        """设置信号处理"""
        def signal_handler(signum, frame):
            print(f"\n{Colors.WARNING}🛑 收到停止信号，正在关闭服务...{Colors.ENDC}")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def shutdown(self):
        """关闭所有服务"""
        print(f"{Colors.WARNING}🛑 正在关闭所有服务...{Colors.ENDC}")
        self.is_running = False
        
        for service_name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"{Colors.OKCYAN}⏹️  关闭{self.services[service_name]['name']}...{Colors.ENDC}")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"{Colors.WARNING}⚠️  强制关闭{service_name}...{Colors.ENDC}")
                    process.kill()
                    process.wait()
                
                print(f"{Colors.OKGREEN}✅ {self.services[service_name]['name']}已关闭{Colors.ENDC}")
        
        # 清理临时文件
        placeholder_script = self.project_root / 'frontend_placeholder.py'
        if placeholder_script.exists():
            placeholder_script.unlink()
        
        print(f"{Colors.OKGREEN}✅ 所有服务已关闭{Colors.ENDC}")
    
    def monitor_services(self):
        """监控服务状态"""
        print(f"\n{Colors.BOLD}👁️  开始监控服务状态... (按 Ctrl+C 停止){Colors.ENDC}")
        
        try:
            while self.is_running:
                time.sleep(10)
                
                # 检查进程状态
                for service_name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        print(f"{Colors.FAIL}💥 {self.services[service_name]['name']}意外退出 (退出码: {process.returncode}){Colors.ENDC}")
                        
                        # 尝试重启
                        print(f"{Colors.OKCYAN}🔄 尝试重启{self.services[service_name]['name']}...{Colors.ENDC}")
                        if self.start_service(service_name):
                            print(f"{Colors.OKGREEN}✅ {self.services[service_name]['name']}重启成功{Colors.ENDC}")
                        else:
                            print(f"{Colors.FAIL}❌ {self.services[service_name]['name']}重启失败{Colors.ENDC}")
        
        except KeyboardInterrupt:
            pass
    
    def run(self):
        """主运行方法"""
        self.print_banner()
        
        # 检查依赖
        if not self.check_dependencies():
            print(f"{Colors.FAIL}❌ 依赖检查失败，请修复后重试{Colors.ENDC}")
            return False
        
        # 设置信号处理
        self.setup_signal_handlers()
        
        # 启动所有服务
        if self.start_all_services():
            self.print_service_status()
            
            # 自动打开浏览器
            try:
                import webbrowser
                time.sleep(2)
                webbrowser.open(f'http://127.0.0.1:{self.frontend_port}')
                print(f"{Colors.OKGREEN}🌐 已自动打开浏览器{Colors.ENDC}")
            except Exception:
                print(f"{Colors.WARNING}⚠️  无法自动打开浏览器{Colors.ENDC}")
            
            # 监控服务
            self.monitor_services()
        else:
            print(f"{Colors.FAIL}❌ 服务启动失败{Colors.ENDC}")
            return False
        
        return True

def main():
    """主函数"""
    manager = ServiceManager()
    
    try:
        success = manager.run()
        return 0 if success else 1
    except Exception as e:
        print(f"{Colors.FAIL}💥 启动器出现异常: {e}{Colors.ENDC}")
        return 1
    finally:
        manager.shutdown()

if __name__ == "__main__":
    sys.exit(main())

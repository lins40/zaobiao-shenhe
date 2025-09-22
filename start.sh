#!/bin/bash
# 招标投标规范智能审核系统 - 启动脚本 (Linux/macOS)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 配置
BACKEND_PORT=8090
FRONTEND_PORT=3000
PROJECT_ROOT=$(dirname "$(realpath "$0")")

# 打印横幅
print_banner() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║     🚀 招标投标规范智能审核系统 - 服务启动器                      ║${NC}"
    echo -e "${CYAN}║        Tender Specification Compliance Review System        ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}📅 启动时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}📂 项目目录: ${PROJECT_ROOT}${NC}"
    echo ""
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用 ($service_name)${NC}"
        echo -e "${YELLOW}   尝试释放端口...${NC}"
        
        # 尝试优雅关闭
        pkill -f "uvicorn.*$port" 2>/dev/null
        pkill -f "python.*$port" 2>/dev/null
        sleep 2
        
        # 强制关闭
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            kill -9 $(lsof -ti:$port) 2>/dev/null
            echo -e "${GREEN}✅ 端口 $port 已释放${NC}"
        fi
    else
        echo -e "${GREEN}✅ 端口 $port 可用 ($service_name)${NC}"
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${CYAN}🔍 检查系统依赖...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Python3 检查通过${NC}"
    
    # 检查虚拟环境
    if [ ! -d "zaobiao_env" ]; then
        echo -e "${RED}❌ 虚拟环境不存在${NC}"
        echo -e "${YELLOW}💡 请先创建虚拟环境: python3 -m venv zaobiao_env${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ 虚拟环境检查通过${NC}"
    
    # 检查端口
    check_port $BACKEND_PORT "后端服务"
    check_port $FRONTEND_PORT "前端服务"
    
    return 0
}

# 等待服务启动
wait_for_service() {
    local url=$1
    local service_name=$2
    local timeout=30
    
    echo -e "${CYAN}⏳ 等待${service_name}启动...${NC}"
    
    for i in $(seq 1 $timeout); do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ${service_name}启动成功${NC}"
            return 0
        fi
        
        if [ $((i % 5)) -eq 0 ]; then
            echo -e "${CYAN}⏳ 仍在等待${service_name}... ($i/$timeout)${NC}"
        fi
        
        sleep 1
    done
    
    echo -e "${RED}❌ ${service_name}启动超时${NC}"
    return 1
}

# 启动后端服务
start_backend() {
    echo -e "${CYAN}🚀 启动后端服务...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # 激活虚拟环境并启动后端
    source zaobiao_env/bin/activate
    
    # 后台启动后端
    nohup python -m uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo "后端服务 PID: $BACKEND_PID" > .pids
    
    # 等待后端启动
    if wait_for_service "http://127.0.0.1:$BACKEND_PORT/health" "后端服务"; then
        echo -e "${GREEN}✅ 后端服务运行中 (PID: $BACKEND_PID)${NC}"
        return 0
    else
        echo -e "${RED}❌ 后端服务启动失败${NC}"
        kill $BACKEND_PID 2>/dev/null
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${CYAN}🚀 启动前端服务...${NC}"
    
    # 创建简单的前端占位符
    cat > frontend_placeholder.py << EOF
#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
import threading
import time

PORT = $FRONTEND_PORT

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
        body { 
            font-family: 'Microsoft YaHei', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0; 
            padding: 0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh;
            color: white;
        }
        .container { 
            text-align: center; 
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .title { 
            font-size: 2.5em; 
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status { 
            background: rgba(76, 175, 80, 0.8); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            font-weight: bold;
        }
        .api-link { 
            display: inline-block;
            background: rgba(33, 150, 243, 0.8);
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px;
            transition: all 0.3s;
        }
        .api-link:hover { 
            background: rgba(33, 150, 243, 1);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">🚀 招标投标规范智能审核系统</h1>
        <p>Tender Specification Compliance Review System</p>
        
        <div class="status">
            ✅ 后端服务运行中 (Port: $BACKEND_PORT)
        </div>
        
        <div>
            <a href="http://127.0.0.1:$BACKEND_PORT/docs" class="api-link" target="_blank">
                📚 API文档
            </a>
            <a href="http://127.0.0.1:$BACKEND_PORT/health" class="api-link" target="_blank">
                💓 健康检查
            </a>
            <a href="http://127.0.0.1:$BACKEND_PORT/api/v1/documents/" class="api-link" target="_blank">
                📋 文档管理
            </a>
        </div>
        
        <p style="margin-top: 30px; opacity: 0.7;">
            前端开发中... 预计Week 10完成
        </p>
    </div>
</body>
</html>
            '''.encode('utf-8')
            self.wfile.write(html_content)
        else:
            super().do_GET()

def open_browser():
    time.sleep(2)
    try:
        webbrowser.open(f'http://127.0.0.1:{PORT}')
    except:
        pass

if __name__ == "__main__":
    # 启动浏览器线程
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    with socketserver.TCPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        print(f"前端服务启动: http://127.0.0.1:{PORT}")
        httpd.serve_forever()
EOF
    
    # 后台启动前端
    nohup python3 frontend_placeholder.py > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    echo "前端服务 PID: $FRONTEND_PID" >> .pids
    
    # 等待前端启动
    if wait_for_service "http://127.0.0.1:$FRONTEND_PORT" "前端服务"; then
        echo -e "${GREEN}✅ 前端服务运行中 (PID: $FRONTEND_PID)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  前端服务启动失败${NC}"
        kill $FRONTEND_PID 2>/dev/null
        return 1
    fi
}

# 打印服务状态
print_status() {
    echo ""
    echo -e "${BOLD}📊 服务状态摘要:${NC}"
    echo "============================================================"
    echo -e "  后端服务     | ${GREEN}✅ 运行中${NC} | 端口: $BACKEND_PORT"
    echo -e "  前端服务     | ${GREEN}✅ 运行中${NC} | 端口: $FRONTEND_PORT"
    echo "============================================================"
    echo -e "${CYAN}🌐 访问地址:${NC}"
    echo "  前端: http://127.0.0.1:$FRONTEND_PORT"
    echo "  后端: http://127.0.0.1:$BACKEND_PORT"
    echo "  API文档: http://127.0.0.1:$BACKEND_PORT/docs"
    echo "============================================================"
    echo -e "${YELLOW}📝 日志文件:${NC}"
    echo "  后端日志: $PROJECT_ROOT/backend.log"
    echo "  前端日志: $PROJECT_ROOT/frontend.log"
    echo "============================================================"
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 收到停止信号，正在关闭服务...${NC}"
    
    if [ -f ".pids" ]; then
        while read -r line; do
            if [[ $line == *"PID:"* ]]; then
                pid=$(echo "$line" | grep -o '[0-9]\+')
                if [ ! -z "$pid" ]; then
                    echo -e "${CYAN}⏹️  关闭进程 $pid...${NC}"
                    kill $pid 2>/dev/null
                fi
            fi
        done < .pids
        rm -f .pids
    fi
    
    # 清理临时文件
    rm -f frontend_placeholder.py
    
    echo -e "${GREEN}✅ 所有服务已关闭${NC}"
    exit 0
}

# 自动打开浏览器
open_browser() {
    sleep 3
    if command -v open &> /dev/null; then
        # macOS
        open "http://127.0.0.1:$FRONTEND_PORT"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "http://127.0.0.1:$FRONTEND_PORT"
    else
        echo -e "${YELLOW}⚠️  无法自动打开浏览器，请手动访问: http://127.0.0.1:$FRONTEND_PORT${NC}"
    fi
}

# 主函数
main() {
    # 设置信号处理
    trap cleanup SIGINT SIGTERM
    
    print_banner
    
    # 检查依赖
    if ! check_dependencies; then
        echo -e "${RED}❌ 依赖检查失败，请修复后重试${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${BOLD}📡 开始启动所有服务...${NC}"
    echo ""
    
    # 启动后端
    if start_backend; then
        # 启动前端
        start_frontend
        
        # 打印状态
        print_status
        
        # 自动打开浏览器
        open_browser &
        
        echo ""
        echo -e "${GREEN}🎉 所有服务启动完成！${NC}"
        echo -e "${YELLOW}📝 按 Ctrl+C 停止所有服务${NC}"
        echo ""
        
        # 监控服务
        while true; do
            sleep 5
            # 检查后端是否还在运行
            if ! curl -s "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
                echo -e "${RED}💥 后端服务异常退出${NC}"
                break
            fi
        done
        
    else
        echo -e "${RED}❌ 后端服务启动失败，取消启动${NC}"
        exit 1
    fi
    
    # 等待信号
    wait
}

# 运行主函数
main "$@"

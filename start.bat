@echo off
REM 招标投标规范智能审核系统 - 启动脚本 (Windows)
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 配置
set BACKEND_PORT=8090
set FRONTEND_PORT=3000
set PROJECT_ROOT=%~dp0

REM 打印横幅
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     🚀 招标投标规范智能审核系统 - 服务启动器                      ║
echo ║        Tender Specification Compliance Review System        ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📅 启动时间: %date% %time%
echo 📂 项目目录: %PROJECT_ROOT%
echo.

REM 检查Python
echo 🔍 检查系统依赖...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或未添加到PATH
    pause
    exit /b 1
)
echo ✅ Python 检查通过

REM 检查虚拟环境
if not exist "zaobiao_env" (
    echo ❌ 虚拟环境不存在
    echo 💡 请先创建虚拟环境: python -m venv zaobiao_env
    pause
    exit /b 1
)
echo ✅ 虚拟环境检查通过

REM 检查并释放端口
echo 🔍 检查端口占用...
netstat -ano | findstr ":%BACKEND_PORT%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️ 端口 %BACKEND_PORT% 已被占用，尝试释放...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

netstat -ano | findstr ":%FRONTEND_PORT%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️ 端口 %FRONTEND_PORT% 已被占用，尝试释放...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo.
echo 📡 开始启动所有服务...
echo.

REM 启动后端服务
echo 🚀 启动后端服务...
cd /d "%PROJECT_ROOT%"

REM 激活虚拟环境并启动后端
start /b cmd /c "zaobiao_env\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT% --reload > backend.log 2>&1"

REM 等待后端启动
echo ⏳ 等待后端服务启动...
set /a count=0
:wait_backend
set /a count+=1
if %count% gtr 30 (
    echo ❌ 后端服务启动超时
    goto cleanup
)

curl -s http://127.0.0.1:%BACKEND_PORT%/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    if %count% gtr 0 (
        if !count! lss 6 (
            echo ⏳ 仍在等待后端服务... (!count!/30^)
        )
    )
    goto wait_backend
)

echo ✅ 后端服务启动成功

REM 创建前端占位符
echo 🚀 启动前端服务...

REM 创建前端占位符Python脚本
(
echo import http.server
echo import socketserver
echo import webbrowser
echo import threading
echo import time
echo.
echo PORT = %FRONTEND_PORT%
echo.
echo class CustomHandler^(http.server.SimpleHTTPRequestHandler^):
echo     def do_GET^(self^):
echo         if self.path == '/':
echo             self.send_response^(200^)
echo             self.send_header^('Content-type', 'text/html; charset=utf-8'^)
echo             self.end_headers^(^)
echo             html_content = '''
echo ^<!DOCTYPE html^>
echo ^<html lang="zh-CN"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<title^>招标投标规范智能审核系统^</title^>
echo     ^<style^>
echo         body { font-family: 'Microsoft YaHei'; background: linear-gradient^(135deg, #667eea 0%%, #764ba2 100%%^); margin: 0; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
echo         .container { text-align: center; background: rgba^(255,255,255,0.1^); padding: 40px; border-radius: 15px; backdrop-filter: blur^(10px^); }
echo         .title { font-size: 2.5em; margin-bottom: 20px; }
echo         .status { background: rgba^(76, 175, 80, 0.8^); padding: 15px; border-radius: 8px; margin: 20px 0; font-weight: bold; }
echo         .api-link { display: inline-block; background: rgba^(33, 150, 243, 0.8^); color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 10px; }
echo     ^</style^>
echo ^</head^>
echo ^<body^>
echo     ^<div class="container"^>
echo         ^<h1 class="title"^>🚀 招标投标规范智能审核系统^</h1^>
echo         ^<div class="status"^>✅ 后端服务运行中 ^(Port: %BACKEND_PORT%^)^</div^>
echo         ^<div^>
echo             ^<a href="http://127.0.0.1:%BACKEND_PORT%/docs" class="api-link" target="_blank"^>📚 API文档^</a^>
echo             ^<a href="http://127.0.0.1:%BACKEND_PORT%/health" class="api-link" target="_blank"^>💓 健康检查^</a^>
echo             ^<a href="http://127.0.0.1:%BACKEND_PORT%/api/v1/documents/" class="api-link" target="_blank"^>📋 文档管理^</a^>
echo         ^</div^>
echo         ^<p style="margin-top: 30px; opacity: 0.7;"^>前端开发中... 预计Week 10完成^</p^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
echo             '''.encode^('utf-8'^)
echo             self.wfile.write^(html_content^)
echo         else:
echo             super^(^).do_GET^(^)
echo.
echo def open_browser^(^):
echo     time.sleep^(2^)
echo     try:
echo         webbrowser.open^(f'http://127.0.0.1:{PORT}'^)
echo     except:
echo         pass
echo.
echo if __name__ == "__main__":
echo     browser_thread = threading.Thread^(target=open_browser, daemon=True^)
echo     browser_thread.start^(^)
echo     with socketserver.TCPServer^(^("127.0.0.1", PORT^), CustomHandler^) as httpd:
echo         print^(f"前端服务启动: http://127.0.0.1:{PORT}"^)
echo         httpd.serve_forever^(^)
) > frontend_placeholder.py

REM 启动前端
start /b cmd /c "python frontend_placeholder.py > frontend.log 2>&1"

REM 等待前端启动
echo ⏳ 等待前端服务启动...
set /a count=0
:wait_frontend
set /a count+=1
if %count% gtr 15 (
    echo ⚠️ 前端服务启动超时
    goto show_status
)

curl -s http://127.0.0.1:%FRONTEND_PORT% >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    goto wait_frontend
)

echo ✅ 前端服务启动成功

:show_status
echo.
echo 📊 服务状态摘要:
echo ============================================================
echo   后端服务     ^| ✅ 运行中 ^| 端口: %BACKEND_PORT%
echo   前端服务     ^| ✅ 运行中 ^| 端口: %FRONTEND_PORT%
echo ============================================================
echo 🌐 访问地址:
echo   前端: http://127.0.0.1:%FRONTEND_PORT%
echo   后端: http://127.0.0.1:%BACKEND_PORT%
echo   API文档: http://127.0.0.1:%BACKEND_PORT%/docs
echo ============================================================
echo 📝 日志文件:
echo   后端日志: %PROJECT_ROOT%backend.log
echo   前端日志: %PROJECT_ROOT%frontend.log
echo ============================================================

REM 自动打开浏览器
timeout /t 2 /nobreak >nul
start http://127.0.0.1:%FRONTEND_PORT%

echo.
echo 🎉 所有服务启动完成！
echo 📝 按任意键停止所有服务...
pause >nul

:cleanup
echo.
echo 🛑 正在关闭服务...

REM 关闭Python进程
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1

REM 清理临时文件
if exist frontend_placeholder.py del frontend_placeholder.py

echo ✅ 所有服务已关闭
pause
exit /b 0

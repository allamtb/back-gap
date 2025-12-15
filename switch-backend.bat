@echo off
echo ========================================
echo   后端地址切换工具
echo ========================================
echo.
echo 请选择后端地址：
echo 1. Localhost (127.0.0.1:8000)
echo 2. 远程 IP (16.163.163.204:8000)
echo 3. 自定义地址
echo.
set /p choice="请输入选项 (1-3): "

if "%choice%"=="1" (
    set VITE_BACKEND_HOST=localhost
    set VITE_BACKEND_PORT=8000
    echo.
    echo ✓ 已切换到 Localhost
    echo 启动开发服务器...
    npm run dev
) else if "%choice%"=="2" (
    set VITE_BACKEND_HOST=16.163.163.204
    set VITE_BACKEND_PORT=8000
    echo.
    echo ✓ 已切换到远程 IP
    echo 启动开发服务器...
    npm run dev
) else if "%choice%"=="3" (
    set /p VITE_BACKEND_HOST="请输入后端 IP 地址: "
    set /p VITE_BACKEND_PORT="请输入后端端口 (默认 8000): "
    if "%VITE_BACKEND_PORT%"=="" set VITE_BACKEND_PORT=8000
    echo.
    echo ✓ 已设置为自定义地址
    echo 启动开发服务器...
    npm run dev
) else (
    echo.
    echo ✗ 无效的选项！
    pause
    exit /b 1
)


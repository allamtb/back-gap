@echo off
echo ============================================================
echo Gap Trader Backend - 统一服务器启动
echo ============================================================
echo.
echo 正在启动：
echo   - FastAPI HTTP API (http://localhost:8000)
echo   - WebSocket K线服务 (ws://localhost:8000/ws)
echo.
echo 两个服务都在同一个端口 8000 上运行
echo.
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

cd /d "%~dp0"
python main.py

echo.
echo ============================================================
echo 服务器已停止
echo ============================================================
pause

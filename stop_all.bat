@echo off
echo 停止项目管理中心服务
echo =====================

set LOGS_DIR=logs

REM 停止后端服务
if exist "%LOGS_DIR%\backend.pid" (
    set /p BACKEND_PID=<"%LOGS_DIR%\backend.pid"
    echo 停止后端服务 (PID: %BACKEND_PID%)...
    taskkill /F /PID %BACKEND_PID% 2>nul
    if not errorlevel 1 (
        echo 后端服务已停止
    ) else (
        echo 后端服务未运行或无法停止
    )
    del "%LOGS_DIR%\backend.pid"
) else (
    echo 未找到后端服务进程ID文件
    echo 尝试按名称关闭所有相关进程...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
)

REM 停止前端服务
if exist "%LOGS_DIR%\frontend.pid" (
    set /p FRONTEND_PID=<"%LOGS_DIR%\frontend.pid"
    echo 停止前端服务 (PID: %FRONTEND_PID%)...
    taskkill /F /PID %FRONTEND_PID% 2>nul
    if not errorlevel 1 (
        echo 前端服务已停止
    ) else (
        echo 前端服务未运行或无法停止
    )
    del "%LOGS_DIR%\frontend.pid"
) else (
    echo 未找到前端服务进程ID文件
    echo 尝试按名称关闭所有相关进程...
    taskkill /F /IM node.exe /FI "WINDOWTITLE eq *pnpm*" 2>nul
)

echo 所有服务已停止 
#!/bin/bash
echo "停止项目管理中心服务"
echo "====================="

LOGS_DIR="logs"

# 停止后端服务
if [ -f "$LOGS_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOGS_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "后端服务已停止"
    else
        echo "后端服务未运行"
    fi
    rm "$LOGS_DIR/backend.pid"
else
    echo "未找到后端服务进程ID文件"
    pkill -f "uvicorn app.main:app"
fi

# 停止前端服务
if [ -f "$LOGS_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOGS_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "前端服务已停止"
    else
        echo "前端服务未运行"
    fi
    rm "$LOGS_DIR/frontend.pid"
else
    echo "未找到前端服务进程ID文件"
    pkill -f "pnpm dev"
fi

echo "所有服务已停止" 
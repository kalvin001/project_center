#!/bin/bash
echo "项目管理中心启动脚本"
echo "====================="

# 检查后端环境
echo "检查后端环境..."
cd backend

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "创建后端虚拟环境..."
    python3 -m pip install uv
    uv venv
    
    echo "安装后端依赖..."
    .venv/bin/pip install -e .
    
    echo "安装额外依赖..."
    .venv/bin/python install_deps.py --force
else
    echo "后端环境已存在，检查是否可用..."
    
    # 检查pip是否可用
    if ! .venv/bin/pip --version &> /dev/null; then
        echo "检测到虚拟环境损坏，重新创建..."
        rm -rf .venv
        python3 -m pip install uv
        uv venv
        
        echo "安装后端依赖..."
        .venv/bin/pip install -e .
        
        echo "安装额外依赖..."
        .venv/bin/python install_deps.py --force
    else
        echo "后端环境正常，检查依赖是否变化..."
    
        # 检查依赖是否变化
        if [ ! -f ".deps_checksum.txt" ]; then
            echo "未找到依赖校验文件，检查依赖是否需要更新..."
            cp pyproject.toml .deps_checksum.txt
            .venv/bin/python install_deps.py
        else
            if ! cmp -s pyproject.toml .deps_checksum.txt; then
                echo "检测到pyproject.toml变化，更新依赖..."
                .venv/bin/pip install -e .
                
                echo "更新依赖校验信息..."
                cp pyproject.toml .deps_checksum.txt
                
                echo "检查并安装额外依赖..."
                .venv/bin/python install_deps.py
            else
                echo "pyproject.toml无变化，检查其他依赖..."
                .venv/bin/python install_deps.py
            fi
        fi
    fi
fi

# 检查前端环境
echo "检查前端环境..."
cd ../frontend
# 检查依赖是否变化
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install -g pnpm
    pnpm install
    
    echo "保存前端依赖校验信息..."
    cp package.json .pkg_checksum.txt
else
    echo "前端环境已存在，检查依赖是否变化..."
    
    if [ ! -f ".pkg_checksum.txt" ]; then
        echo "未找到前端依赖校验文件，需要重新安装依赖..."
        pnpm install
        
        echo "保存前端依赖校验信息..."
        cp package.json .pkg_checksum.txt
    else
        if ! cmp -s package.json .pkg_checksum.txt; then
            echo "检测到前端依赖变化，需要更新..."
            pnpm install
            
            echo "更新前端依赖校验信息..."
            cp package.json .pkg_checksum.txt
        else
            echo "前端依赖无变化，跳过安装步骤..."
        fi
    fi
fi

# 启动后端和前端（先启动后端）
echo "启动后端服务..."
LOGS_DIR="../logs"
mkdir -p $LOGS_DIR

BACKEND_LOG="$LOGS_DIR/backend_$(date +%Y%m%d_%H%M%S).log"
FRONTEND_LOG="$LOGS_DIR/frontend_$(date +%Y%m%d_%H%M%S).log"

cd ../backend
nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8011 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "后端进程ID: $BACKEND_PID"
echo $BACKEND_PID > "$LOGS_DIR/backend.pid"

# 等待后端启动
echo "等待后端启动 (5秒)..."
sleep 5

# 启动前端
echo "启动前端服务..."
cd ../frontend
nohup pnpm dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "前端进程ID: $FRONTEND_PID"
echo $FRONTEND_PID > "$LOGS_DIR/frontend.pid"

echo "服务启动中..."
echo "后端地址: http://localhost:8011"
echo "前端地址: http://localhost:8012"
echo "API文档地址: http://localhost:8011/api/docs"
echo "后端日志: $BACKEND_LOG"
echo "前端日志: $FRONTEND_LOG"
echo "====================="
echo "服务已在后台启动。使用 stop_all.sh 停止服务" 
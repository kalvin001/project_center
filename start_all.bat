@echo off
echo 项目管理中心启动脚本
echo =====================

REM 创建日志目录
if not exist logs mkdir logs

REM 检查后端环境
echo 检查后端环境...
cd backend

REM 检查虚拟环境是否存在
if not exist .venv (
    echo 创建后端虚拟环境...
    python -m pip install uv
    uv venv
    
    echo 安装后端依赖...
    .venv\Scripts\python -m pip install -e .
    
    echo 安装额外依赖...
    .venv\Scripts\python install_deps.py --force
) else (
    echo 后端环境已存在，检查是否可用...
    
    REM 检查pip是否可用
    .venv\Scripts\python -m pip --version > nul 2>&1
    if errorlevel 1 (
        echo 检测到虚拟环境损坏，重新创建...
        rmdir /s /q .venv
        python -m pip install uv
        uv venv
        
        echo 安装后端依赖...
        .venv\Scripts\python -m pip install -e .
        
        echo 安装额外依赖...
        .venv\Scripts\python install_deps.py --force
    ) else (
        echo 后端环境正常，检查依赖是否变化...
    
        REM 检查依赖是否变化
        if not exist .deps_checksum.txt (
            echo 未找到依赖校验文件，检查依赖是否需要更新...
            copy pyproject.toml .deps_checksum.txt > nul
            .venv\Scripts\python install_deps.py
        ) else (
            fc /b pyproject.toml .deps_checksum.txt > nul
            if errorlevel 1 (
                echo 检测到pyproject.toml变化，更新依赖...
                .venv\Scripts\python -m pip install -e .
                
                echo 更新依赖校验信息...
                copy pyproject.toml .deps_checksum.txt > nul
                
                echo 检查并安装额外依赖...
                .venv\Scripts\python install_deps.py
            ) else (
                echo pyproject.toml无变化，检查其他依赖...
                .venv\Scripts\python install_deps.py
            )
        )
    )
)

REM 检查前端环境
echo 检查前端环境...
cd ..\frontend
REM 检查依赖是否变化
if not exist node_modules (
    echo 安装前端依赖...
    npm install -g pnpm
    pnpm install
    
    echo 保存前端依赖校验信息...
    copy package.json .pkg_checksum.txt > nul
) else (
    echo 前端环境已存在，检查依赖是否变化...
    
    if not exist .pkg_checksum.txt (
        echo 未找到前端依赖校验文件，需要重新安装依赖...
        pnpm install
        
        echo 保存前端依赖校验信息...
        copy package.json .pkg_checksum.txt > nul
    ) else (
        fc /b package.json .pkg_checksum.txt > nul
        if errorlevel 1 (
            echo 检测到前端依赖变化，需要更新...
            pnpm install
            
            echo 更新前端依赖校验信息...
            copy package.json .pkg_checksum.txt > nul
        ) else (
            echo 前端依赖无变化，跳过安装步骤...
        )
    )
)

REM 获取当前日期时间，用于日志文件命名
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "DATETIME=%dt:~0,8%_%dt:~8,6%"

REM 启动后端和前端（先启动后端）
echo 启动后端服务...
cd ..\backend
set BACKEND_LOG=..\logs\backend_%DATETIME%.log
start /b cmd /c ".venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8011 > %BACKEND_LOG% 2>&1"
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /nh ^| findstr /i "python.exe"') do (
    echo %%a > ..\logs\backend.pid
    echo 后端进程ID: %%a
    goto :backend_started
)
:backend_started

REM 等待后端启动
echo 等待后端启动 (5秒)...
timeout /t 5 /nobreak >nul

REM 启动前端
echo 启动前端服务...
cd ..\frontend
set FRONTEND_LOG=..\logs\frontend_%DATETIME%.log
start /b cmd /c "pnpm dev > %FRONTEND_LOG% 2>&1"
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq node.exe" /nh ^| findstr /i "node.exe"') do (
    echo %%a > ..\logs\frontend.pid
    echo 前端进程ID: %%a
    goto :frontend_started
)
:frontend_started

cd ..
echo 服务启动中...
echo 后端地址: http://localhost:8011
echo 前端地址: http://localhost:8012
echo API文档地址: http://localhost:8011/api/docs
echo 后端日志: %BACKEND_LOG%
echo 前端日志: %FRONTEND_LOG%
echo =====================
echo 服务已在后台启动。使用 stop_all.bat 停止服务

REM 使启动脚本立即结束，但服务会在后台继续运行
exit 
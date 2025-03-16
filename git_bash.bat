@echo off
chcp 65001 > nul
echo 启动Git Bash终端...

REM 尝试默认路径
set GIT_BASH="C:\Program Files\Git\bin\bash.exe"

REM 检查默认路径是否存在
if not exist %GIT_BASH% (
    REM 尝试其他可能的路径
    set GIT_BASH="C:\Program Files (x86)\Git\bin\bash.exe"
    
    if not exist %GIT_BASH% (
        REM 如果仍然找不到，尝试从注册表获取
        for /f "tokens=*" %%a in ('where bash 2^>nul') do (
            set GIT_BASH="%%a"
            goto :found_bash
        )
        
        echo 未找到Git Bash，请确保已安装Git。
        echo 你可以从 https://git-scm.com/downloads 下载并安装Git。
        pause
        exit /b 1
    )
)

:found_bash
echo 找到Git Bash: %GIT_BASH%
echo 启动交互式Git Bash终端...

REM 启动Git Bash
start "" %GIT_BASH% --login -i

echo Git Bash已启动。


git add . ; git commit -m "update" ;
git push -u origin master
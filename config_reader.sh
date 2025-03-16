#!/bin/bash

# 设置配置文件路径
CONFIG_FILE="$(dirname "$0")/config.ini"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误：配置文件 $CONFIG_FILE 不存在!"
    exit 1
fi

echo "正在读取配置文件: $CONFIG_FILE"

# 初始化计数器和设置列表
CONFIG_COUNT=0
CONFIG_LIST=""

# 函数：解析INI文件
function parse_ini() {
    local file=$1
    local section=""
    
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # 跳过空行和注释
        [[ $key =~ ^[[:space:]]*$ ]] && continue
        [[ $key =~ ^[[:space:]]*\; ]] && continue
        
        # 提取节名称
        if [[ $key =~ ^\[(.+)\]$ ]]; then
            section=${BASH_REMATCH[1]}
            continue
        fi
        
        # 去除键和值中的空格
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # 跳过没有值的行
        [ -z "$value" ] && continue
        
        # 设置环境变量
        if [ -n "$key" ]; then
            export "$key"="$value"
            echo "已加载配置: $key=$value"
            CONFIG_COUNT=$((CONFIG_COUNT+1))
            CONFIG_LIST="$CONFIG_LIST $key"
        fi
    done < "$file"
}

# 解析配置文件
parse_ini "$CONFIG_FILE"

# 检查是否成功加载了任何配置
if [ $CONFIG_COUNT -eq 0 ]; then
    echo "错误：未能从配置文件中加载任何配置项！"
    exit 1
fi

echo "成功加载了 $CONFIG_COUNT 个配置项"

# 检查必要的配置项是否存在
REQUIRED_CONFIGS="PROJECT_NAME BACKEND_PORT FRONTEND_PORT BACKEND_HOST FRONTEND_HOST BACKEND_CMD FRONTEND_CMD"
MISSING_CONFIGS=""
MISSING_COUNT=0

for config in $REQUIRED_CONFIGS; do
    if [ -z "${!config}" ]; then
        MISSING_CONFIGS="$MISSING_CONFIGS $config"
        MISSING_COUNT=$((MISSING_COUNT+1))
    fi
done

if [ $MISSING_COUNT -gt 0 ]; then
    echo "错误：配置文件缺少必要的配置项:$MISSING_CONFIGS"
    exit 1
fi

echo "配置已成功加载！" 
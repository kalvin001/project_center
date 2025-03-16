"""
配置读取工具
用于读取YAML格式的配置文件，替代原有的bat脚本
"""

import os
import sys
import yaml
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_script_dir():
    """获取脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))

def read_config(config_file=None):
    """
    读取配置文件
    
    Args:
        config_file: 配置文件路径，如果未指定则使用默认路径
        
    Returns:
        dict: 配置项字典
    """
    if config_file is None:
        config_file = os.path.join(get_script_dir(), 'config.yaml')
    
    logger.info(f"正在读取配置文件: {config_file}")
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        logger.error(f"错误：配置文件 {config_file} 不存在!")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 提取配置项到平面字典
        config = {}
        
        # 基本设置
        if '基本设置' in config_data:
            for key, value in config_data['基本设置'].items():
                config[key] = value
        
        # 后端配置
        if '后端' in config_data:
            for key, value in config_data['后端'].items():
                config[key] = value
        
        # 前端配置
        if '前端' in config_data:
            for key, value in config_data['前端'].items():
                config[key] = value
        
        # 显示读取到的配置项
        for key, value in config.items():
            logger.info(f"已加载配置: {key}={value}")
        
        logger.info(f"成功加载了 {len(config)} 个配置项")
        
        # 检查必要的配置项
        required_configs = [
            'PROJECT_NAME', 'BACKEND_PORT', 'FRONTEND_PORT', 
            'BACKEND_HOST', 'FRONTEND_HOST', 'BACKEND_CMD', 
            'FRONTEND_CMD', 'BACKEND_WINDOW', 'FRONTEND_WINDOW'
        ]
        
        missing_configs = [config_name for config_name in required_configs if config_name not in config]
        
        if missing_configs:
            logger.error(f"错误：配置文件缺少必要的配置项: {', '.join(missing_configs)}")
            sys.exit(1)
        
        logger.info("配置已成功加载！")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"错误：配置文件格式错误 - {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"错误：读取配置文件时出错 - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 如果直接运行此脚本，则读取并打印配置
    config = read_config()
    print("\n配置项列表:")
    for key, value in config.items():
        print(f"{key} = {value}") 
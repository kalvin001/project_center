"""
文件处理工具模块

该模块包含文件操作的通用工具函数。
"""

import os
import shutil
import logging
import traceback
import time
from typing import Dict, Union, List


def format_size(size_bytes: int) -> str:
    """将字节大小转换为人类可读格式"""
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"


def custom_copytree(src: str, dst: str, ignore_patterns: List[str], important_files: List[str] = None):
    """
    自定义复制目录函数，应用忽略规则
    
    Args:
        src: 源目录路径
        dst: 目标目录路径
        ignore_patterns: 忽略的文件模式列表
        important_files: 重要文件列表，这些文件将始终复制，不会被忽略
    """
    from app.utils.ignore_handler import should_ignore_file
    
    if important_files is None:
        important_files = ["start_all.bat", "README.md", "prompt.txt", ".gitignore"]
    
    # 设置记录级别和日志格式
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('file_copier')
    logger.setLevel(logging.DEBUG)
    
    # 确保日志处理器不重复添加
    if not logger.handlers:
        # 创建文件处理器，保存详细日志
        log_file = f"copy_log_{time.strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    
    # 支持长路径(Windows)
    if os.name == 'nt':
        src = os.path.normpath('\\\\?\\' + os.path.abspath(src))
        dst = os.path.normpath('\\\\?\\' + os.path.abspath(dst))
        
    os.makedirs(dst, exist_ok=True)
    
    # 防止复制循环的目录路径集合
    processed_dirs = set()
    
    # 记录统计信息
    stats = {
        "total_files": 0,
        "copied_files": 0,
        "ignored_files": 0,
        "total_dirs": 0,
        "copied_dirs": 0,
        "ignored_dirs": 0,
        "important_dirs": ["backend", "frontend", "app", "projects"],  # 重要目录列表，添加projects
        "backend_files": 0,  # backend目录文件计数
        "backend_dirs": 0,   # backend目录子目录计数
        "backend_errors": [] # backend相关错误记录
    }
    
    # 检查忽略规则中是否包含重要目录
    for pattern in ignore_patterns:
        for important_dir in stats["important_dirs"]:
            if important_dir in pattern:
                logger.warning(f"警告: 忽略规则 '{pattern}' 可能会排除重要目录 '{important_dir}'")
    
    # 强制从忽略列表中移除重要目录
    filtered_ignore_patterns = []
    for pattern in ignore_patterns:
        skip = False
        for important_dir in stats["important_dirs"]:
            if important_dir == pattern or pattern.startswith(f"{important_dir}/") or pattern.startswith(f"{important_dir}\\"):
                logger.warning(f"移除忽略规则: '{pattern}'，因为它会影响重要目录 '{important_dir}'")
                skip = True
                break
        if not skip:
            filtered_ignore_patterns.append(pattern)
    
    logger.info(f"原始忽略规则数: {len(ignore_patterns)}, 过滤后忽略规则数: {len(filtered_ignore_patterns)}")
    ignore_patterns = filtered_ignore_patterns
    
    # 实现自定义的目录遍历和复制
    def _copytree(current_src, current_dst, rel_path=""):
        nonlocal stats
        
        # 检查是否是backend相关目录
        is_backend = rel_path == "backend" or rel_path.startswith("backend/") or rel_path.startswith("backend\\")
        
        # 记录重要目录的处理
        is_important_dir = False
        for imp_dir in stats["important_dirs"]:
            if rel_path == imp_dir or rel_path.startswith(f"{imp_dir}/") or rel_path.startswith(f"{imp_dir}\\"):
                is_important_dir = True
                logger.info(f"处理重要目录: {rel_path}")
                break
                
        if is_backend:
            logger.debug(f"BACKEND目录详情 - 路径: {current_src} -> {current_dst}")
            logger.debug(f"BACKEND目录详情 - 绝对路径: {os.path.abspath(current_src)}")
            logger.debug(f"BACKEND目录详情 - 目录存在: {os.path.exists(current_src)}")
            logger.debug(f"BACKEND目录详情 - 目标目录存在: {os.path.exists(current_dst)}")
        
        # 检查当前源目录是否存在
        if not os.path.exists(current_src):
            error_msg = f"源目录不存在: {current_src}"
            logger.error(error_msg)
            if is_backend:
                stats["backend_errors"].append(error_msg)
            return
            
        # 检查当前目录是否应该被忽略
        if rel_path and should_ignore_file(rel_path, ignore_patterns):
            # 重要目录永远不忽略
            if not is_important_dir:
                logger.info(f"忽略目录: {rel_path}")
                stats["ignored_dirs"] += 1
                return
            else:
                logger.warning(f"重要目录 {rel_path} 被忽略规则匹配，但将被强制处理")
            
        # 确保目标目录存在
        if not os.path.exists(current_dst):
            try:
                os.makedirs(current_dst, exist_ok=True)
                logger.debug(f"已创建目标目录: {current_dst}")
            except Exception as e:
                error_msg = f"创建目标目录失败 {current_dst}: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                if is_backend:
                    stats["backend_errors"].append(error_msg)
                return
        
        # 先处理当前目录下的文件
        files = []
        dirs = []
        
        try:
            for item in os.listdir(current_src):
                s = os.path.join(current_src, item)
                if os.path.isfile(s):
                    files.append(item)
                elif os.path.isdir(s):
                    dirs.append(item)
        except PermissionError as e:
            error_msg = f"无法访问目录 {current_src}: {e}"
            logger.warning(error_msg)
            if is_backend:
                stats["backend_errors"].append(error_msg)
            return
        except Exception as e:
            error_msg = f"列出目录 {current_src} 时出错: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            if is_backend:
                stats["backend_errors"].append(error_msg)
            return
        
        # 处理文件
        for item in files:
            stats["total_files"] += 1
            if is_backend:
                stats["backend_files"] += 1
                
            s = os.path.join(current_src, item)
            d = os.path.join(current_dst, item)
            rel_file_path = os.path.join(rel_path, item) if rel_path else item
            
            # 记录详细的backend文件信息
            if is_backend:
                try:
                    file_size = os.path.getsize(s) if os.path.exists(s) else 0
                    logger.debug(f"BACKEND文件: {rel_file_path}, 大小: {format_size(file_size)}")
                except Exception as e:
                    logger.warning(f"无法获取文件大小 {rel_file_path}: {str(e)}")
            
            # 检查是否是重要文件，如果是则一定复制
            if item in important_files:
                try:
                    shutil.copy2(s, d)
                    stats["copied_files"] += 1
                    logger.info(f"复制重要文件: {rel_file_path}")
                except Exception as e:
                    error_msg = f"复制重要文件 {rel_file_path} 失败: {str(e)}"
                    logger.error(error_msg)
                    if is_backend:
                        stats["backend_errors"].append(error_msg)
                continue
            
            # 检查是否应该忽略此文件
            should_ignore = should_ignore_file(rel_file_path, ignore_patterns)
            if should_ignore:
                stats["ignored_files"] += 1
                logger.info(f"忽略文件: {rel_file_path}")
                if is_backend:
                    logger.warning(f"BACKEND文件被忽略: {rel_file_path}")
                continue
            
            # 复制普通文件
            try:
                shutil.copy2(s, d)
                stats["copied_files"] += 1
                
                # 检查是否属于重要目录的文件
                if is_important_dir:
                    logger.info(f"复制重要目录文件: {rel_file_path}")
                    if is_backend:
                        logger.debug(f"BACKEND文件已复制: {rel_file_path}")
                else:
                    logger.info(f"复制文件: {rel_file_path}")
            except Exception as e:
                error_msg = f"复制文件 {rel_file_path} 失败: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                if is_backend:
                    stats["backend_errors"].append(error_msg)
        
        # 处理子目录
        for item in dirs:
            stats["total_dirs"] += 1
            if is_backend:
                stats["backend_dirs"] += 1
                
            s = os.path.join(current_src, item)
            d = os.path.join(current_dst, item)
            rel_dir_path = os.path.join(rel_path, item) if rel_path else item
            
            # 检查是否是重要目录
            current_is_important_dir = False
            for imp_dir in stats["important_dirs"]:
                if rel_dir_path == imp_dir or rel_dir_path.startswith(f"{imp_dir}/") or rel_dir_path.startswith(f"{imp_dir}\\"):
                    current_is_important_dir = True
                    break
                    
            is_backend_dir = rel_dir_path == "backend" or rel_dir_path.startswith("backend/") or rel_dir_path.startswith("backend\\")
            
            # 记录详细的backend目录信息
            if is_backend_dir:
                logger.debug(f"BACKEND目录: {rel_dir_path}, 路径: {s}")
            
            # 检查是否应该忽略此目录
            should_ignore = should_ignore_file(rel_dir_path, ignore_patterns)
            
            # 重要目录永远不忽略
            if current_is_important_dir:
                if should_ignore:
                    logger.warning(f"重要目录 {rel_dir_path} 被忽略规则匹配，但将被强制处理")
                should_ignore = False
            
            if should_ignore:
                stats["ignored_dirs"] += 1
                logger.info(f"忽略目录: {rel_dir_path}")
                continue
            
            # 防止目录循环复制：检查目标目录是否会导致循环
            abs_src = os.path.normpath(os.path.abspath(s))
            abs_dst = os.path.normpath(os.path.abspath(d))
            if abs_src in processed_dirs or abs_dst.startswith(abs_src + os.sep):
                logger.warning(f"跳过可能导致循环的目录: {rel_dir_path}")
                continue
            
            # 记录已处理的目录
            processed_dirs.add(abs_src)
            
            # 创建目标子目录
            try:
                os.makedirs(d, exist_ok=True)
                stats["copied_dirs"] += 1
                
                # 记录重要目录的复制
                if current_is_important_dir:
                    logger.info(f"复制重要目录: {rel_dir_path}")
                    if is_backend_dir:
                        logger.debug(f"BACKEND目录创建: {d}")
                
                # 递归处理子目录
                _copytree(s, d, rel_dir_path)
            except Exception as e:
                error_msg = f"创建目录 {rel_dir_path} 失败: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                if is_backend_dir:
                    stats["backend_errors"].append(error_msg)
    
    # 开始复制
    logger.info(f"开始复制目录: {src} -> {dst}")
    logger.info(f"忽略规则数量: {len(ignore_patterns)}")
    if len(ignore_patterns) > 0:
        logger.info(f"部分忽略规则示例: {ignore_patterns[:min(5, len(ignore_patterns))]}")
    
    # 强制创建backend目录
    logger.info("检查backend相关路径...")
    backend_src_path = os.path.join(src, "backend")
    backend_dst_path = os.path.join(dst, "backend")
    
    if os.path.exists(backend_src_path):
        logger.info(f"BACKEND源目录存在: {backend_src_path}")
        try:
            backend_content = os.listdir(backend_src_path) if os.path.isdir(backend_src_path) else '不是目录'
            logger.info(f"BACKEND源目录内容: {backend_content}")
        except Exception as e:
            logger.error(f"无法列出BACKEND源目录内容: {str(e)}")
    else:
        logger.error(f"BACKEND源目录不存在: {backend_src_path}")
        
    # 确保backend目标目录存在
    try:
        os.makedirs(backend_dst_path, exist_ok=True)
        logger.info(f"确保BACKEND目标目录已创建: {backend_dst_path}")
    except Exception as e:
        logger.error(f"创建BACKEND目标目录失败: {str(e)}")
    
    # 执行复制操作
    _copytree(src, dst)
    
    # 再次确认backend目录是否已复制
    if not os.path.exists(backend_dst_path):
        logger.error(f"复制后BACKEND目录仍不存在，尝试单独复制")
        if os.path.exists(backend_src_path):
            try:
                # 尝试直接复制backend目录
                shutil.copytree(backend_src_path, backend_dst_path)
                logger.info(f"成功通过直接方法复制BACKEND目录")
            except Exception as e:
                logger.error(f"直接复制BACKEND目录失败: {str(e)}")
    
    # 输出统计信息
    logger.info(f"复制完成，统计信息:")
    logger.info(f"  总文件数: {stats['total_files']}")
    logger.info(f"  已复制文件: {stats['copied_files']}")
    logger.info(f"  已忽略文件: {stats['ignored_files']}")
    logger.info(f"  总目录数: {stats['total_dirs']}")
    logger.info(f"  已复制目录: {stats['copied_dirs']}")
    logger.info(f"  已忽略目录: {stats['ignored_dirs']}")
    
    # 输出backend相关统计
    logger.info(f"BACKEND统计信息:")
    logger.info(f"  backend文件数: {stats['backend_files']}")
    logger.info(f"  backend目录数: {stats['backend_dirs']}")
    if stats["backend_errors"]:
        logger.error(f"BACKEND错误信息:")
        for error in stats["backend_errors"]:
            logger.error(f"  - {error}")
    
    # 检查backend目录是否成功复制
    if os.path.exists(backend_dst_path):
        logger.info(f"BACKEND目标目录已创建: {backend_dst_path}")
        try:
            backend_content = os.listdir(backend_dst_path) if os.path.isdir(backend_dst_path) else '不是目录'
            logger.info(f"BACKEND目标目录内容: {backend_content}")
        except Exception as e:
            logger.error(f"无法列出BACKEND目标目录内容: {str(e)}")
    else:
        logger.error(f"BACKEND目标目录未成功创建: {backend_dst_path}")
    
    return stats

if __name__ == "__main__":
    src = r"D:\code\eai_demo"
    dst = r"D:\code\eai_demo_copy"
    ignore_patterns = []
    important_files = ["start_all.bat", "README.md", "prompt.txt", ".gitignore"]
    custom_copytree(src, dst, ignore_patterns, important_files)

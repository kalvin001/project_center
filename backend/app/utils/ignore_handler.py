"""
.gitignore文件处理模块

该模块使用pathspec库处理.gitignore规则，确保与git的行为一致。
"""

import os
import logging
from typing import List, Callable

try:
    import pathspec  # 尝试导入pathspec库
    HAS_PATHSPEC = True
except ImportError:
    logging.warning("pathspec库未安装，将使用兼容模式。请运行 'pip install pathspec' 获取更好的性能。")
    HAS_PATHSPEC = False

def parse_gitignore_file(gitignore_file_path: str) -> List[str]:
    """
    解析.gitignore文件，返回规则列表
    
    Args:
        gitignore_file_path: .gitignore文件路径
        
    Returns:
        忽略规则列表
    """
    if not os.path.exists(gitignore_file_path):
        return []
    
    ignore_patterns = []
    try:
        with open(gitignore_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 去除注释和空白行
                line = line.strip()
                if line and not line.startswith('#'):
                    ignore_patterns.append(line)
    except Exception as e:
        logging.error(f"读取.gitignore文件出错: {e}")
    
    return ignore_patterns

def create_gitignore_matcher(gitignore_file_path: str = None, patterns: List[str] = None) -> Callable[[str], bool]:
    """
    创建一个用于匹配.gitignore规则的函数
    
    Args:
        gitignore_file_path: .gitignore文件路径，可选
        patterns: 直接提供的忽略规则列表，可选
        
    Returns:
        接受文件路径、返回是否应该忽略的函数
    """
    if not HAS_PATHSPEC:
        logging.warning("未安装pathspec库，可能导致.gitignore规则解析不准确")
        return lambda _: False
    
    # 收集规则
    all_patterns = []
    
    # 从文件读取规则
    if gitignore_file_path and os.path.exists(gitignore_file_path):
        with open(gitignore_file_path, 'r', encoding='utf-8') as f:
            all_patterns.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
    
    # 添加直接提供的规则
    if patterns:
        all_patterns.extend(patterns)
    
    # 添加几个始终应该忽略的关键模式
    critical_patterns = [
        "node_modules/", 
        "node_modules",
        "frontend/node_modules/",
        "frontend/node_modules",
        ".venv/", 
        ".venv",
        "backend/.venv/",
        "backend/.venv",
        "venv/", 
        "venv",
        "backend/venv/",
        "backend/venv",
        "__pycache__/",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".git/",
        ".git"
    ]
    
    for pattern in critical_patterns:
        if pattern not in all_patterns:
            all_patterns.append(pattern)
    
    # 创建pathspec规范
    spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, all_patterns)
    
    # 重要文件和目录列表 - 这些永远不会被忽略
    whitelist = ["start_all.bat", "README.md", "prompt.txt", ".gitignore"]
    protected_dirs = ["backend", "frontend", "app"]
    
    # 返回匹配函数
    def matcher(file_path: str) -> bool:
        # 规范化路径
        normalized_path = file_path.replace('\\', '/')
        
        # 检查白名单文件
        if normalized_path in whitelist or os.path.basename(normalized_path) in whitelist:
            return False
        
        # 检查保护目录 - 目录本身不忽略，但其内容可能被忽略
        if normalized_path in protected_dirs:
            return False
        
        # 使用pathspec检查是否匹配
        return spec.match_file(normalized_path)
    
    return matcher

def get_gitignore_patterns(project_path: str) -> List[str]:
    """
    获取项目的忽略规则，包括根目录和项目目录的.gitignore文件
    
    Args:
        project_path: 项目目录路径
        
    Returns:
        忽略规则列表
    """
    # 检查根目录的.gitignore文件，向上查找三级
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(project_path)))
    root_gitignore_path = os.path.join(project_root, ".gitignore")
    root_patterns = parse_gitignore_file(root_gitignore_path)
    
    # 检查项目目录的.gitignore文件
    project_gitignore_path = os.path.join(project_path, ".gitignore") 
    project_patterns = parse_gitignore_file(project_gitignore_path)
    
    # 合并两个列表
    all_patterns = list(set(root_patterns + project_patterns))
            
    return all_patterns

def should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """
    判断文件是否应该被忽略
    
    Args:
        file_path: 文件路径，相对于项目根目录
        ignore_patterns: 忽略规则列表
        
    Returns:
        是否应该忽略
    """
    # 规范化路径分隔符
    normalized_path = file_path.replace('\\', '/')
    
    # 白名单检查 - 这些文件永远不会被忽略
    whitelist = ["start_all.bat", "README.md", "prompt.txt", ".gitignore"]
    if normalized_path in whitelist or os.path.basename(normalized_path) in whitelist:
        return False
    
    # 重要目录本身不忽略
    protected_dirs = ["backend", "frontend", "app"]
    if normalized_path in protected_dirs:
        return False
    
    # 特殊目录总是被忽略
    if any(ignored in normalized_path for ignored in [
        "node_modules", ".venv", "venv", "__pycache__"
    ]):
        return True
    
    # 特殊文件扩展名总是被忽略
    if normalized_path.endswith(('.pyc', '.pyo', '.pyd', '.so', '.o', '.a', '.lib', '.dylib', '.dll')):
        return True
    
    if HAS_PATHSPEC:
        # 使用pathspec库进行高级匹配
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ignore_patterns)
        return spec.match_file(normalized_path)
    else:
        # 如果没有pathspec库，使用简化的功能
        for pattern in ignore_patterns:
            pattern = pattern.strip()
            
            # 忽略空行和注释
            if not pattern or pattern.startswith('#'):
                continue
                
            # 处理通配符
            if pattern.startswith('*'):
                if normalized_path.endswith(pattern[1:]):
                    return True
            # 处理目录匹配
            elif pattern.endswith('/'):
                if normalized_path.startswith(pattern) or f"/{pattern}" in normalized_path:
                    return True
            # 完全匹配
            elif pattern == normalized_path or normalized_path.endswith(f"/{pattern}") or f"/{pattern}/" in normalized_path:
                return True
        
        return False

# 保持向后兼容的函数名
parse_ignore_file = parse_gitignore_file
get_ignore_patterns = get_gitignore_patterns 


if __name__ == "__main__":
    print(get_gitignore_patterns("D:\\data\\code\\project_center"))

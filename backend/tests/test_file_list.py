import os
import re
from pathlib import Path
from typing import List, Dict, Union, Set

def parse_ignore_patterns(project_path: str) -> List[str]:
    """解析项目中的.ignore文件，返回忽略模式列表"""
    ignore_file_path = os.path.join(project_path, ".ignore")
    ignore_patterns = []
    
    # 如果存在.ignore文件，读取其内容
    if os.path.exists(ignore_file_path):
        try:
            with open(ignore_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 去除注释和空白行
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        except Exception as e:
            print(f"读取.ignore文件出错: {e}")
    
    # 添加常见的忽略模式
    common_ignore_patterns = [
        ".venv/", 
        "backend/.venv/",
        ".venv",
        "backend/.venv",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "env/",
        "venv/",
        "ENV/",
        "env.bak/",
        "venv.bak/",
        ".git/",
        ".idea/",
        ".vscode/",
        "node_modules/",
        "dist/",
        "build/",
        ".DS_Store"
    ]
    
    # 添加尚未包含的常见忽略模式
    for pattern in common_ignore_patterns:
        if pattern not in ignore_patterns:
            ignore_patterns.append(pattern)
    
    return ignore_patterns

def should_ignore(path: str, ignore_patterns: List[str]) -> bool:
    """判断文件或目录是否应该被忽略"""
    if not ignore_patterns:
        return False
    
    # 规范化路径分隔符
    normalized_path = path.replace('\\', '/')
    
    # 保留文件白名单 - 这些文件永远不会被忽略
    whitelist = ["start_all.bat", "README.md", "prompt.txt", ".ignore"]
    if normalized_path in whitelist or normalized_path.split('/')[-1] in whitelist:
        return False
    
    for pattern in ignore_patterns:
        pattern = pattern.replace('\\', '/')  # 规范化模式中的路径分隔符
        
        # 处理目录匹配模式 (pattern/)
        if pattern.endswith('/'):
            pattern_without_slash = pattern[:-1]
            # 检查是否匹配目录名称
            if (normalized_path == pattern_without_slash or 
                normalized_path.startswith(pattern) or 
                f"/{pattern_without_slash}" in normalized_path or
                normalized_path.endswith(f"/{pattern_without_slash}") or
                f"/{pattern}" in normalized_path):
                return True
        
        # 处理具体的匹配模式如 backend/.venv/
        elif '/' in pattern:
            if normalized_path.startswith(pattern) or normalized_path == pattern or pattern in normalized_path:
                return True
        
        # 处理通配符 (*.ext)
        elif pattern.startswith('*'):
            ext = pattern[1:]  # 获取扩展名部分
            if normalized_path.endswith(ext):
                return True
        
        # 处理精确匹配
        elif pattern == normalized_path or pattern in normalized_path.split('/'):
            # 特殊处理 .venv 目录
            if pattern == ".venv" and (".venv" == normalized_path or 
                                     normalized_path.endswith("/.venv") or 
                                     "/.venv/" in normalized_path):
                return True
            return True
        
        # 处理glob模式匹配
        elif '*' in pattern or '?' in pattern:
            # 转换glob模式为正则表达式
            regex_pattern = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
            if re.match(f"^{regex_pattern}$", normalized_path) or re.search(f"/{regex_pattern}$", normalized_path):
                return True
    
    return False

def get_files_to_upload(project_path: str) -> List[Dict[str, Union[str, int]]]:
    """
    获取需要上传的文件列表
    
    Args:
        project_path: 本地项目路径
    
    Returns:
        要上传的文件列表，每个文件包含路径和大小信息
    """
    try:
        # 确保项目路径存在
        if not os.path.exists(project_path):
            print(f"错误: 项目路径不存在 - {project_path}")
            return []
        
        # 获取忽略模式
        ignore_patterns = parse_ignore_patterns(project_path)
        print(f"应用的忽略模式: {ignore_patterns}")
        
        files_to_upload = []
        root_path = Path(project_path)
        
        # 遍历项目目录
        for root, dirs, files in os.walk(project_path):
            # 转换为相对路径
            rel_root = os.path.relpath(root, project_path)
            rel_root = "" if rel_root == "." else rel_root
            
            # 过滤要忽略的目录
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(rel_root, d), ignore_patterns)]
            
            for file in files:
                rel_path = os.path.join(rel_root, file).replace("\\", "/")
                
                # 检查文件是否应该被忽略
                if should_ignore(rel_path, ignore_patterns):
                    print(f"忽略文件: {rel_path}")
                    continue
                
                # 获取文件大小
                abs_path = os.path.join(root, file)
                file_size = os.path.getsize(abs_path)
                
                files_to_upload.append({
                    "path": rel_path,
                    "size": file_size
                })
        
        return files_to_upload
    
    except Exception as e:
        print(f"获取文件列表时出错: {str(e)}")
        return []

def main():
    # 测试函数
    import sys
    
    # if len(sys.argv) < 2:
    #     print("用法: python test_file_list.py <项目路径>")
    #     return
    
    # project_path = sys.argv[1]
    # print(f"分析项目路径: {os.path.abspath(project_path)}")
    
    # if not os.path.exists(project_path):
    #     print(f"错误: 指定的路径不存在!")
    #     return
    project_path = r"D:\code\projects\project_center"
        
    # 检查项目内容
    print("\n项目目录内容:")
    for root, dirs, files in os.walk(project_path, topdown=True, onerror=lambda e: print(f"访问错误: {e}")):
        level = root.replace(project_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{sub_indent}{f}")
        # 限制只显示前2级
        if level >= 1:
            dirs[:] = []
    
    # 获取文件列表
    files = get_files_to_upload(project_path)
    
    if not files:
        print("\n没有找到要上传的文件!")
        return
    
    print(f"\n要上传的文件列表 ({len(files)}个文件):")
    for file in files:
        print(f"{file['path']} ({file['size']} 字节)")
    
    # 计算总大小
    total_size = sum(file['size'] for file in files)
    print(f"\n总大小: {total_size} 字节 ({total_size / 1024:.2f} KB, {total_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    main()

    

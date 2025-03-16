import os
import re

def main():
    # 读取文件内容
    file_path = 'app/core/machines.py'
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 替换导入语句
    content = content.replace(
        "from app.models.machine_log import MachineLog",
        "from app.core.logs import create_machine_log"
    )
    
    # 替换所有的MachineLog创建实例
    pattern = r'log = MachineLog\(\s*machine_id=(\w+),\s*log_type="([^"]+)",\s*content=([^,]+),\s*status="([^"]+)"\s*\)\s*db\.add\(log\)\s*await db\.commit\(\)'
    replacement = r'await create_machine_log(db, machine_id=\1, operation="\2", title="\2操作", content=\3, status="\4")'
    content = re.sub(pattern, replacement, content)
    
    # 其他形式的MachineLog创建
    pattern2 = r'log = MachineLog\(\s*machine_id=(\w+),\s*log_type="([^"]+)",\s*content="([^"]+)",\s*status="([^"]+)"\s*\)\s*db\.add\(log\)\s*await db\.commit\(\)'
    replacement2 = r'await create_machine_log(db, machine_id=\1, operation="\2", title="\2操作", content="\3", status="\4")'
    content = re.sub(pattern2, replacement2, content)
    
    # 再处理一种形式
    pattern3 = r'log = MachineLog\(\s*machine_id=(\w+),\s*log_type="([^"]+)",\s*content=([^,]+),\s*status=([^)]+)\s*\)\s*db\.add\(log\)\s*await db\.commit\(\)'
    replacement3 = r'await create_machine_log(db, machine_id=\1, operation="\2", title="\2操作", content=\3, status=\4)'
    content = re.sub(pattern3, replacement3, content)
    
    # 写回文件
    with open(file_path + '.new', 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"处理完成，请检查 {file_path}.new 文件")


if __name__ == "__main__":
    main() 
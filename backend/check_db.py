import sqlite3
import os
import traceback

try:
    print("开始连接数据库...")
    # 连接数据库
    conn = sqlite3.connect('project_center.db')
    cur = conn.cursor()

    # 查询项目ID 9
    print("执行SQL查询...")
    cur.execute('SELECT id, name, storage_path FROM projects WHERE id = 9')
    result = cur.fetchone()

    if result:
        project_id, name, storage_path = result
        print(f"项目ID: {project_id}")
        print(f"项目名称: {name}")
        print(f"存储路径: {storage_path}")
        
        # 检查路径是否存在
        print("检查存储路径是否存在...")
        if os.path.exists(storage_path):
            print(f"路径存在: {storage_path}")
            # 检查是否为目录
            if os.path.isdir(storage_path):
                print(f"路径是一个目录")
                # 尝试列出目录内容
                try:
                    files = os.listdir(storage_path)
                    print(f"目录中的文件数量: {len(files)}")
                    if len(files) > 0:
                        print(f"前5个文件: {files[:5]}")
                except Exception as e:
                    print(f"列出目录内容时出错: {e}")
            else:
                print(f"路径不是一个目录")
        else:
            print(f"路径不存在: {storage_path}")
    else:
        print("数据库中找不到项目ID 9")
        
        # 检查是否存在其他项目
        cur.execute('SELECT id FROM projects ORDER BY id')
        project_ids = cur.fetchall()
        print(f"数据库中的项目ID列表: {[id[0] for id in project_ids]}")

    conn.close()
    print("数据库连接已关闭")

except Exception as e:
    print(f"发生错误: {e}")
    print(traceback.format_exc()) 
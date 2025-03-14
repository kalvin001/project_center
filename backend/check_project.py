import sqlite3
import json

# 连接到数据库
conn = sqlite3.connect('project_center.db')
cursor = conn.cursor()

# 获取列名
cursor.execute('PRAGMA table_info(projects)')
columns = [col[1] for col in cursor.fetchall()]
print("表结构 (部分1):", columns[:5])
print("表结构 (部分2):", columns[5:])

# 查询特定项目
cursor.execute('SELECT * FROM projects WHERE id=11')
project = cursor.fetchone()

if project:
    # 输出为字典形式更容易阅读
    project_dict = {columns[i]: project[i] for i in range(len(columns))}
    
    # 将结果写入文件
    with open('project_data.json', 'w') as f:
        json.dump(project_dict, f, indent=2, default=str)
        
    print("\n项目数据已写入 project_data.json 文件")
    
    # 打印部分关键字段
    print("\n关键字段:")
    key_fields = ['id', 'name', 'repository_type', 'repository_url']
    for key in key_fields:
        if key in project_dict:
            print(f"{key}: {project_dict[key]}")
else:
    print("未找到ID为11的项目")

# 关闭连接
conn.close() 
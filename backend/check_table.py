import sqlite3

# 连接到数据库
conn = sqlite3.connect('project_center.db')
cursor = conn.cursor()

# 查询表结构
cursor.execute('PRAGMA table_info(projects)')
columns = cursor.fetchall()

# 输出所有列
for col in columns:
    print(col)

# 关闭连接
conn.close() 
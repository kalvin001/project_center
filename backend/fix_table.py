import sqlite3

# 连接到数据库
conn = sqlite3.connect('project_center.db')
cursor = conn.cursor()

try:
    # 开始事务
    cursor.execute('BEGIN TRANSACTION')
    
    # 1. 创建临时表
    cursor.execute('''
    CREATE TABLE projects_new (
        id INTEGER NOT NULL,
        name VARCHAR NOT NULL,
        description TEXT,
        owner_id INTEGER NOT NULL,
        repository_url VARCHAR,
        repository_type VARCHAR DEFAULT 'git' NOT NULL,
        last_updated DATETIME DEFAULT (CURRENT_TIMESTAMP),
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
        is_active BOOLEAN,
        project_type VARCHAR NOT NULL,
        tech_stack JSON,
        storage_path VARCHAR NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(owner_id) REFERENCES users (id)
    )
    ''')
    
    # 2. 复制数据到新表 (没有repository_type的项目使用默认值'git')
    cursor.execute('''
    INSERT INTO projects_new (id, name, description, owner_id, repository_url, 
                             last_updated, created_at, is_active, 
                             project_type, tech_stack, storage_path)
    SELECT id, name, description, owner_id, repository_url, 
           last_updated, created_at, is_active, 
           project_type, tech_stack, storage_path
    FROM projects
    ''')
    
    # 3. 删除旧表
    cursor.execute('DROP TABLE projects')
    
    # 4. 重命名新表
    cursor.execute('ALTER TABLE projects_new RENAME TO projects')
    
    # 5. 重新创建索引
    cursor.execute('CREATE INDEX ix_projects_id ON projects (id)')
    cursor.execute('CREATE INDEX ix_projects_name ON projects (name)')
    
    # 提交事务
    conn.commit()
    print("表结构修复成功！添加了repository_type列")

except Exception as e:
    # 出现错误时回滚
    conn.rollback()
    print(f"发生错误: {e}")

finally:
    # 关闭连接
    conn.close() 
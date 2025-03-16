import sqlite3
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "project_center.db")

def rebuild_tables():
    """删除现有表并创建新的部署表"""
    print(f"开始重建部署相关表: {DB_PATH}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件 {DB_PATH} 不存在")
        return False
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 开始事务
        cursor.execute("BEGIN TRANSACTION")
        
        # 删除现有表
        print("删除现有的 project_machine 表...")
        cursor.execute("DROP TABLE IF EXISTS project_machine")
        
        print("删除现有的 deployments 表...")
        cursor.execute("DROP TABLE IF EXISTS deployments")
        
        # 创建新的部署表
        print("创建新的 deployments 表...")
        cursor.execute("""
            CREATE TABLE deployments (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                machine_id INTEGER NOT NULL,
                environment TEXT NOT NULL DEFAULT 'development',
                deploy_path TEXT,
                status TEXT DEFAULT 'not_deployed',
                log TEXT,
                deployed_at TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                UNIQUE (project_id, machine_id)
            )
        """)
        
        # 提交事务
        conn.commit()
        print("表重建成功!")
        return True
    
    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(f"错误: 表重建失败: {str(e)}")
        return False
    
    finally:
        # 关闭连接
        conn.close()

if __name__ == "__main__":
    rebuild_tables() 
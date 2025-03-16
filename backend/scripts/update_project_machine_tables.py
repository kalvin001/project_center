import sqlite3
import os
from datetime import datetime

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "project_center.db")

def update_database():
    """更新数据库表结构，添加project_machine关联表，更新deployment表"""
    print(f"开始更新数据库: {DB_PATH}")
    
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
        
        # 检查deployments表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deployments'")
        if cursor.fetchone():
            print("检测到deployments表，备份表...")
            
            # 创建备份表
            cursor.execute("""
                CREATE TABLE deployments_backup (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    environment TEXT NOT NULL,
                    deploy_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    log TEXT,
                    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            # 转储数据
            print("转储旧的部署数据...")
            cursor.execute("""
                INSERT INTO deployments_backup (id, project_id, environment, deploy_path, status, log, deployed_at)
                SELECT id, project_id, environment, deploy_path, status, log, deployed_at
                FROM deployments
            """)
            
            # 删除旧表
            cursor.execute("DROP TABLE deployments")
            print("删除旧的部署表...")
        
        # 创建project_machine关联表
        print("创建project_machine关联表...")
        cursor.execute("""
            CREATE TABLE project_machine (
                project_id INTEGER NOT NULL,
                machine_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, machine_id),
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (machine_id) REFERENCES machines (id)
            )
        """)
        
        # 创建新的deployments表
        print("创建新的deployments表...")
        cursor.execute("""
            CREATE TABLE deployments (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                machine_id INTEGER NOT NULL,
                environment TEXT NOT NULL,
                deploy_path TEXT NOT NULL,
                status TEXT NOT NULL,
                log TEXT,
                deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (machine_id) REFERENCES machines (id)
            )
        """)
        
        # 如果有备份表，尝试导入数据
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deployments_backup'")
        if cursor.fetchone():
            print("检测到备份表，迁移数据到新表...")
            
            # 获取机器ID列表
            cursor.execute("SELECT id FROM machines LIMIT 1")
            machine_row = cursor.fetchone()
            if machine_row:
                # 将旧数据导入到新表，使用获取到的第一个机器ID
                machine_id = machine_row[0]
                cursor.execute(f"""
                    INSERT INTO deployments (project_id, machine_id, environment, deploy_path, status, log, deployed_at)
                    SELECT project_id, {machine_id}, environment, deploy_path, status, log, deployed_at
                    FROM deployments_backup
                """)
                print(f"数据迁移完成，所有旧部署记录关联到机器ID: {machine_id}")
            else:
                print("警告: 未找到可用机器，无法迁移旧的部署数据")
                
            # 删除备份表
            cursor.execute("DROP TABLE deployments_backup")
            print("删除备份表...")
        
        # 提交事务
        conn.commit()
        print("数据库更新成功!")
        return True
    
    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(f"错误: 数据库更新失败: {str(e)}")
        return False
    
    finally:
        # 关闭连接
        conn.close()

if __name__ == "__main__":
    update_database() 
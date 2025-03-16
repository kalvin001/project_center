import sqlite3
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "project_center.db")

def check_tables():
    """检查数据库表结构"""
    print("开始检查数据库表结构...")
    print(f"数据库路径：{DB_PATH}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件 {DB_PATH} 不存在")
        return False
    else:
        print(f"数据库文件存在")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\n现有的表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 检查project_machine表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_machine'")
        if cursor.fetchone():
            print("\nproject_machine表结构:")
            cursor.execute("PRAGMA table_info(project_machine)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        else:
            print("\nproject_machine表不存在")
            
        # 检查deployments表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deployments'")
        if cursor.fetchone():
            print("\ndeployments表结构:")
            cursor.execute("PRAGMA table_info(deployments)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
            
            # 获取部署记录数量
            cursor.execute("SELECT COUNT(*) FROM deployments")
            count = cursor.fetchone()[0]
            print(f"\ndeployments表中有 {count} 条记录")
        else:
            print("\ndeployments表不存在")
        
        print("\n检查完成")
    
    except Exception as e:
        print(f"错误: 检查表结构失败: {str(e)}")
        return False
    
    finally:
        # 关闭连接
        conn.close()

if __name__ == "__main__":
    print("脚本开始执行")
    check_tables()
    print("脚本执行完毕") 
import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def add_avatar_column():
    """向users表添加avatar_url列"""
    db_path = os.path.join(os.getcwd(), "project_center.db")
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return
    
    logger.info(f"正在修改数据库: {db_path}")
    
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查avatar_url列是否存在
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if "avatar_url" not in column_names:
            logger.info("avatar_url列不存在，正在添加...")
            # 添加avatar_url列
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
            conn.commit()
            logger.info("avatar_url列添加成功")
        else:
            logger.info("avatar_url列已存在，无需添加")
        
        conn.close()
        logger.info("数据库修改完成")
        
    except Exception as e:
        logger.error(f"修改数据库出错: {str(e)}")

if __name__ == "__main__":
    add_avatar_column() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'project_center.db')

def update_machine_password():
    """检查并更新机器密码"""
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 首先查看表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("数据库中的表:")
    for table in tables:
        print(f"- {table[0]}")
    
    # 查询机器表名
    machine_table = None
    for table in tables:
        if 'machine' in table[0].lower():
            machine_table = table[0]
            break
    
    if not machine_table:
        print("未找到机器相关的表")
        conn.close()
        return
    
    print(f"使用表: {machine_table}")
    
    # 查看表结构
    cursor.execute(f"PRAGMA table_info({machine_table})")
    columns = cursor.fetchall()
    print(f"{machine_table} 表的列:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # 查询机器信息
    try:
        cursor.execute(f"SELECT * FROM {machine_table} WHERE id = 1")
        machine = cursor.fetchone()
        
        if not machine:
            print("未找到ID为1的机器")
            conn.close()
            return
        
        # 显示机器信息
        column_names = [col[1] for col in columns]
        for i, value in enumerate(machine):
            if i < len(column_names):
                print(f"{column_names[i]}: {value}")
        
        # 找到密码列的索引
        password_idx = None
        for i, col in enumerate(columns):
            if col[1].lower() == 'password':
                password_idx = i
                break
        
        if password_idx is None:
            print("未找到密码列")
            conn.close()
            return
        
        password = machine[password_idx]
        print(f"当前密码: {password}")
        
        # 如果密码为空或者不正确，更新密码
        if not password:
            new_password = "your_secure_password"  # 替换为实际密码
            print(f"密码为空，更新为: {new_password}")
            
            # 更新密码
            cursor.execute(f"UPDATE {machine_table} SET password = ? WHERE id = 1", (new_password,))
            conn.commit()
            print("密码已更新")
        else:
            print("密码已存在，是否需要更新? (y/n)")
            choice = input().strip().lower()
            if choice == 'y':
                new_password = input("请输入新密码: ").strip()
                if new_password:
                    # 更新密码
                    cursor.execute(f"UPDATE {machine_table} SET password = ? WHERE id = 1", (new_password,))
                    conn.commit()
                    print("密码已更新")
    
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    update_machine_password() 
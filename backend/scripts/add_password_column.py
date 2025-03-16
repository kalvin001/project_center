#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'project_center.db')

def add_password_column():
    """添加密码列到machines表"""
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查是否已存在password列
        cursor.execute("PRAGMA table_info(machines)")
        columns = cursor.fetchall()
        
        has_password_column = False
        for col in columns:
            if col[1].lower() == 'password':
                has_password_column = True
                break
        
        if has_password_column:
            print("密码列已存在")
        else:
            # 添加密码列
            cursor.execute("ALTER TABLE machines ADD COLUMN password VARCHAR(255)")
            conn.commit()
            print("成功添加密码列")
        
        # 更新ID为1的机器密码
        password = input("请输入机器密码: ").strip()
        if password:
            cursor.execute("UPDATE machines SET password = ? WHERE id = 1", (password,))
            conn.commit()
            print("密码已更新")
        
        # 验证更新
        cursor.execute("SELECT id, name, host, username, password FROM machines WHERE id = 1")
        machine = cursor.fetchone()
        if machine:
            print(f"机器ID: {machine[0]}")
            print(f"机器名称: {machine[1]}")
            print(f"主机地址: {machine[2]}")
            print(f"用户名: {machine[3]}")
            print(f"密码: {machine[4]}")
    
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    add_password_column() 
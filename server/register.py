from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
import os
import bcrypt

base_id=0
def record_exists(conn,table, column, value):
    cursor = conn.cursor()
    cursor.execute(f"SELECT {column} FROM {table} WHERE {column} = ?", (value,))
    exists = cursor.fetchone() is not None
    return exists


# 加密密码hash256
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def register(userId, password):
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # 如果文件夹不存在，则创建
    db = sqlite3.connect(db_path)  # 连接数据库
    cursor = db.cursor()#创建光标
    cursor_id = cursor.execute(
        """
        SELECT id  FROM users 
        """
    )#获取所有的id，用于计算新用户的id
    id = cursor_id.fetchall()#获取所有的id
    print("原有的id:",id)
    if not id:
        new_id = base_id
    else:
        new_id = id[-1][0]+1#新用户的id
    if record_exists(db,"users", "userId",userId):
        db.close()
        return False,"用户名已存在！"
    # print("原有的id:",id) 
    else:
        hashPassword=hash_password(password)
        cursor.execute(
            """
            INSERT INTO users (id, userId, password,role,token) VALUES (?,?,?,?,?)
            """,
            (new_id, userId, hashPassword,"user",None)#默认角色为user
        )#插入新用户的数据
    data = cursor.execute(
        """
        SELECT * FROM users WHERE userId = ? AND password = ?
        """,(userId,password)
    )#查询新用户的数据
    if data is not None:
        db.commit()
        db.close()
        return True,"注册成功！"
    else:
        db.close()
        return False,"注册失败！请检查用户名和密码！"
    #新用户存在则返回true

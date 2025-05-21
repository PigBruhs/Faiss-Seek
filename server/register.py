from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
base_id=0
def register(userId, password):
    db = sqlite3.connect('database.db')#连接数据库
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
    cursor.execute(
        """
        INSERT INTO users (id, userId, password) VALUES (?, ?, ?)
        """,
        (new_id, userId, password)
    )#插入新用户的数据
    data = cursor.execute(
        """
        SELECT * FROM users WHERE userId = ? AND password = ?
        """,(userId,password)
    )#查询新用户的数据
    if data is not None:
        db.commit()
        db.close()
        return True 
    else:
        db.close()
        return False
    #新用户存在则返回true

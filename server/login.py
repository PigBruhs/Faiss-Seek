from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
def login(userId, password):
    #登录的数据库操作函数
    #首先获取用户的id,
    #连接数据库
    db= sqlite3.connect('database.db')
    cursor = db.cursor()
    data = cursor.execute(
        """
        SELECT * FROM users WHERE userId = ? AND password = ?
        """,(userId,password)
    )
    print("登录数据:",data)
    if data is not None:
        return True 
    else:
        print("登录失败")
        return False
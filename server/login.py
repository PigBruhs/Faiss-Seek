from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
import secrets
# 生成token，默认长度为50
def generate_token(length=50):
    return secrets.token_urlsafe(length)[:length]

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
        #登录成功，生成token
        token = generate_token()
        #更新数据库中的token
        cursor.execute(
            """
            UPDATE users SET token = ? WHERE userId = ? AND password = ?
            """,(token,userId,password)
        )
        print("登录成功，生成的token:",token)
        db.commit()
        return True ,token
    else:
        print("登录失败")
        return False,None
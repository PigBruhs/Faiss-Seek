from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
import secrets
import os
import bcrypt
# 验证密码，仅返回是否正确
def verify_password(input_password, hashed_password):
    return bcrypt.checkpw(input_password.encode(), hashed_password.encode())

# 生成token，默认长度为50
def generate_token(length=50):
    return secrets.token_urlsafe(length)[:length]

def login(userId, password):
    #登录的数据库操作函数
    #首先获取用户的id,
    #连接数据库
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # 如果文件夹不存在，则创建
    db = sqlite3.connect(db_path)  # 连接数据库
    cursor = db.cursor()
    data = cursor.execute(
        """
        SELECT * FROM users WHERE userId = ? 
        """,(userId,)
    )
    user = cursor.fetchone()  # 获取查询结果
    hashed_password=user[2]
    print("哈希密码的值为：",hashed_password)
    print("登录数据:",data)
    if data is not None:
        if verify_password(password,hashed_password):
            # 登录成功，生成token
            token = generate_token()
            #更新数据库中的token
            cursor.execute(
                """
                UPDATE users SET token = ? WHERE userId = ? 
                """,(token,userId,)
            )
            print("登录成功，生成的token:",token)
            db.commit()
            db.close()
            #返回登录成功的结果 
            role=user[3]  # 获取用户角色
            print("用户角色:", role)
            return True ,token , role
        else:
             print("密码错误")
             return False,None,None
    else:
        print("没有该用户")
        return False,None,None
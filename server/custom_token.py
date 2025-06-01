#这里存储与token相关的函数，包括检验token是否是当前用户的，刷新token
from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
import os
def isUser(token):
    print("token的数据是:",token)
    if not token:  # 如果 Token 为空，直接返回 False
        print("token验证失败,token是空的")
        return False
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT * FROM users WHERE token = ?
        """,(token,)
    )
    data = cursor.fetchone()
    if data is not None:
        print("token验证成功")
        return True
    else:
        print("token验证失败")
        return False

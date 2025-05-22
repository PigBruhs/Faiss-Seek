#这里存储与token相关的函数，包括检验token是否是当前用户的，刷新token
from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
import os
from app import cnnect_db
def isUser(token):
    db = cnnect_db()
    cursor = db.cursor()
    cursor.execute(
        """"
        SELECT * FROM users WHERE token = ?
        """,(token,)
    )
    data = cursor.fetchone()
    if data is not None:
        return True
    else:
        return False

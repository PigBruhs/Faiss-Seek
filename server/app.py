from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sqlite3
from login import login
from register import register
app = Flask(__name__)
CORS(app)
users_db = {}#数据库连接函数


def init_db(): #使用数据库建模文件初始化数据库，在命令行中使用一次即可。
    db = sqlite3.connect('database.db')#连接数据库
    db.cursor().execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId TEXT NOT NULL,
            password TEXT NOT NULL,
            role TeXT NOT NULL,
            token TEXT
        );
        '''
    )   
    db.commit(),


@app.route('/register', methods=['POST'])
def register_():
    # 打印接收到的原始数据
    data = request.get_json()
    print("收到注册请求数据:", data)
    print(data)#打印接受到的数据，确认数据是什么类型的 
    if not data:
        return jsonify({
            "success": False,
            "message": "请求数据不能为空！"
        }), 400

    else:   
        result=register(data['userId'], data['password']) # 直接返回前端需要的响应格式
        print("注册数据:",result)
        if result[0]:
            return jsonify({
                "success": True,
                "message": result[1] 
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": result[1]
            }), 401

@app.route('/login', methods=['POST'])
def login_():
    # 打印接收到的原始数据
    data = request.get_json()
    print("收到登录请求数据:", data)
    if not data:
        return jsonify({
            "success": False,
            "message": "请求数据不能为空！"
        }), 400

    else:    # 直接返回前端需要的响应格式
      print(data)#打印接受到的数据，确认数据是什么类型的
      result = login(data['userId'], data['password'])
      if result[0]:
          print(data)
          return jsonify({
              "success": True,
              "message": "登录成功！",
              "token": result[1],
              "role": "user",
              "userId": data['userId']
          }), 200
      else:
            return jsonify({
                "success": False,
                "message": "登录失败！请检查用户名和密码！"
            }), 401

@app.before_request#请求前处理函数，通过g这个变量存储数据库连接
def before_request():
    pass

@app.teardown_request
def teardown_request(exception):#请求后处理函数，关闭数据库
   pass

if __name__ == '__main__':
    app.run(host= "0.0.0.0",port=19198, debug=True)
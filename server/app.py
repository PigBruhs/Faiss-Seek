from flask import Flask, request, jsonify,g
from flask_cors import CORS
import os
import sqlite3
from login import login
from register import register
from werkzeug.utils import secure_filename


import sys
sys.path.append("..")
from utils import load_index_base,search_topn

app = Flask(__name__)
CORS(app)
users_db = {}#数据库连接函数
UPLOAD_ADDRESS = 'data/upload'
app.config['UPLOAD_ADDRESS'] = UPLOAD_ADDRESS
if not os.path.exists(UPLOAD_ADDRESS):
    os.makedirs(UPLOAD_ADDRESS)

def cnnect_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db

def init_db(): #使用数据库建模文件初始化数据库，在命令行中使用一次即可。
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # 如果文件夹不存在，则创建
    db = sqlite3.connect(db_path)  # 连接数据库
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

@app.route('/match', methods=['POST']) 
def match():
    # 打印接收到的原始数据
    data = request.get_json()
    print("收到匹配请求数据:", data)
    if not data:
        return jsonify({
            "success": False,
            "message": "请求数据不能为空！"
        }), 400
    else:   
        file = request.files.get('file')
        indices = load_index_base('index_base')#加载索引
        topn = search_topn(indices,file) #topn为结果图片路径
        filename= secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_ADDRESS,filename)
        file.save(file_path)
        if os.path.exists(file_path):
            print("文件存在,路径为",file_path,"文件名为：",filename)
        if file:
            return jsonify({
                "success": True,
                "message": "图片接受成功"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "图片接受失败"
            }), 400
        


@app.before_request#请求前处理函数，通过g这个变量存储数据库连接
def before_request():
    pass

@app.teardown_request
def teardown_request(exception):#请求后处理函数，关闭数据库
   pass

if __name__ == '__main__':
    init_db()#初始化数据库
    app.run(host= "0.0.0.0",port=19198, debug=True)
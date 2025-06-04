from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sys
import os
import sqlite3
import faiss
from flask import send_from_directory
from authService import auth
from tokenService import tokenService
from werkzeug.utils import secure_filename
from typing import Dict
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from flask import Flask, request, jsonify
from dbService import cnnect_db
from imageService import ImageService
from webListService import webListService

app = Flask(__name__)
CORS(app)
users_db = {}#数据库连接函数???
UPLOAD_ADDRESS = 'data/upload'
app.config['UPLOAD_ADDRESS'] = UPLOAD_ADDRESS
if not os.path.exists(UPLOAD_ADDRESS):
    os.makedirs(UPLOAD_ADDRESS)

global imgservice
imgservice= ImageService()

@app.route('/data/base/<path:filename>')
def serve_image(filename):
    return send_from_directory('../data/base', filename)

def load_index_base(index_folder: str) -> Dict[str, faiss.IndexFlatIP]:
    """
    扫描 index_folder 下所有 .index 文件，加载为 Faiss 索引，并以文件名(不含扩展)为 key 返回。
    输入：
        index_folder: 索引文件夹路径
    返回：
        Dict[str, faiss.IndexFlatIP], 文件名到索引的字典
    """
    indices: Dict[str, faiss.IndexFlatIP] = {}
    for file in os.listdir(index_folder):
        if file.lower().endswith(".index"):
            name, _ = os.path.splitext(file)
            path = os.path.join(index_folder, file)
            indices[name] = faiss.read_index(path)
    return indices

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
    
@app.route('/protected', methods=['GET'])
def protected():
    # 检查 Authorization 请求头
    auth_header = request.headers.get('Authorization')
    print("Authorization:", auth_header)
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401
    

    token = auth_header.split(" ")[1]  # 提取 Token
    # 验证 Token（示例代码，实际需要根据你的逻辑验证 Token）
    result=tokenService.IsUser(token)
    if not result:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401
    else:
        # 如果 Token 验证成功
        return jsonify({
            "success": True,
            "message": "Token 验证成功"
        }), 200

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
        result=auth.Register(data['userId'], data['password']) # 直接返回前端需要的响应格式
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
      result = auth.Login(data['userId'], data['password'])  # 调用登录函数
      if result[0]:
          print(data)
          return jsonify({
              "success": True,
              "message": "登录成功！",
              "token": result[1],
              "role": result[2],
              "userId": data['userId']
          }), 200
      else:
            return jsonify({
                "success": False,
                "message": "登录失败！请检查用户名和密码！"
            }), 401
@app.route('/match', methods=['POST'])
def match():
    # 检查 Authorization 请求头
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401

    token = auth_header.split(" ")[1]  # 提取 Token
    result=tokenService.IsUser(token)#验证token
    if not result:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401
   
    # 获取上传的图片
    file = request.files.get('image')
    if not file:
        return jsonify({
            "success": False,
            "message": "未接收到文件"
        }), 400
    result= imgservice.img_search(file, model="vgg16", top_n=5)  # 调用图片搜索服务
    if not result["success"]:
        return jsonify({
            "success": False,
            "message": result["message"],
        }), 401
    elif result.get("result"):
        return jsonify({
            "success": True,
            "message": result["message"],
            "results":result["result"],
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": result["message"],
        }), 400

    #
'''
@app.route('/match', methods=['POST'])
def match():
    # 检查 Authorization 请求头
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401

    token = auth_header.split(" ")[1]  # 提取 Token
    # 验证 Token
    db = cnnect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE token = ?", (token,))
    user = cursor.fetchone()
    db.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401

    # 获取上传的图片
    file = request.files.get('image')
    if not file:
        return jsonify({
            "success": False,
            "message": "未接收到文件"
        }), 400

    # 确保文件名包含扩展名
    filename = secure_filename(file.filename)
    if '.' not in filename:
        filename += '.jpg'  # 默认添加 .jpg 扩展名

    # 保存图片到临时目录
    temp_dir = '../data/temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, filename)
    file.save(file_path)

    # 检查文件是否保存成功
    if not os.path.exists(file_path):
        return jsonify({
            "success": False,
            "message": "文件保存失败"
        }), 500

    # 加载索引并进行匹配
    try:
        indices = load_index_base('../index_base/local')  # 加载索引
        topn = search_topn(indices, image_path=file_path, top_n=5)  # 获取匹配结果
    except Exception as e:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({
            "success": False,
            "message": f"匹配失败: {str(e)}"
        }), 500

    # 删除临时文件
    if os.path.exists(file_path):
        os.remove(file_path)

    # 构造返回的图片 URL
    base_url = request.host_url + "data/base/"
    results = [{"name": name, "url": base_url + name + ".jpg", "score": score} for name, score in topn]

    # 返回匹配结果
    return jsonify({
        "success": True,
        "message": "图片接受成功",
        "results": results  # 返回匹配结果
    }), 200
        '''


@app.route('/getWebList', methods=['POST'])
def getWebList():
    #token验证
    auth_header = request.headers.get('Authorization')
    print("Authorization:", auth_header)
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401

    token = auth_header.split(" ")[1]  # 提取 Token
    # 验证 Token（示例代码，实际需要根据你的逻辑验证 Token）
    tokenResult=tokenService.IsUser(token)
    if not tokenResult:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401
    else:
        # 如果 Token 验证成功
        result = webListService.getWebList()
        print("获取网站的处理结果是：",result)
        return jsonify({
            "success":result['success'],
            "webList":result['webList']
        }),200
  
    
@app.route('/addWeb', methods=['POST'])
def addWeb():
     #token验证
    auth_header = request.headers.get('Authorization')
    print("Authorization:", auth_header)
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401

    token = auth_header.split(" ")[1]  # 提取 Token
    # 验证 Token（示例代码，实际需要根据你的逻辑验证 Token）
    tokenResult=tokenService.IsUser(token)
    if not tokenResult:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401
    else:
        # 如果 Token 验证成功
        print("请求体内容是：",request.data)
        data=request.get_json(force=True)
        print("获取到的网站数据",data)
        if data is not None:
            result=webListService.addWeb(data)
            return jsonify({
                "success":result['success'],
                "message":result['message']
            }),200
        else:
            return jsonify({
                 "success": False,
                 "message": "后端数据接收失败"
            }),401
        

@app.route('/webRequestList', methods=['GET'])
def  webRquestList():
    auth_header = request.headers.get('Authorization')
    print("Authorization:", auth_header)
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401

    token = auth_header.split(" ")[1]  # 提取 Token
    # 验证 Token（示例代码，实际需要根据你的逻辑验证 Token）
    tokenResult=tokenService.isAdmin(token)
    if not tokenResult:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401
    else:
        # 如果 Token 验证成功
        result=webListService.webRequestList()
        print("获取的结果是：",result)
        if result['success']:
            return jsonify({
            "success": result["success"],
            "webRequestList": result['webRequestList']
        }), 200
        else:
            return jsonify({
            "success": result["success"],
            "webRequestList": result['webRequestList']
        }), 400
            
@app.route('/approveWeb', methods=['POST'])
def approveWeb():
    auth_header = request.headers.get('Authorization')
    print("Authorization:", auth_header)
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "缺少或无效的 Token"
        }), 401

    token = auth_header.split(" ")[1]  # 提取 Token
    # 验证 Token（示例代码，实际需要根据你的逻辑验证 Token）
    tokenResult=tokenService.isAdmin(token)
    if not tokenResult:
        return jsonify({
            "success": False,
            "message": "Token 无效或已过期"
        }), 401
    else:
        # 如果 Token 验证成功
        data=request.get_json()
        print("获取到的数据：",data)
        result=webListService.approve(data)
        print("获取的结果是：",result)
        if result['success']:
            return jsonify({
            "success": result["success"],
            "message": result['message']
        }), 200
        else:
            return jsonify({
            "success": result["success"],
            "message": result['message']
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
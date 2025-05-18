from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


users_db = {}


@app.route('/register', methods=['POST'])
def register():
    # 打印接收到的原始数据
    data = request.get_json()
    print("收到注册请求数据:", data)



    # 直接返回前端需要的响应格式
    return jsonify({
        "success": True,
        "message": "注册成功！"
    }), 200


@app.route('/login', methods=['POST'])
def login():
    # 打印接收到的原始数据
    data = request.get_json()
    print("收到登录请求数据:", data)

    data = request.get_json()

    # 直接返回前端需要的响应格式
    return jsonify({
        "success": True,
        "message": "登录成功！",
        "userId": data.get('userId')
    }), 200


if __name__ == '__main__':
    app.run(port=19198, debug=True)
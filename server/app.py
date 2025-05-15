from flask import Flask
from flask_cors import CORS
from config import Config
from routes.auth import auth_bp
from routes.gameManage import gameManage_bp
from database.database import Database
from database.schema import Schema

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    
    # 初始化数据库
    Database.initialize_db()
    
    # 创建所有表
    schema = Schema()
    schema.create_tables()
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(gameManage_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, port=Config.SERVER_PORT)
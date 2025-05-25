
# 答而多图图

这是一个基于 Flask 后端和 Vue 3 前端的全栈项目，支持用户注册、登录、图片上传与匹配等功能。

## 项目结构

答而多图图
├── server/                # 后端代码
│   ├── app.py             # Flask 主程序
│   ├── Test.py            # 爬虫脚本
│   ├── requirements.txt   # 后端依赖
│   └── init.py            # 数据库初始化脚本
├── src/                   # 前端代码
│   ├── main.js            # Vue 主入口
│   ├── components/        # Vue 组件
│   │   ├── LoginPage.vue  # 登录页面
│   │   ├── RegisterPage.vue # 注册页面
│   │   ├── Home.vue       # 主页
│   │   └── scomponents/   # 子组件
│   │       ├── LoginComponent.vue  # 登录组件
│   │       ├── RegisterComponent.vue # 注册组件
│   │       ├── HeaderTop.vue        # 顶部导航栏
│   │       └── HeaderTopAfterLogin.vue # 登录后的顶部导航栏
├── utils/                 # 工具模块
│   ├── index_base.py      # 索引加载工具
│   ├── index_search.py    # 索引搜索工具
│   └── other_utils.py     # 其他工具
├── data/                  # 数据存储目录
│   ├── base/              # 索引图片
│   ├── temp/              # 临时文件
│   ├── search/            # 搜索结果
│   └── pixnio_image_urls.txt # 爬取的图片链接
├── docs/                  # 文档
│   ├── 前后端交互文档.md   # 前后端接口说明
│   └── 软件需求规约/       # 软件需求文档
├── scripts/               # 启动脚本
│   └── qstart.bat         # 快速启动脚本
├── index_base/            # 索引文件
│   ├── 001_accordion_image_0002.index
│   ├── 002_anchor_image_0003.index
│   └── ...
├── pretrained/            # 预训练模型
├── public/                # 公共资源
│   └── favicon.ico        # 网站图标
├── package.json           # 前端依赖
├── vite.config.js         # Vite 配置
└── README.md              # 项目说明


## 环境要求

- **后端**：
  - Python 3.8 或更高版本
  - pip
- **前端**：
  - Node.js 16 或更高版本
  - npm

## 快速启动

### 1. 安装依赖

运行 `scripts/qstart.bat` 脚本，自动完成以下操作：

- 检查并安装 Python 和 Node.js 环境。
- 创建 Python 虚拟环境并安装后端依赖（`server/requirements.txt`）。
- 安装前端依赖（`npm install`）。

### 2. 启动项目

`qstart.bat` 脚本会自动启动：

- 后端服务（运行 `server/app.py`）。
- 前端开发服务器（运行 `npm run dev`）。

### 3. 访问项目

启动完成后：

- 前端访问地址：[http://127.0.0.1:14514](http://127.0.0.1:14514)
- 后端访问地址：[http://127.0.0.1:19198](http://127.0.0.1:19198)

## 手动操作

如果需要手动启动项目，请按照以下步骤操作：

### 后端


1. 进入 `server` 目录：

```sh
cd server
```


2. 创建虚拟环境并安装依赖：

python-mvenv.venv

.venv\Scripts\activate

pipinstall-rrequirements.txt


3. 初始化数据库

pythoninit.py


4. 启动后端服务

pythonapp.py

### 前端


1. 安装依赖

npm install axios
npm install --save-dev @arco-design/web-vue
npm install -D unplugin-vue-components unplugin-auto-import
npm install vite-plugin-style-import -save-dev
npm install consola --save-dev
npm install vue-router


2. 启动开发服务器

npmrundev

## 功能说明


### 用户注册与登录

* **注册接口** ：`POST /register`
* **登录接口** ：`POST /login`

### 图片上传与匹配

* **上传接口** ：`POST /match`
* **匹配结果** ：返回匹配图片的 URL 和相似度分数。

### Token 验证

* **验证接口** ：`GET /protected`

## 注意事项

* 确保 `data/base` 和 `data/temp` 目录存在，且具有读写权限。
* 如果需要修改前端与后端的端口，请分别修改 `vite.config.js` 和 `server/app.py`。

## 常见问题

1. **Python 或 Node.js 未安装**
   请确保已安装 Python 和 Node.js，并将其添加到系统环境变量中。
2. **依赖安装失败**
   检查网络连接，或尝试使用国内镜像源：


pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

npm instal l--registry=https://registry.npm.taobao.org


**3. 端口冲突**
如果端口被占用，请修改 `vite.config.js` 和 `server/app.py` 中的端口配置。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目。

GitHub地址：https://github.com/PigBruhs/Faiss-Seek

## 许可证

本项目基于 MIT 许可证开源。 ```

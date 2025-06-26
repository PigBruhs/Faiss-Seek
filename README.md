
# 答而多图图

这是一个基于 Flask 后端和 Vue 3 前端的全栈图片搜索匹配系统，支持用户注册、登录、图片上传与匹配、图源管理等功能。

## 项目结构

```

e:\软件实训开发\答而多图图

├── server/                    # 后端代码目录

│   ├── app.py                 # Flask 主应用程序

│   ├── authService.py         # 用户认证服务

│   ├── tokenService.py        # Token 验证服务

│   ├── imageService.py        # 图片处理服务

│   ├── webListService.py      # 图源管理服务

│   ├── dbService.py           # 数据库连接服务

│   ├── Test.py                # 爬虫测试脚本

│   ├── requirements.txt       # Python 依赖列表

│   └── database/              # 数据库文件目录

├── src/                       # 前端代码目录

│   ├── main.js                # Vue 应用入口

│   ├── App.vue                # 根组件

│   ├── components/            # Vue 组件

│   │   ├── LoginPage.vue      # 登录页面

│   │   ├── RegisterPage.vue   # 注册页面

│   │   ├── Home.vue           # 主页

│   │   └── scomponents/       # 子组件目录

│   │       ├── LoginComponent.vue         # 登录组件

│   │       ├── RegisterComponent.vue      # 注册组件

│   │       ├── HeaderTop.vue              # 顶部导航栏

│   │       ├── HeaderTopAfterLogin.vue    # 登录后导航栏

│   │       ├── AddWeb.vue                 # 添加图源组件

│   │       ├── SelectWeb.vue              # 选择图源组件

│   │       └── ImageUpLoader.vue          # 图片上传组件

│   ├── assets/                # 静态资源

│   │   ├── base.css           # 基础样式

│   │   ├── main.css           # 主样式

│   │   ├── fonts/             # 字体文件

│   │   └── images/            # 图片资源

│   └── router/                # 路由配置

├── utils/                     # 工具模块

│   ├── crawler.py             # 网络爬虫工具

│   ├── index_base.py          # 索引构建工具

│   ├── index_search.py        # 索引搜索工具

│   └── feature_extraction.py # 特征提取工具

├── data/                      # 数据存储目录

│   ├── base/                  # 本地图片库

│   ├── search/                # 搜索结果缓存

│   ├── temp/                  # 临时文件

│   ├── upload/                # 上传文件目录

│   └── pixnio_image_urls.txt  # 爬取的图片链接

├── crawled_images/            # 爬虫下载的图片

│   ├── hippopx/               # 各个网站的图片

│   ├── pexels/

│   ├── pixabay/

│   ├── pixnio/

│   ├── unsplash/

│   └── viewofchina/

├── index_base/                # 索引文件存储

│   ├── local/                 # 本地图片索引

│   └── url/                   # 网络图片索引

├── pretrained/                # 预训练模型

├── docs/                      # 文档目录

│   ├── 前后端交互文档.md       # API 接口文档

│   └── 软件需求规约/           # 需求文档

├── scripts/                   # 脚本目录

│   └── qstart.bat             # 快速启动脚本

├── public/                    # 公共资源

├── __pycache__/               # Python 缓存文件

├── .vscode/                   # VSCode 配置

├── chromedriver.exe           # Chrome 驱动（爬虫用）

├── debug.bat                  # 调试脚本

├── package.json               # 前端依赖配置

├── vite.config.js             # Vite 构建配置

├── jsconfig.json              # JavaScript 配置

├── .gitignore                 # Git 忽略文件

└── README.md                  # 项目说明文档

```

## 核心功能模块

### 1. 后端服务 (server/)

-**app.py**: Flask 主应用，包含所有 API 路由定义

- 用户注册/登录 (`/register`, `/login`)
- Token 验证 (`/protected`)
- 图片匹配 (`/match`)
- 图源管理 (`/getWebList`, `/addWeb`, `/approveWeb`, `/rejectWeb`, `/deleteWeb`)
- 本地索引更新 (`/updateLocal`)

-**认证系统**: `authService.py` + `tokenService.py` 提供完整的用户认证流程

-**图片服务**: `imageService.py` 处理图片上传、特征提取、相似度匹配

-**图源管理**: `webListService.py` 管理图片网站源的增删改查

-**数据库**: `dbService.py` 提供 SQLite 数据库连接和操作

### 2. 前端界面 (src/)

-**Vue 3 框架**: 使用 Arco Design 组件库

-**页面组件**:

  -`LoginPage.vue` / `RegisterPage.vue`: 用户认证页面

  -`Home.vue`: 主页面，包含图片上传和搜索功能

-**子组件**:

  -`AddWeb.vue`: 图源添加和管理（支持用户提交和管理员审核）

  -`SelectWeb.vue`: 图源选择和删除

  -`ImageUpLoader.vue`: 图片上传组件

-**样式**: 自定义字体和毛玻璃效果设计

### 3. 图片处理系统 (utils/)

-**爬虫模块**: 支持多线程爬取多个图片网站

-**索引系统**: 构建和搜索图片特征索引

-**特征提取**: 支持多种深度学习模型:

- ResNet50
- VGG16
- ViT-B-16

### 4. 数据存储

-**本地图片库**: `data/base/` 存储本地图片资源

-**索引文件**: `index_base/` 存储不同模型的图片特征索引

-**爬虫数据**: `crawled_images/` 按网站分类存储爬取的图片

-**数据库**: SQLite 存储用户信息和图源管理数据

## 技术栈

**后端:**

- Flask (Python Web 框架)
- SQLite (数据库)
- PIL/Pillow (图片处理)
- PyTorch/TensorFlow (深度学习模型)
- FAISS (高效相似性搜索)

**前端:**

- Vue 3 (前端框架)
- Vite (构建工具)
- Arco Design (UI 组件库)
- Axios (HTTP 客户端)

**其他:**

- Selenium + ChromeDriver (网页自动化爬虫)
- JWT (用户认证)

## 环境要求

-**后端**：

- Python 3.8 或更高版本
- pip

-**前端**：

- Node.js 16 或更高版本
- npm

## 快速启动

### 1. 安装依赖

运行 `scripts/qstart.bat` 脚本，自动完成以下操作：

- 检查并安装 Python 和 Node.js 环境
- 创建 Python 虚拟环境并安装后端依赖（`server/requirements.txt`）
- 安装前端依赖（`npm install`）
- 下载预训练模型（vit16,resnet50,vgg16）并放入/pretrained 文件夹下
- 下载与本地 Chrome 浏览器版本匹配的 ChromeDriver。
- 以及其他需要手动安装的依赖

### 2. 启动项目

`qstart.bat` 脚本会自动启动：

- 后端服务（运行 `server/app.py`）
- 前端开发服务器（运行 `npm run dev`）

### 3. 访问项目

启动完成后：

- 前端访问地址：[http://127.0.0.1:14514](http://127.0.0.1:14514)
- 后端访问地址：[http://127.0.0.1:19198](http://127.0.0.1:19198)

## 手动操作

如果需要手动启动项目，请按照以下步骤操作：

### 后端

1. 进入 `server` 目录：

```sh

cdserver

```

2. 创建虚拟环境并安装依赖：

```sh

python-mvenv.venv

.venv\Scripts\activate

pipinstall-rrequirements.txt

```

3. 初始化数据库（首次运行）：

```sh

pythonapp.py  # 会自动调用 init_db()

```

4. 启动后端服务：

```sh

pythonapp.py

```

### 前端

1. 安装依赖：

```sh

npminstall

```

2. 启动开发服务器：

```sh

npmrundev

```

## 功能说明

### 用户认证

-**注册接口**: `POST /register` - 用户注册

-**登录接口**: `POST /login` - 用户登录，返回 JWT Token

-**Token 验证**: `GET /protected` - 验证用户身份

### 图片搜索匹配

-**上传接口**: `POST /match` - 上传图片进行相似度搜索

-**支持多种模型**: ResNet50、VGG16、ViT-B-16

-**返回结果**: 匹配图片的 URL 和相似度分数

### 图源管理

-**获取图源**: `POST /getWebList` - 获取可用图源列表

-**添加图源**: `POST /addWeb` - 用户提交新图源（需管理员审核）

-**管理员功能**:

  -`GET /webRequestList` - 获取待审核图源

  -`POST /approveWeb` - 审核通过图源

  -`POST /rejectWeb` - 拒绝图源申请

  -`POST /deleteWeb` - 删除图源

  -`GET /updateLocal` - 更新本地图源索引

### 权限管理

-**用户角色**: `user`（普通用户）、`admin`（管理员）

-**Token 验证**: 所有需要认证的接口都需要在请求头中携带 Bearer Token

-**管理员权限**: 图源审核、删除、索引更新等功能仅限管理员

## 注意事项

- 确保 `data/base`、`data/temp`、`data/upload` 目录存在，且具有读写权限
- Chrome 浏览器和 ChromeDriver 版本需要匹配（爬虫功能）
- 如果需要修改端口：

  - 前端端口：修改 `vite.config.js`
  - 后端端口：修改 `server/app.py` 中的 `app.run()` 参数
- 首次使用需要初始化数据库，会自动创建用户表和图源表

## 常见问题

1.**Python 或 Node.js 未安装**

   请确保已安装 Python 和 Node.js，并将其添加到系统环境变量中。

2.**依赖安装失败**

   检查网络连接，或尝试使用国内镜像源：

```sh

   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

   npm install --registry=https://registry.npm.taobao.org

```

3.**端口冲突**

   如果端口被占用，请修改 `vite.config.js` 和 `server/app.py` 中的端口配置。

4.**ChromeDriver 版本不匹配**

   请下载与本地 Chrome 浏览器版本匹配的 ChromeDriver。

5.**数据库初始化失败**

   确保 `server/database/` 目录存在写入权限。

6.模型文件缺失，请去对应模型的官网下载模型并放入/pretrained 文件夹下

## API 文档

详细的前后端交互文档请参考：[`docs/前后端交互文档.md`](docs/前后端交互文档.md)

## 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目。

GitHub地址：https://github.com/PigBruhs/Faiss-Seek

## 许可证

本项目基于 MIT 许可证开源。

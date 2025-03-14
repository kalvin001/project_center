# 项目管理中心 (Project Center)

项目管理中心是一个用于管理代码项目完整生命周期的应用程序。它提供了项目的创建、上传、更新、管理和部署功能。

## 功能特点

- 用户认证和授权
- 项目CRUD操作
- 项目文件上传和下载
- 项目部署管理
- 美观的用户界面

## 技术栈

### 后端

- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- UV包管理

### 前端

- React 18
- TypeScript
- Ant Design 5
- Zustand (状态管理)
- Axios (HTTP客户端)
- Vite (构建工具)
- PNPM (包管理器)

## 快速开始

### 系统要求

- Windows 10+
- Python 3.8+
- Node.js 16+
- npm 7+

### 一键启动

项目提供了一键启动脚本，可以自动安装依赖并启动前后端服务：

```bash
# 在项目根目录下运行
start_all.bat
```

启动后可以访问：
- 前端: http://localhost:8012
- 后端API: http://localhost:8011
- API文档: http://localhost:8011/api/docs

### 手动启动

如果需要手动启动，可以按照以下步骤操作：

#### 后端

```bash
cd backend

# 安装UV (如果尚未安装)
pip install uv

# 创建虚拟环境并安装依赖
uv venv
uv pip install -e .

# 启动后端服务
python run.py
```

#### 前端

```bash
cd frontend

# 安装PNPM (如果尚未安装)
npm install -g pnpm

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

## 项目结构

```
project_center/
├── backend/             # 后端代码
│   ├── app/             # 应用代码
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心功能
│   │   ├── db/          # 数据库
│   │   ├── models/      # 数据模型
│   │   └── schemas/     # 数据模式
│   ├── projects/        # 项目存储目录
│   └── run.py           # 启动脚本
├── frontend/            # 前端代码
│   ├── public/          # 静态资源
│   └── src/             # 源代码
│       ├── components/  # 组件
│       ├── pages/       # 页面
│       ├── services/    # 服务
│       ├── stores/      # 状态管理
│       └── utils/       # 工具函数
└── start_all.bat        # 一键启动脚本
```

## 使用说明

1. 注册/登录系统
2. 创建新项目或查看现有项目
3. 上传项目文件（ZIP格式）
4. 管理项目信息和部署配置
5. 部署项目到指定服务器

## 许可证

MIT 
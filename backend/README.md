# 项目管理中心后端

基于FastAPI和SQLite的项目管理中心后端服务。

## 功能

- 用户认证和授权
- 项目CRUD操作
- 项目文件上传和下载
- 项目部署管理

## 技术栈

- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- UV包管理

## 安装

### 使用UV创建虚拟环境并安装依赖

```bash
# 安装UV (如果尚未安装)
pip install uv

# 创建虚拟环境并安装依赖
uv venv
uv pip install -e .
```

## 运行

```bash
# 启动开发服务器
python run.py
```

服务器将在 http://localhost:8011 运行，API文档可以在 http://localhost:8011/api/docs 访问。

## API文档

启动服务器后，可以通过以下URL访问API文档：

- Swagger UI: http://localhost:8011/api/docs
- ReDoc: http://localhost:8011/api/redoc

## 环境变量

可以通过创建`.env`文件或设置系统环境变量来配置应用程序，例如：

```
DEBUG=False
SECRET_KEY=your_secret_key_here
```

关键配置项见`app/core/config.py`文件。 
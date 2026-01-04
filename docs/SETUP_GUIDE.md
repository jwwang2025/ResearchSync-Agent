# ResearchSync-Agent 前后端分离项目设置指南

## 概述

本项目已重构为前后端分离架构：
- **后端**: FastAPI (Python)
- **前端**: React + TypeScript + Vite

## 前置要求

### 后端
- Python 3.9+
- pip 或 conda

### 前端
- Node.js 18+
- npm/yarn/pnpm

## 快速开始

### 1. 后端设置

#### 安装依赖

```bash
# 安装基础依赖（如果还没有）
pip install -r requirements.txt

# 安装 API 相关依赖
pip install -r requirements-api.txt
```

#### 配置环境变量

确保 `.env` 文件已配置（参考项目根目录的 `.env.example`）：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
TAVILY_API_KEY=your_tavily_key_here  # 可选
MCP_SERVER_URL=your_mcp_url  # 可选
MCP_API_KEY=your_mcp_key  # 可选
```

#### 启动后端服务

```bash
# 方式 1: 使用 uvicorn 直接运行
cd backend/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 使用 Python 模块运行
python -m backend.api.main

# 方式 3: 从项目根目录运行
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

#### 验证后端

访问以下 URL 验证后端是否正常运行：
- API 文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/health

### 2. 前端设置

#### 安装依赖

```bash
cd frontend
npm install
# 或
yarn install
# 或
pnpm install
```

#### 配置环境变量（可选）

创建 `frontend/.env` 文件（如果默认值不适用）：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

#### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

前端应用将在 `http://localhost:3000` 启动。

### 3. 访问应用

打开浏览器访问: http://localhost:3000

## 开发指南

### 后端开发

#### API 路由结构

```
backend/api/
├── main.py              # FastAPI 应用入口
├── routes/              # 路由模块
│   ├── research.py      # 研究任务 REST API
│   ├── websocket.py     # WebSocket 实时通信
│   └── config.py        # 配置管理 API
└── models/              # Pydantic 模型
    └── research.py      # 研究相关数据模型
```

#### 添加新的 API 端点

1. 在 `backend/api/routes/` 中创建或修改路由文件
2. 在 `backend/api/main.py` 中注册路由
3. 在 `backend/api/models/` 中定义相应的 Pydantic 模型

#### WebSocket 消息格式

参考 `ARCHITECTURE.md` 中的 WebSocket 消息格式说明。

### 前端开发

#### 项目结构

```
frontend/src/
├── components/          # React 组件
│   └── Research/        # 研究相关组件
├── pages/               # 页面组件（待实现）
├── services/            # API 服务
│   ├── api.ts           # REST API 客户端
│   └── websocket.ts     # WebSocket 客户端
├── hooks/               # 自定义 Hooks
│   └── useWebSocket.ts  # WebSocket Hook
├── types/               # TypeScript 类型定义
└── App.tsx              # 根组件
```

#### 添加新组件

1. 在 `frontend/src/components/` 中创建组件
2. 使用 TypeScript 和 Ant Design 组件
3. 通过 `services/api.ts` 或 `services/websocket.ts` 与后端通信

#### 状态管理

当前使用 React Hooks 进行状态管理。如需更复杂的状态管理，可以考虑：
- Zustand（推荐，轻量）
- Redux Toolkit
- Context API

## 生产部署

### 后端部署

#### 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn
gunicorn backend.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 使用 Docker（推荐）

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

COPY . .

CMD ["gunicorn", "backend.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 前端部署

#### 构建生产版本

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/` 目录。

#### 使用 Nginx 部署

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 常见问题

### 1. 后端启动失败

- 检查 Python 版本（需要 3.9+）
- 检查依赖是否安装完整
- 检查 `.env` 文件配置是否正确
- 检查端口 8000 是否被占用

### 2. 前端无法连接后端

- 检查后端是否正常运行
- 检查 `frontend/.env` 中的 API URL 配置
- 检查浏览器控制台的错误信息
- 检查 CORS 配置（后端 `main.py` 中的 CORS 设置）

### 3. WebSocket 连接失败

- 检查后端 WebSocket 路由是否正确
- 检查防火墙设置
- 检查代理配置（如果使用反向代理）

### 4. 研究任务无法启动

- 检查 LLM API 密钥配置
- 检查后端日志中的错误信息
- 检查网络连接

## 下一步

1. **完善前端 UI**: 添加更多组件和页面
2. **添加任务历史**: 实现任务历史查看功能
3. **添加用户认证**: 如果需要多用户支持
4. **添加数据库**: 持久化任务和报告数据
5. **添加任务队列**: 使用 Celery 处理长时间任务
6. **优化性能**: 添加缓存、优化查询等

## 参考文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Ant Design 文档](https://ant.design/)
- [Vite 文档](https://vitejs.dev/)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 架构设计文档


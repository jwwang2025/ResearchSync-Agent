# ResearchSync-Agent 后端

基于 FastAPI 的多智能体研究系统后端服务。

## 快速启动

### 前置要求
- Python 3.9+
- 已安装项目依赖

### 环境配置
确保项目根目录有 `.env` 文件，并配置以下环境变量：
```env
LLM_PROVIDER=deepseek  # 或 openai, claude, gemini
DEEPSEEK_API_KEY=your_api_key_here
TAVILY_API_KEY=your_tavily_key_here  # 可选，用于网络搜索
MCP_SERVER_URL=your_mcp_url  # 可选
MCP_API_KEY=your_mcp_key  # 可选
REDIS_URL=redis://localhost:6379  # 可选，用于分布式任务
```

### 启动方式

#### 方式 1: 直接启动（推荐用于开发）
```bash
python backend/main.py
```

#### 方式 2: 使用 uvicorn
```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 方式 3: 使用 Python 模块
```bash
python -m backend.api.main
```

### 环境变量控制

启动时可通过环境变量控制行为：
```bash
# 启用自动重载（开发环境）
export DEV_RELOAD=true

# 指定主机和端口
export HOST=127.0.0.1
export PORT=8001

# 启动服务
python backend/main.py
```

### 验证服务

启动后访问以下地址验证：
- **API 文档**: http://localhost:8000/api/docs
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/
http://127.0.0.1:8000


### 生产部署

#### 使用 Gunicorn
```bash
pip install gunicorn
gunicorn backend.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 使用 Docker
```bash
docker build -t researchsync-backend .
docker run -p 8000:8000 researchsync-backend
```

## 项目结构

```
backend/
├── api/                 # FastAPI 应用
│   ├── main.py         # 应用入口
│   ├── routes/         # API 路由
│   └── models/         # 数据模型
├── agents/             # 多智能体系统
├── llm/                # LLM 提供商集成
├── tools/              # 工具集成
├── workflow/           # LangGraph 工作流
└── utils/              # 工具函数
```

## 开发说明

- API 基于 FastAPI，支持自动生成 OpenAPI 文档
- 支持 WebSocket 实时通信
- 集成多种 LLM 提供商 (OpenAI, Claude, DeepSeek, Gemini)
- 支持外部工具集成 (Tavily 搜索, ArXiv, MCP)

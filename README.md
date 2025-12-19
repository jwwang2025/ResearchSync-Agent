# ResearchSync-Agent

基于 LangGraph 的多智能体研究系统，支持前后端分离架构。

## 项目简介

ResearchSync-Agent 是一个智能研究助手系统，通过多个协作的 AI 智能体（Coordinator、Planner、Researcher、Rapporteur）自动完成研究任务，生成高质量的研究报告。

## 架构

### 当前支持两种架构

1. **CLI 架构**（原有）
   - 命令行界面
   - 适合脚本和自动化场景

2. **前后端分离架构**（新增）✨
   - 后端：FastAPI (Python)
   - 前端：React + TypeScript + Vite
   - 适合 Web 应用和用户交互

## 快速开始

### CLI 模式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 CLI
python main.py
```

### 前后端分离模式

#### 后端

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-api.txt

# 启动后端服务
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 启动，API 文档在 http://localhost:8000/api/docs

#### 前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:3000 启动

详细设置请参考 [SETUP_GUIDE.md](./SETUP_GUIDE.md)

## 项目结构

```
ResearchSync-Agent/
├── backend/              # 后端代码
│   ├── api/             # FastAPI 应用（前后端分离）
│   ├── agents/          # 智能体模块
│   ├── llm/            # LLM 接口
│   ├── tools/          # 搜索工具
│   ├── workflow/       # 工作流引擎
│   └── cli/            # CLI 接口
├── frontend/           # 前端应用（前后端分离）
├── outputs/           # 输出报告目录
└── test/              # 测试文件
```

## 功能特性

- 🤖 **多智能体协作** - Coordinator、Planner、Researcher、Rapporteur 四个智能体协作完成研究
- 🔍 **多源搜索** - 支持 Tavily、ArXiv、MCP 等多种数据源
- 📊 **智能规划** - 自动生成研究计划，支持人工审批
- 📝 **报告生成** - 自动生成 Markdown 或 HTML 格式的研究报告
- 🌐 **Web 界面** - 现代化的 Web 界面，实时显示研究进度
- 🔄 **实时通信** - WebSocket 支持实时状态更新和流式输出
- 🔌 **多 LLM 支持** - 支持 OpenAI、Claude、Gemini、DeepSeek 等多种 LLM

## 技术栈

### 后端
- Python 3.9+
- LangGraph / LangChain
- FastAPI
- WebSocket

### 前端
- React 18+
- TypeScript
- Vite
- Ant Design

## 配置

创建 `.env` 文件：

```env
# LLM 配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here

# 搜索工具配置（可选）
TAVILY_API_KEY=your_tavily_key_here
MCP_SERVER_URL=your_mcp_url
MCP_API_KEY=your_mcp_key

# 工作流配置
MAX_ITERATIONS=5
AUTO_APPROVE_PLAN=false
OUTPUT_DIR=./outputs
```

## 文档

- [架构设计文档](./ARCHITECTURE.md) - 前后端分离架构详细设计
- [设置指南](./SETUP_GUIDE.md) - 详细的设置和启动指南
- [迁移总结](./MIGRATION_SUMMARY.md) - 前后端分离迁移总结

## 开发

### 后端开发

```bash
# 运行后端开发服务器（自动重载）
python -m uvicorn backend.api.main:app --reload

# 运行 CLI
python main.py
```

### 前端开发

```bash
cd frontend
npm run dev
```

## 许可证

[添加您的许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

[添加您的联系方式]


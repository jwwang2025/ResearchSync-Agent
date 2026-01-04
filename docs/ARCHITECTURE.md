# ResearchSync-Agent 前后端分离架构设计

## 技术栈推荐

### 后端（API 服务）

#### 核心框架
- **FastAPI** - 现代、快速的 Python Web 框架
  - 异步支持，适合长时间运行的研究任务
  - 自动生成 OpenAPI/Swagger 文档
  - 类型提示和验证（Pydantic）
  - 与现有 Python 代码库无缝集成

#### 实时通信
- **WebSocket** (FastAPI WebSocket 支持)
  - 流式输出研究进度
  - 实时状态更新
  - 双向通信（前端可发送审批反馈）

#### 任务管理（可选，用于长时间任务）
- **Celery** + **Redis**
  - 异步任务队列
  - 任务状态跟踪
  - 支持任务取消和重试

#### 数据存储
- **PostgreSQL** (可选)
  - 存储研究任务历史
  - 用户数据（如需要多用户支持）
  - 研究报告归档
- **Redis**
  - 缓存
  - 会话管理
  - Celery broker（如使用）

#### 认证授权（可选）
- **JWT** (python-jose)
  - 用户认证
  - API 安全

### 前端（Web 应用）

#### 核心框架
- **React 18+** + **TypeScript**
  - 组件化开发
  - 类型安全
  - 丰富的生态系统
  - 或 **Vue 3** + **TypeScript**（更轻量，学习曲线平缓）

#### UI 框架
- **Ant Design** (推荐)
  - 企业级 UI 组件
  - 中文文档完善
  - 丰富的组件（表格、表单、进度条等）
  - 或 **Material-UI** / **shadcn/ui**

#### 状态管理
- **Zustand** (推荐，轻量)
  - 简单易用
  - 或 **Redux Toolkit**（更复杂但功能强大）
  - 或 **Pinia**（如果使用 Vue）

#### 实时通信
- **WebSocket 客户端**
  - 原生 WebSocket API
  - 或 **Socket.io-client**（如果需要更多功能）

#### 构建工具
- **Vite**
  - 快速开发服务器
  - 优化的生产构建

#### 其他工具库
- **react-markdown** / **marked** - Markdown 渲染
- **recharts** / **Chart.js** - 数据可视化（研究进度）
- **react-router-dom** - 路由管理
- **axios** / **fetch** - HTTP 请求
- **dayjs** - 日期处理

## 项目结构

```
ResearchSync-Agent/
├── backend/                    # 后端（Python）
│   ├── api/                   # FastAPI 应用
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── routes/            # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── research.py    # 研究任务相关路由
│   │   │   ├── tasks.py       # 任务管理路由
│   │   │   └── websocket.py   # WebSocket 路由
│   │   ├── models/            # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── research.py    # 研究相关模型
│   │   │   └── task.py        # 任务模型
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── research_service.py
│   │   │   └── workflow_service.py
│   │   └── dependencies.py    # 依赖注入
│   ├── agents/                # 现有智能体（保持不变）
│   ├── llm/                   # 现有 LLM 模块（保持不变）
│   ├── tools/                 # 现有工具（保持不变）
│   ├── workflow/              # 现有工作流（保持不变）
│   └── utils/                 # 现有工具（保持不变）
│
├── frontend/                  # 前端（React/Vue）
│   ├── src/
│   │   ├── components/        # React 组件
│   │   │   ├── Research/
│   │   │   │   ├── ResearchForm.tsx
│   │   │   │   ├── ResearchProgress.tsx
│   │   │   │   ├── PlanReview.tsx
│   │   │   │   └── ReportViewer.tsx
│   │   │   ├── Layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   └── Common/
│   │   │       ├── Loading.tsx
│   │   │       └── ErrorBoundary.tsx
│   │   ├── pages/             # 页面组件
│   │   │   ├── Home.tsx
│   │   │   ├── Research.tsx
│   │   │   └── History.tsx
│   │   ├── stores/            # 状态管理
│   │   │   ├── researchStore.ts
│   │   │   └── taskStore.ts
│   │   ├── services/          # API 服务
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── researchService.ts
│   │   ├── hooks/             # 自定义 Hooks
│   │   │   ├── useWebSocket.ts
│   │   │   └── useResearch.ts
│   │   ├── types/             # TypeScript 类型定义
│   │   │   ├── research.ts
│   │   │   └── task.ts
│   │   ├── utils/             # 工具函数
│   │   └── App.tsx            # 根组件
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── requirements.txt           # Python 依赖
├── requirements-api.txt       # API 专用依赖（可选）
└── README.md
```

## API 设计

### RESTful API

#### 1. 研究任务管理
```
POST   /api/v1/research/start          # 启动研究任务
GET    /api/v1/research/{task_id}      # 获取任务状态
DELETE /api/v1/research/{task_id}      # 取消任务
GET    /api/v1/research/history        # 获取历史任务列表
```

#### 2. WebSocket
```
WS     /ws/research/{task_id}          # 研究任务实时流
```

#### 3. 配置管理
```
GET    /api/v1/config                  # 获取配置信息
PUT    /api/v1/config                  # 更新配置
GET    /api/v1/models/{provider}       # 获取可用模型列表
```

### WebSocket 消息格式

#### 客户端 -> 服务端
```json
{
  "type": "approve_plan",
  "task_id": "xxx",
  "approved": true,
  "feedback": "optional feedback"
}
```

#### 服务端 -> 客户端
```json
{
  "type": "status_update",
  "task_id": "xxx",
  "step": "planning",
  "data": {...}
}

{
  "type": "plan_ready",
  "task_id": "xxx",
  "plan": {...}
}

{
  "type": "progress",
  "task_id": "xxx",
  "iteration": 1,
  "max_iterations": 5,
  "current_task": "..."
}

{
  "type": "report_ready",
  "task_id": "xxx",
  "report": "..."
}

{
  "type": "error",
  "task_id": "xxx",
  "message": "..."
}
```

## 数据流

1. **用户提交研究问题**
   - 前端：POST `/api/v1/research/start`
   - 后端：创建任务，返回 task_id

2. **建立 WebSocket 连接**
   - 前端：连接 `ws://host/ws/research/{task_id}`
   - 后端：开始研究工作流，流式发送状态更新

3. **研究计划审批**
   - 后端：发送 `plan_ready` 消息
   - 前端：显示计划，等待用户审批
   - 前端：通过 WebSocket 发送审批结果
   - 后端：继续或修改计划

4. **研究执行**
   - 后端：流式发送进度更新
   - 前端：实时显示进度

5. **报告生成**
   - 后端：发送 `report_ready` 消息
   - 前端：显示最终报告

## 部署建议

### 开发环境
- 后端：`uvicorn backend.api.main:app --reload`
- 前端：`npm run dev` (Vite)

### 生产环境
- 后端：使用 Gunicorn + Uvicorn workers
- 前端：构建静态文件，使用 Nginx 服务
- 反向代理：Nginx 处理静态文件和 API 代理
- 数据库：PostgreSQL + Redis

## 迁移步骤

1. **阶段 1：搭建后端 API**
   - 创建 FastAPI 应用
   - 实现基础 REST API
   - 实现 WebSocket 支持
   - 集成现有工作流

2. **阶段 2：搭建前端应用**
   - 初始化 React/Vue 项目
   - 实现基础 UI 组件
   - 集成 WebSocket 客户端
   - 实现研究流程界面

3. **阶段 3：功能完善**
   - 添加任务历史
   - 添加配置管理界面
   - 优化用户体验
   - 添加错误处理和加载状态

4. **阶段 4：优化和部署**
   - 性能优化
   - 添加测试
   - 部署配置
   - 文档完善


# ResearchSync-Agent Frontend

前端 Web 应用，使用 React + TypeScript + Vite 构建。

## 技术栈

- **React 18+** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI 组件库
- **Zustand** - 状态管理
- **React Router** - 路由管理
- **WebSocket** - 实时通信

## 快速开始

### 安装依赖

```bash
npm install
# 或
yarn install
# 或
pnpm install
```

### 开发

```bash
npm run dev
```

### 构建

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── components/     # React 组件
│   ├── pages/         # 页面组件
│   ├── stores/        # 状态管理
│   ├── services/      # API 服务
│   ├── hooks/         # 自定义 Hooks
│   ├── types/         # TypeScript 类型
│   ├── utils/         # 工具函数
│   └── App.tsx        # 根组件
├── public/            # 静态资源
└── package.json       # 依赖配置
```

## 环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```


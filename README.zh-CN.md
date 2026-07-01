---
tags: [readme, overview, 概览, 中文]
aliases: [项目概览中文, 中文说明]
---

# 综合教育平台

一套面向局域网课堂、校内机房和小型教学场景的一体化 Python 学习平台。

它把学生端游戏化学习流程、教师端管理后台、本地化部署、实时 PvP 对战和学习记录沉淀整合在同一个项目里。

[English](README.md)

---

## 项目简介

这个项目面向的是“老师在本地开一台服务器，学生通过浏览器进入课堂学习”的场景，重点解决：

- 本地课堂快速部署
- 学生按单元和关卡推进学习
- 老师统一管理学生和题库
- 学习记录、错题和排行榜沉淀
- 课堂内实时 PvP 对战

它不是通用 LMS，不是云端 SaaS，也不是自由代码执行沙箱。

---

## 核心功能

### 学生端

- 登录与注册
- 首页导航
- 冒险闯关
- 随机练习
- 极限挑战
- 排行榜
- 成就墙
- 学习记录与错题复盘
- PVP 大厅、房间、对战与结算
- 个人中心

### 教师端

- 管理员登录
- 仪表盘
- 学生管理
- 题库、单元、关卡管理
- 教学分析
- 错题统计
- PVP 房间管理
- 导入中心

### 平台能力

- FastAPI 后端
- Vue 3 + TypeScript 前端
- SQLite 持久化
- WebSocket 在线状态与 PVP 同步
- Windows 本地启动
- PyInstaller 打包支持

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router |
| 后端 | FastAPI、SQLAlchemy |
| 数据库 | SQLite |
| 实时通信 | WebSocket |
| 测试 | Pytest、Vitest、Playwright |
| 打包 | PyInstaller |

---

## 仓库结构

```text
backend/
  app/
    main.py            FastAPI 入口
    __main__.py        CLI 入口
    cli.py             迁移命令
    database.py        engine / session / Base
    deps.py            鉴权依赖
    models/            ORM 模型
    schemas/           Pydantic 模型
    routers/           HTTP 路由
    services/          业务逻辑
    ws/                WebSocket 逻辑
  alembic/             迁移
  tests/               后端测试

frontend/
  src/
    main.ts            Vue 启动入口
    router/            路由配置
    stores/            Pinia 状态
    api/               HTTP 请求层
    views/             页面组件
    components/        通用组件

docs/
  PRD.md
  ARCHITECTURE.md
  API.md
  DATABASE.md
  UI_SPEC.md
```

---

## 快速开始

### 环境要求

- Windows 是当前主要维护环境
- Python `>= 3.12`
- Node.js 和 npm
- 推荐使用 `uv` 管理 Python 依赖

### 后端启动

```powershell
uv sync --directory backend
cd backend
uv run python -m app
```

### 前端开发

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

### 一体化本地启动

```powershell
start.bat
```

默认访问地址：

- 学生端：`http://localhost/app/`
- 教师端：`http://localhost/app/admin`

默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

系统首次启动会自动补种管理员账号，首次登录后应立即修改密码。

---

## 常用命令

```powershell
# 前端构建
npm --prefix frontend run build

# 前端单测
npm --prefix frontend run test

# 前端 E2E
npm --prefix frontend run test:e2e

# 后端测试
cd backend
uv run pytest tests/ -v

# 查看迁移状态
cd backend
uv run python -m app migrate --status

# 执行迁移
cd backend
uv run python -m app migrate --upgrade
```

---

## 当前运行事实

- 前端部署路径固定为 `/app/`
- 后端同时暴露 `/api/v1/*` 和 `/api/*`
- 在线状态 WebSocket 入口为 `/ws/online`
- 根路径 `/` 会重定向到 `/app/`
- `/admin` 会重定向到 `/app/admin`
- 教师端当前仍是单个 Vue 页面内的 tab 化后台

---

## 文档地图

下面这些文档是当前仓库的主文档源：

1. [docs/PRD.md](docs/PRD.md)
   产品目标、角色、功能范围、业务规则
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
   代码结构、运行入口、路由、模块边界
3. [docs/API.md](docs/API.md)
   HTTP 接口、WebSocket 消息、鉴权和错误约定
4. [docs/DATABASE.md](docs/DATABASE.md)
   数据表、关系、迁移约束
5. [docs/UI_SPEC.md](docs/UI_SPEC.md)
   学生端/教师端 UI 规范、视觉系统和响应式边界


---

## 开发说明

- 学生端看到的关键业务结果必须以服务端为准
- 判题、PVP 状态和结算是服务端权威逻辑
- 改前端至少应通过构建
- 改后端至少应通过最接近修改范围的验证
- 公开文档请只链接 `docs/` 下的公开文档或 README 本身，不要把本地专用协作文件当成公开入口

---

## 公开仓库说明

通常适合保留在公开仓库里的内容：

- 源码
- 公开文档
- 公开变更日志

通常只建议本地保留的内容：

- 内部变更日志
- agent 记忆和本地 AI 协作文档
- 审查记录和临时草稿
- 数据库文件
- 构建产物

---

## 许可证

详见 [LICENSE](LICENSE)。

---

> 📍 [[README|English Overview]]

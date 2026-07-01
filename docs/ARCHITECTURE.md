---
tags: [architecture, technical, 架构]
aliases: [架构说明, 技术架构, Architecture]
---

# 综合教育平台架构说明

> 文档版本：v2.2.22  
> 更新日期：2026-06-04  
> 文档类型：技术架构基线  
> 使用对象：前端、后端、测试、AI Agent

---

## 1. 架构目标

本文件描述当前仓库真实运行架构，不描述历史设想，也不把未来愿景写成已落地事实。

目标：

- 帮助开发者快速找到入口和边界
- 帮助 AI Agent 在不破坏现有结构的前提下继续开发
- 让前端、后端、数据库、UI、测试知道各自负责什么

---

## 2. 总体运行关系

```text
浏览器
  ├─ 学生端 SPA (/app/)
  └─ 教师端 SPA (/app/admin)
        │
        ├─ HTTP API (/api/v1/* + /api/*)
        └─ WebSocket (/ws/online)
                │
FastAPI 应用
  ├─ routers/        路由层
  ├─ services/       业务层
  ├─ models/         ORM
  ├─ schemas/        请求/响应模型
  ├─ ws/             实时连接与广播
  └─ SQLite          data/app.db
```

---

## 3. 仓库结构

### 3.1 顶层目录

```text
backend/         FastAPI 后端
frontend/        Vue 3 前端
data/            SQLite 数据文件
docs/            对外和协作文档
更新日志/         公开版本日志
```

### 3.2 后端目录

```text
backend/app/
├─ main.py          应用创建、路由挂载、SPA 托管
├─ __main__.py      CLI 入口
├─ cli.py           迁移命令封装
├─ config.py        配置
├─ database.py      engine / SessionLocal / Base / session_scope
├─ deps.py          鉴权依赖
├─ models/          ORM 模型
├─ schemas/         Pydantic 模型
├─ routers/         HTTP API
├─ services/        业务逻辑
└─ ws/              WebSocket 入口与管理
```

### 3.3 前端目录

```text
frontend/src/
├─ main.ts          启动入口
├─ App.vue          根组件
├─ router/          页面路由
├─ stores/          Pinia 状态
├─ api/             HTTP 请求层
├─ views/           页面组件
├─ components/      通用组件
└─ style.css        全局样式与主题变量
```

---

## 4. 运行入口

### 4.1 后端入口

#### `backend/app/main.py`

职责：

- 创建 FastAPI 应用
- 注册异常处理
- 挂载 HTTP 路由
- 注册 `/ws/online`
- 托管 `frontend/dist`
- 处理 `/` 与 `/admin` 重定向
- 启动时自动建表和补种默认管理员

#### `backend/app/__main__.py`

职责：

- 作为 `python -m app` CLI 入口
- 提供迁移子命令

### 4.2 前端入口

#### `frontend/src/main.ts`

职责：

- 创建 Vue 应用
- 注册 Pinia
- 注册 Router
- 恢复学生端登录态

#### `frontend/src/App.vue`

职责：

- 挂载 `router-view`
- 提供页面切换过渡

---

## 5. 前后端边界

### 5.1 前端负责

- 页面布局与交互
- 请求发起
- 局部临时状态
- 路由跳转
- WebSocket 消息消费

### 5.2 前端不负责

- 判题真值
- 权限兜底
- 结算权威结果
- 房间状态最终裁定

### 5.3 后端负责

- 鉴权
- 判题
- 会话管理
- 排行榜与统计
- PVP 房间和对战状态
- 数据持久化
- WebSocket 广播

---

## 6. HTTP 路由结构

后端统一通过 `backend/app/routers/__init__.py` 定义路由组：

- `/auth`
- `/units`
- `/questions`
- `/records`
- `/scores`
- `/achievements`
- `/leaderboard`
- `/admin`
- `/pvp`

在 `main.py` 中同时挂载到：

- `/api/v1/*`
- `/api/*`

设计意义：

- 新旧前缀兼容
- 前端平滑演进

---

## 7. 页面路由结构

### 7.1 基础约束

- Vite base：`/app/`
- Vue Router history base：`/app/`

### 7.2 学生端路由

- `/`
- `/login`
- `/account`
- `/adventure`
- `/adventure/play`
- `/adventure/result`
- `/practice`
- `/practice/session`
- `/practice/result`
- `/extreme`
- `/extreme/session`
- `/extreme/result`
- `/records`
- `/leaderboard`
- `/achievements`
- `/pvp`
- `/pvp/room`
- `/pvp/battle`
- `/pvp/result`

### 7.3 教师端路由

- `/admin`
- `/admin/dashboard`
- `/admin/students`
- `/admin/questions`
- `/admin/analytics`
- `/admin/pvp`

注意：

- `/admin` 会重定向到 `/admin/dashboard`
- 教师端已拆分为后台父路由 + 独立子页面

---

## 8. 前端架构

### 8.1 状态层

当前主要 Pinia store：

- `auth.ts`
  - 学生 token / 用户信息
  - 登录、注册、退出、恢复会话

- `websocket.ts`
  - 学生端 WebSocket
  - 连接、重连、心跳、消息分发

- `game.ts`
  - 学习相关状态

- `pvp.ts`
  - 学生端 PVP 房间、题目、倒计时、反馈、结算

### 8.2 API 层

`frontend/src/api/` 按业务拆分：

- `auth.ts`
- `admin.ts`
- `game.ts`
- `records.ts`
- `leaderboard.ts`
- `pvp.ts`
- `achievements.ts`
- `http.ts`

要求：

- 请求层只负责通信，不堆页面逻辑
- 页面不要直接手写大量 fetch 逻辑

### 8.3 教师端当前结构

教师端当前是“后台父路由 + 业务 Store + 独立页面”体系：

- 父路由：`frontend/src/views/admin/AdminShell.vue`
- 仪表盘：`frontend/src/views/admin/AdminDashboardPage.vue` + `frontend/src/stores/adminDashboard.ts`
- 学生管理：`frontend/src/views/admin/AdminStudentsPage.vue` + `frontend/src/stores/adminStudents.ts`
- 题库管理与导入中心：`frontend/src/views/admin/AdminQuestionsPage.vue` + `frontend/src/stores/adminQuestions.ts`
- 教学分析与错题统计：`frontend/src/views/admin/AdminAnalyticsPage.vue` + `frontend/src/stores/adminAnalytics.ts`
- PVP 管理：`frontend/src/views/admin/AdminPvpPage.vue` + `frontend/src/stores/adminPvp.ts`

管理员登录态仍使用独立的 `admin_token` / `admin_user`，不和学生端 token 混用。

---

## 9. 后端架构

### 9.1 路由层 `routers/`

职责：

- 接收参数
- 接入鉴权依赖
- 调用 service
- 返回 schema

要求：

- 尽量薄
- 不在路由层堆复杂业务流程

### 9.2 服务层 `services/`

职责：

- 题目处理
- 认证辅助
- 评分
- PVP 逻辑
- 限流或统计相关逻辑

硬约束：

- 不要在 `services/` 创建 `SessionLocal()`
- 不要在 `services/` 直接 `commit/rollback`

### 9.3 数据层 `models/` + `schemas/`

- `models/`：数据库模型
- `schemas/`：接口输入输出

要求：

- API 对外结构以 schema 为准
- 页面和测试不要绕过 schema 假设数据库内部字段

---

## 10. 数据库会话模型

`backend/app/database.py` 暴露：

- `engine`
- `SessionLocal`
- `Base`
- `get_db()`
- `session_scope()`

### 10.1 `get_db()`

适用：

- HTTP 请求

行为：

- yield session
- 异常时 rollback
- 请求结束时 close

### 10.2 `session_scope()`

适用：

- 后台任务
- WebSocket 相关流程

行为：

- 上下文退出时 commit
- 异常时 rollback
- 结束时 close

---

## 11. WebSocket 架构

### 11.1 入口

- 统一端点：`/ws/online`

### 11.2 认证方式

- 连接建立后发送首条 `auth` 消息
- 不把 token 放在 URL

### 11.3 当前承载能力

1. 在线状态
   - 管理端收到 `online_status`

2. PVP 房间与对战快照
   - 学生端请求房间 / battle 快照
   - 管理端请求房间列表

### 11.4 管理类

`ConnectionManager` 负责：

- 学生连接
- 管理员连接
- 鉴权缓存
- 广播
- 节流发送
- 过期连接清理

---

## 12. 关键模块边界

### 12.1 学生端 PVP

涉及文件：

- `frontend/src/views/PvPLobbyView.vue`
- `frontend/src/views/PvPRoomView.vue`
- `frontend/src/views/PvPBattleView.vue`
- `frontend/src/views/PvPResultView.vue`
- `frontend/src/stores/pvp.ts`
- `frontend/src/api/pvp.ts`

规则：

- 初始状态可以走 HTTP
- 实时快照走 WebSocket
- 题目反馈不能被乱序消息覆盖

### 12.2 教师端 PVP

涉及文件：

- `frontend/src/views/admin/AdminPvpPage.vue`
- `frontend/src/stores/adminPvp.ts`
- `frontend/src/api/admin.ts`
- `backend/app/routers/pvp.py`
- `backend/app/services/pvp_service.py`

规则：

- 管理端 PVP 是 `/admin/pvp` 独立后台页面
- 使用独立 admin WebSocket 同步房间快照
- PVP 房间列表、表单、开始和结束操作由 `stores/adminPvp.ts` 管理

### 12.3 记录与判题

涉及文件：

- `backend/app/routers/records.py`
- `backend/app/models/record.py`
- `frontend/src/api/records.ts`

规则：

- 判题结果以服务端为准
- 每次答题必须绑定 `play_session_id`

---

## 13. UI 与样式边界

当前全局样式中心：

- `frontend/src/style.css`

当前事实：

- 学生端和教师端共用一套基础 design tokens
- 学生端已有浅色视觉系统
- 教师端通过 `[data-theme="admin"]` 做主题覆盖

要求：

- 大部分页面调整不能只改单页 `.vue`，还要确认是否影响 `style.css`
- 不要随意回退现有视觉系统

---

## 14. 测试边界

后端：

- `backend/tests/unit/`
- `backend/tests/integration/`

前端：

- `frontend/tests/components/`
- `frontend/tests/e2e/specs/`

要求：

- 结构性改动至少补最接近范围验证
- 前端改动至少跑构建
- 后端改动至少跑相关测试、迁移状态或启动验证

---

## 15. AI Agent 修改规则

AI 不允许：

- 乱删已有模块
- 一口气大改架构
- 修改无关文件
- 把未来方案当当前事实
- 新增前端字段却没有后端支持
- 绕过服务层直接拼数据库实现

AI 应当：

- 先读 `PRD`
- 再读 `ARCHITECTURE`
- 按任务再读 `API` / `DATABASE` / `UI_SPEC`
- 小步修改，小步验证

---

## 16. 后续合理演进方向

这些方向可以做，但都还不是当前事实：

1. 继续细化教师后台公共组件
2. 为教师后台业务 Store 补充单元测试
3. 细化 WebSocket 消息模块
4. 把更多边界写进自动化测试

---

## 关联文档

- [[docs/HOME|文档地图]] · [[docs/PRD|PRD]] · [[docs/API|API]] · [[docs/DATABASE|数据库]] · [[docs/UI_SPEC|UI规范]] · [[docs/AGENTS|协作说明]]

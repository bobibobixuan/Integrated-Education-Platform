---
tags: [api, websocket, interface, 接口]
aliases: [API文档, 接口说明, API Reference]
---

# 综合教育平台 API 说明

> 文档版本：v2.2.23  
> 更新日期：2026-06-04  
> 文档类型：接口基线  
> 使用对象：前端、后端、测试、AI Agent

---

## 1. 总体约定

### 1.1 前缀

当前后端同时支持两套前缀：

- `/api/v1/*`
- `/api/*`

前端当前主要使用兼容前缀 `/api/*`。

### 1.2 数据格式

- 请求和响应以 JSON 为主
- 鉴权接口使用 Bearer Token
- WebSocket 使用 JSON message

### 1.3 鉴权

学生端：

- `Authorization: Bearer <token>`

教师端：

- 同样走 Bearer Token
- 管理员接口统一通过 `get_admin_user` 鉴权

### 1.4 错误约定

- HTTP 层使用标准状态码
- 页面上应展示面向用户的错误提示
- 测试不要只断言文案，优先断言状态码和核心字段

---

## 2. 鉴权相关接口

### `POST /api/auth/register`

作用：

- 学生注册

请求：

```json
{
  "username": "student01",
  "password": "1234",
  "nickname": "小明"
}
```

响应：

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "student01",
    "nickname": "小明",
    "role": "user",
    "is_active": true,
    "force_password_change": false
  }
}
```

### `POST /api/auth/login`

作用：

- 学生或管理员登录

### `POST /api/auth/refresh`

作用：

- 刷新 token

### `GET /api/auth/me`

作用：

- 获取当前登录用户

### `PUT /api/auth/profile`

作用：

- 更新昵称

### `PUT /api/auth/password`

作用：

- 修改密码
- 成功后返回新的 token

---

## 3. 单元与题目接口

### `GET /api/units/with-levels`

作用：

- 获取单元及其关卡树

### `GET /api/units/`

作用：

- 获取单元列表

### `GET /api/units/{unit_id}/levels`

作用：

- 获取某单元下的关卡

### `GET /api/questions/batch`

作用：

- 批量获取题目

### `GET /api/questions/units/{unit_id}`

作用：

- 获取某单元的题目

### `GET /api/questions/levels/{level_id}`

作用：

- 获取某关卡的题目

### `GET /api/questions/{question_id}`

作用：

- 获取单题详情

---

## 4. 学习记录与会话接口

### `GET /api/records/summary`

作用：

- 获取用户总统计

关键字段：

- `total_questions`
- `total_correct`
- `total_score`
- `power_score`
- `max_combo`
- `practice_count`
- `extreme_passes`
- `extreme_dual_passes`

### `GET /api/records/progress`

作用：

- 获取关卡进度

### `GET /api/records/recent`

作用：

- 获取最近作答记录

### `GET /api/records/wrong`

作用：

- 获取错题记录

### `POST /api/records/start-session`

作用：

- 开启学习会话

请求：

```json
{
  "level_id": 1,
  "mode": "adventure"
}
```

响应：

```json
{
  "play_session_id": "uuid",
  "started_at": "2026-06-04T12:00:00Z",
  "question_count": 5
}
```

### `POST /api/records/next-question`

作用：

- 获取下一题

### `POST /api/records/answer`

作用：

- 提交普通作答

请求：

```json
{
  "play_session_id": "uuid",
  "question_id": 10,
  "submitted_answer": "B",
  "client_time_spent": 3.2
}
```

关键响应字段：

- `success`
- `is_correct`
- `correct_answer`
- `score_added`
- `new_achievements`

`new_achievements` 当前返回对象数组，每项包含：

- `id`
- `name`
- `icon`
- `description`
- `rarity`
- `category`

### `POST /api/records/stats`

作用：

- 同步轻量统计增量

---

## 5. 排行榜与成就接口

### `GET /api/leaderboard/`

作用：

- 获取排行榜

前端当前使用两类榜单：

- `power`
- `weekly`

### `GET /api/achievements/`

作用：

- 获取成就列表

说明：

- 服务端会在启动和接口访问时自动补种默认成就定义
- 服务端会在返回前按当前统计与关卡进度重新评估解锁状态

关键字段：

- `id`
- `name`
- `icon`
- `description`
- `hint`
- `rarity`
- `category`
- `unlocked`
- `unlocked_at`

---

## 6. 分数与进度接口

### `GET /api/scores/progress`

作用：

- 获取按单元组织的进度

### `GET /api/scores/power`

作用：

- 获取战力相关结果

### `GET /api/scores/stats`

作用：

- 获取统计结果

---

## 7. 学生端 PVP 接口

### `GET /api/pvp/my-room`

作用：

- 获取当前用户所在房间

### `GET /api/pvp/rooms`

作用：

- 获取房间列表

### `POST /api/pvp/rooms`

作用：

- 学生创建房间

请求关键字段：

- `title`
- `description`
- `group_size`
- `question_unit_ids`
- `question_count`
- `battle_time_limit_seconds`

### `POST /api/pvp/rooms/{room_id}/join`

作用：

- 加入房间

### `PUT /api/pvp/my-room/ready`

作用：

- 切换准备状态

### `POST /api/pvp/my-room/leave`

作用：

- 离开房间

### `GET /api/pvp/my-battle`

作用：

- 获取或恢复当前对战会话

响应关键字段：

- `room`
- `play_session_id`
- `session_status`
- `question_count`
- `current_question`

### `POST /api/pvp/answer`

作用：

- 提交 PVP 答案

响应关键字段：

- `success`
- `is_correct`
- `correct_answer`
- `battle_power_delta`
- `current_battle_power`
- `session_status`
- `knowledge`
- `next_question`

### `POST /api/pvp/finalize-session`

作用：

- 结束并结算当前 PVP 会话

---

## 8. 教师端接口

### 8.1 仪表盘

#### `GET /api/admin/dashboard`

作用：

- 获取后台首页 KPI 和趋势数据

### 8.2 学生管理

#### `GET /api/admin/users`

作用：

- 获取用户列表

#### `GET /api/admin/students`

作用：

- 分页学生列表

#### `GET /api/admin/students/{user_id}`

作用：

- 获取学生详情

#### `POST /api/admin/students`

作用：

- 创建学生

#### `POST /api/admin/students/import`

作用：

- 批量导入学生

#### `PUT /api/admin/students/{user_id}`

作用：

- 更新学生

#### `DELETE /api/admin/students/{user_id}`

作用：

- 禁用或删除学生相关状态

### 8.3 教学分析

#### `GET /api/admin/analytics/levels`

作用：

- 关卡统计分析

#### `GET /api/admin/analytics/wrong-questions`

作用：

- 高错题统计

### 8.4 题库管理

#### `GET /api/admin/questions`

#### `POST /api/admin/questions`

#### `PUT /api/admin/questions/{question_id}`

#### `DELETE /api/admin/questions/{question_id}`

作用：

- 完整题库 CRUD

### 8.5 设置

#### `GET /api/admin/settings/registration`

#### `PUT /api/admin/settings/registration`

作用：

- 获取和修改学生自助注册开关

### 8.6 导入

#### `POST /api/admin/import`

作用：

- JSON 题库导入

#### `POST /api/admin/import/excel`

作用：

- Excel 题库导入

### 8.7 教师端 PVP

#### `GET /api/admin/pvp/rooms`

#### `POST /api/admin/pvp/rooms`

#### `PUT /api/admin/pvp/rooms/{room_id}`

#### `POST /api/admin/pvp/rooms/{room_id}/start`

#### `POST /api/admin/pvp/rooms/{room_id}/finish`

#### `GET /api/admin/pvp/logs`

作用：

- 教师端房间管理、开赛、结算和日志查看

---

## 9. WebSocket 协议

端点：

- `/ws/online`

### 9.1 基础消息

客户端发送：

- `auth`
- `deauth`
- `logout`
- `heartbeat`

服务端发送：

- `auth_state`

### 9.2 在线状态

服务端对管理员发送：

- `online_status`

包含：

- `online_count`
- `total_count`
- `online_users`
- `offline_users`

### 9.3 PVP 消息

客户端请求：

- `request_pvp_room_state`
- `request_pvp_battle`
- `request_pvp_rooms`

服务端返回：

- `pvp_room_state`
- `pvp_battle_session`
- `pvp_rooms`
- `pvp_error`

---

## 10. 前端调用边界

前端调用接口时必须遵守：

- 不自行伪造服务端最终状态
- 不依赖未在 schema 中定义的字段
- 对高风险逻辑优先用后端返回值覆盖本地猜测
- PVP 相关状态不要只靠 HTTP，也不要只靠 WebSocket，当前是混合模式

---

## 11. AI Agent 修改接口时的规则

如果 AI 修改 API：

- 不要随意改路径
- 不要随意删字段
- 不要改出与前端类型不兼容的结构
- 改 schema 时同步更新前端 `types/api.ts`
- 改鉴权或错误约定时同步更新 `docs/API.md`

---

## 关联文档

- [[README|项目概览]] · [[docs/PRD|PRD]] · [[docs/ARCHITECTURE|架构]] · [[docs/DATABASE|数据库]] · [[docs/UI_SPEC|UI规范]]

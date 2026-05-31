# 综合教育平台数据库说明

> 文档版本：v2.2.22  
> 更新日期：2026-06-04  
> 文档类型：数据库基线  
> 使用对象：后端、测试、AI Agent

---

## 1. 总体原则

当前数据库使用 SQLite，主文件位置：

- `data/app.db`

数据库负责：

- 保存用户、题库、学习记录、PVP、成就等持久状态

数据库不应被：

- 文档指挥直接手工修改
- 前端直接依赖结构
- UI 绕过后端直接控制

---

## 2. 连接与配置

入口文件：

- `backend/app/database.py`

当前连接配置包含：

- `journal_mode=WAL`
- `busy_timeout=10000`
- `synchronous=NORMAL`
- `foreign_keys=ON`

作用：

- 提升并发稳定性
- 降低 SQLite 锁冲突带来的课堂异常

---

## 3. 会话与事务边界

### 3.1 `get_db()`

适用：

- HTTP 请求

行为：

- 请求作用域 session
- 异常回滚
- 结束关闭

### 3.2 `session_scope()`

适用：

- WebSocket
- 后台任务

行为：

- 上下文退出时自动提交
- 异常回滚

### 3.3 硬规则

- 不要在 `services/` 里创建 `SessionLocal()`
- 不要在 `services/` 里直接 `commit/rollback`

---

## 4. 核心表概览

### 4.1 用户与权限

#### `users`

主字段：

- `id`
- `username`
- `password_hash`
- `nickname`
- `role`
- `token_version`
- `is_active`
- `force_password_change`
- `disabled_at`
- `disabled_reason`

作用：

- 学生与管理员账号
- token 失效控制
- 禁用与强制改密控制

#### `user_stats`

主字段：

- `user_id`
- `total_questions`
- `total_correct`
- `total_score`
- `power_score`
- `max_combo`
- `practice_count`
- `extreme_passes`
- `extreme_dual_passes`

作用：

- 用户累计统计

关系：

- `users` 1:1 `user_stats`

### 4.2 内容结构

#### `units`

主字段：

- `id`
- `name`
- `icon`
- `subtitle`
- `description`
- `learning_goal`
- `coach_line`
- `starter_tip`
- `color`
- `sort_order`
- `is_active`

#### `levels`

主字段：

- `id`
- `unit_id`
- `name`
- `icon`
- `bg`
- `questions_count`
- `sort_order`
- `is_active`

关系：

- `units` 1:N `levels`

#### `questions`

主字段：

- `id`
- `level_id`
- `title`
- `type`
- `content`
- `options`
- `answer`
- `knowledge_meaning`
- `knowledge_rule`
- `knowledge_error`
- `knowledge_example`
- `sort_order`
- `is_active`

关系：

- `levels` 1:N `questions`

### 4.3 学习记录

#### `answer_records`

主字段：

- `user_id`
- `question_id`
- `user_answer`
- `is_correct`
- `time_spent`
- `mode`
- `play_session_id`
- `question_version`
- `correct_answer_snapshot`

关键约束：

- 唯一约束：`(play_session_id, question_id)`

作用：

- 每次真实作答记录

#### `level_progress`

主字段：

- `user_id`
- `level_id`
- `stars`
- `unlocked`
- `best_combo`

关键约束：

- 唯一约束：`(user_id, level_id)`

作用：

- 用户关卡进度

#### `play_sessions`

主字段：

- `play_session_id`
- `user_id`
- `level_id`
- `mode`
- `pvp_room_id`
- `best_combo`
- `is_suspicious`
- `status`
- `started_at`
- `expires_at`
- `completed_at`

作用：

- 学习或对战会话主表

#### `session_questions`

主字段：

- `play_session_id`
- `question_id`
- `question_order`
- `delivered_at`
- `answered_at`

关键约束：

- `(play_session_id, question_id)`
- `(play_session_id, question_order)`

作用：

- 保障题目顺序与幂等提交

#### `score_review_decisions`

作用：

- 保存人工复核或评分决策相关数据

### 4.4 PVP

#### `pvp_rooms`

主字段：

- `title`
- `description`
- `group_size`
- `status`
- `mode`
- `ranking_metric`
- `question_unit_ids`
- `question_count`
- `battle_time_limit_seconds`
- `countdown_started_at`
- `auto_start_at`
- `started_at`
- `finished_at`
- `battle_started_at`
- `battle_expires_at`
- `battle_answer_accept_until`

作用：

- 房间主表

#### `pvp_room_members`

主字段：

- `room_id`
- `user_id`
- `seat_order`
- `team`
- `is_ready`
- `live_battle_power`
- `live_correct_count`
- `live_wrong_count`
- `live_answered_count`
- `current_streak`
- `best_streak`

关键约束：

- `(room_id, user_id)` 唯一

作用：

- 房间成员及实时战况

#### `pvp_broadcasts`

主字段：

- `room_id`
- `message`
- `category`
- `created_by`

作用：

- 房间日志和广播记录

### 4.5 成就

#### `achievements`

主字段：

- `id`
- `name`
- `icon`
- `description`
- `hint`
- `rarity`
- `category`
- `condition_type`
- `condition_value`

#### `user_achievements`

主字段：

- `user_id`
- `achievement_id`
- `unlocked_at`

关键约束：

- `(user_id, achievement_id)` 唯一

---

## 5. 主要关系图

```text
users
  ├─ 1:1 user_stats
  ├─ 1:N answer_records
  ├─ 1:N level_progress
  ├─ 1:N play_sessions
  ├─ 1:N user_achievements
  ├─ 1:N pvp_room_members
  ├─ 1:N created pvp_rooms
  └─ 1:N pvp_broadcasts

units
  └─ 1:N levels

levels
  ├─ 1:N questions
  ├─ 1:N level_progress
  └─ 1:N play_sessions

questions
  ├─ 1:N answer_records
  └─ 1:N session_questions

pvp_rooms
  ├─ 1:N pvp_room_members
  ├─ 1:N pvp_broadcasts
  └─ 1:N play_sessions
```

---

## 6. 关键业务约束

### 6.1 判题

- `answer_records.is_correct` 必须由服务端写入
- 不信任前端传回的正确性结果

### 6.2 会话

- `play_session_id` 是学习和 PVP 记录的关键关联键
- 同一会话内同一题不能重复记账

### 6.3 PVP

- 旧会话失效处理必须限制 `mode == "pvp"`
- 房间重置时要清空对战时间字段
- 最终结算必须处理未答题项

---

## 7. 索引与唯一约束重点

高价值约束：

- `users.username` 唯一
- `user_stats.user_id` 唯一
- `answer_records(play_session_id, question_id)` 唯一
- `level_progress(user_id, level_id)` 唯一
- `session_questions(play_session_id, question_id)` 唯一
- `session_questions(play_session_id, question_order)` 唯一
- `play_sessions.play_session_id` 唯一
- `pvp_room_members(room_id, user_id)` 唯一
- `user_achievements(user_id, achievement_id)` 唯一

---

## 8. 迁移规则

当前迁移相关入口：

- `backend/app/__main__.py`
- `backend/app/cli.py`
- `backend/alembic/`

常用命令：

```powershell
cd backend
uv run python -m app migrate --status
uv run python -m app migrate --upgrade
```

规则：

- 不直接改线上数据库文件结构
- 模型字段变化要配套迁移
- 文档写清楚行为变化，不鼓励手工 SQL 修库

---

## 9. AI Agent 修改数据库时的规则

AI 如果涉及数据库变更，必须：

- 先读 `docs/DATABASE.md`
- 再读对应 `models/` 和 `schemas/`
- 不直接让前端依赖内部字段
- 不删除正在使用的字段
- 不随意改唯一约束
- 不把迁移工作留成口头说明

必须同步考虑：

- API schema
- 前端类型
- 测试
- 文档

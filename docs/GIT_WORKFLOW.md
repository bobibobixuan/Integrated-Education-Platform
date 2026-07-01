---
tags: [git, workflow, devops, 工作流]
aliases: [Git工作流, 双仓库策略, Git Workflow]
---

# Git 双仓库工作流

> 面向项目维护者和 AI 协作者。  
> 本文档详细说明日常开发和正式发版的标准 Git 操作流程。

---

## 1. 远端仓库配置

本项目使用两个 GitHub 远端仓库：

```txt
private → https://github.com/bobibobixuan/Integrated-Education-Platform-private.git
public  → https://github.com/bobibobixuan/Integrated-Education-Platform.git
```

### 配置方法

如果还没有配置远端，执行：

```bash
# 如果已经有 origin，先改名
git remote rename origin public

# 添加私有仓库远端
git remote add private https://github.com/bobibobixuan/Integrated-Education-Platform-private.git
```

### 验证配置

```bash
git remote -v
```

期望输出：

```txt
private  https://github.com/bobibobixuan/Integrated-Education-Platform-private.git (fetch)
private  https://github.com/bobibobixuan/Integrated-Education-Platform-private.git (push)
public   https://github.com/bobibobixuan/Integrated-Education-Platform.git (fetch)
public   https://github.com/bobibobixuan/Integrated-Education-Platform.git (push)
```

---

## 2. 双仓库定位

```
private（私有仓库）              public（公开仓库）
─────────────────────────────────────────────────
日常开发                          正式发布
preview/dev 分支                  main 分支
feature/* 分支                    稳定版本 tag
fix/* 分支                        CHANGELOG.md
更新日志/ 详细记录
完整开发历史
```

**核心结论：**

> private 是开发仓库，public 是展示仓库。  
> preview/dev 只推 private。  
> main 稳定后才推 public。

---

## 3. 分支策略

| 分支 | 定位 | 推送目标 | 说明 |
|------|------|----------|------|
| `main` | 正式稳定分支 | `private` + `public` | 只在一批功能收敛、测试通过后推进 |
| `preview/dev` | 日常开发分支 | 仅 `private` | AI 所有修改默认提交到这里 |
| `feature/*` | 功能分支 | 仅 `private` | 如 `feature/pvp-admin`，完成后合并回 `preview/dev` |
| `fix/*` | 修复分支 | 仅 `private` | 如 `fix/login-redirect`，完成后合并回 `preview/dev` |

---

## 4. 日常开发流程

### 标准步骤

```bash
# 1. 切换到开发分支
git checkout preview/dev

# 2. 拉取最新代码
git pull private preview/dev

# 3. 修改代码...

# 4. 暂存改动
git add .

# 5. 提交（使用规范前缀）
git commit -m "类型: 简短说明"

# 6. 推送到私有仓库
git push private preview/dev
```

### 提交信息格式

```txt
feat:     新增功能
fix:      修复问题
ui:       优化界面
docs:     更新文档
refactor: 重构代码（不改变功能）
test:     增加或调整测试
chore:    工程配置或杂项调整
```

示例：

```bash
git commit -m "ui: 优化学生端 PVP 竞技大厅布局"
git commit -m "fix: 修复房间状态刷新不同步问题"
git commit -m "docs: 更新双仓库 Git 工作流说明"
```

### 创建功能分支

```bash
# 从 preview/dev 创建功能分支
git checkout preview/dev
git checkout -b feature/新功能名

# 开发完成后合并回 preview/dev
git checkout preview/dev
git merge feature/新功能名
git push private preview/dev
```

### 创建修复分支

```bash
git checkout preview/dev
git checkout -b fix/问题描述
# ... 修复 ...
git checkout preview/dev
git merge fix/问题描述
git push private preview/dev
```

---

## 5. 正式发版流程

**只有用户明确说"准备发正式版""合并到 main""发布 vX.X.X"时才进入。**

### 发版步骤

```bash
# 1. 确保 preview/dev 是最新且干净的
git checkout preview/dev
git status

# 2. 切到 main
git checkout main
git pull private main

# 3. 合并 preview/dev
git merge preview/dev

# 4. 根据 更新日志/ 汇总正式版本说明

# 5. 更新 CHANGELOG.md

# 6. 提交版本说明
git add CHANGELOG.md
git commit -m "docs: 发布 vX.X.X 正式版本说明"

# 7. 打 tag
git tag -a vX.X.X -m "vX.X.X: 版本说明"

# 8. 推送到私有仓库
git push private main
git push private vX.X.X

# 9. 推送到公开仓库
git push public main
git push public vX.X.X

# 10. 切回开发分支
git checkout preview/dev
```

### 发版示例

```bash
git checkout preview/dev
git status
git checkout main
git pull private main
git merge preview/dev

# 汇总更新日志
git add CHANGELOG.md
git commit -m "docs: 发布 v1.1.0 正式版本说明"
git tag -a v1.1.0 -m "v1.1.0: PVP 竞技大厅与移动端适配"

git push private main
git push private v1.1.0
git push public main
git push public v1.1.0

git checkout preview/dev
```

---

## 6. 公开仓库只推这些

**允许推送到 `public`：**

```bash
git push public main
git push public v1.0.0
git push public v1.1.0
git push public v2.0.0
# ... 等正式版本 tag
```

**绝对禁止：**

```bash
# 禁止！
git push public preview/dev
git push public feature/*
git push public fix/*
git push public --all
git push public --mirror
git push --mirror public
```

---

## 7. 日志策略

| 日志 | 用途 | 推送目标 | 更新时机 |
|------|------|----------|----------|
| `更新日志/` | 预览期详细变动 | 仅 `private` | 每次 AI 修改后 |
| `CHANGELOG.md` | 正式版本说明 | `public`（随 `main`） | 正式发版时 |

规则：
- 预览期改动 → 更新 `更新日志/`，不急着写 `CHANGELOG.md`
- 正式发版 → 汇总 `更新日志/` → 写入 `CHANGELOG.md` → 合并到 `main` → 打 tag

---

## 8. 禁止操作（完整列表）

以下命令**绝对不允许**执行，除非用户明确单独确认：

```bash
# 危险推送
git push public --all
git push public --mirror
git push --mirror public
git push --force
git push -f

# 危险本地操作
git reset --hard
git clean -fd
git rebase --abort 外的 rebase 操作

# 不允许的行为
# ✗ 把 preview/dev 推到 public
# ✗ 把 feature/* 推到 public
# ✗ 把 fix/* 推到 public
# ✗ 自动覆盖远程历史
# ✗ 自动删除未知文件
# ✗ 自动切换分支导致未保存改动丢失
```

---

## 9. 公开仓库清理

### 删除公开仓库中不该存在的分支

如果发现公开仓库有 `preview/dev`、`feature/*`、`fix/*` 等不应公开的分支，立即删除：

```bash
# 删除公开仓库的 preview/dev
git push public --delete preview/dev

# 删除公开仓库的功能分支
git push public --delete feature/xxx
```

### 验证公开仓库干净

```bash
git ls-remote --heads public
```

期望输出只有 `refs/heads/main`（和正式 tag）。

---

## 10. 私有仓库 main 同步

当 `preview/dev` 已收敛且需要更新 `private/main` 时：

```bash
# 1. 确保 preview/dev 最新
git checkout preview/dev
git status

# 2. 把 preview/dev 推为 private 的 main
git push private preview/dev:main --force
```

注意：
- `private/main` 是完整开发历史的镜像，不需要像 `public/main` 那样干净
- 如果旧的 `private/main` 需要保留，先存档：

```bash
# 存档旧 main
git push private private/main:refs/heads/archive/legacy-main

# 再覆盖
git push private preview/dev:main --force
```

---

## 11. 日常操作速查表

| 想做什么 | 命令 |
|----------|------|
| 日常提交 | `git add . && git commit -m "type: msg" && git push private preview/dev` |
| 拉取最新 | `git pull private preview/dev` |
| 查看状态 | `git status` |
| 查看日志 | `git log --oneline -10` |
| 新建功能分支 | `git checkout -b feature/xxx` |
| 合并功能分支 | `git checkout preview/dev && git merge feature/xxx` |
| 发正式版 | 见第 5 节完整流程 |
| 删除公开仓库分支 | `git push public --delete preview/dev` |
| 清理公开仓库 | `git ls-remote --heads public` |
| 同步 private/main | `git push private preview/dev:main --force` |
| 存档旧 main | `git push private private/main:refs/heads/archive/legacy-main` |

---

> 📍 [[docs/HOME|文档地图]] · [[docs/RELEASE_POLICY|发版策略]]

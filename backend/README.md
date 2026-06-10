# User Activity Backend

用户活跃度后台 Demo。收集手机前端上报的活跃度（0-100），维护单向好友关系，每小时同步好友活跃度数据。

## 项目结构

```
backend/
├── run.sh              # 一键启动脚本
├── requirements.txt    # Python 依赖
├── init_demo.py        # 初始化演示数据
├── activity.db         # SQLite 数据库（自动生成）
├── .venv/              # Python 虚拟环境
└── app/
    ├── __init__.py
    ├── main.py         # FastAPI 应用入口 + 所有 API 路由
    ├── models.py       # 数据库模型（User / Friendship / ActivityLog）
    ├── database.py     # SQLAlchemy 异步引擎配置
    ├── auth.py         # JWT 认证（hash / token / dependency）
    ├── tasks.py        # 后台定时任务
    └── templates/
        └── admin.html  # Web 管理页面
```

## 快速启动

```bash
# 创建虚拟环境（首次）
python3 -m venv .venv

# 安装依赖
.venv/bin/pip install -r requirements.txt

# 初始化演示数据
.venv/bin/python init_demo.py

# 启动服务
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或直接用脚本
bash run.sh
```

## 演示用户

| 用户 | 密码 | 类型 | 好友圈 |
|------|------|------|--------|
| admin | admin123 | 真实 | alice, bob, carol, dave, eve |
| alice | alice123 | 真实 | bob, carol, dave, eve |
| bob | bob123 | 真实 | alice, carol, frank, grace |
| carol | carol123 | 真实 | alice, bob, hank, iris |
| dave | dave123 | 虚拟 | eve |
| eve | eve123 | 虚拟 | — |
| frank | frank123 | 虚拟 | grace |
| grace | grace123 | 虚拟 | — |
| hank | hank123 | 虚拟 | iris |
| iris | iris123 | 虚拟 | — |
| jack | jack123 | 虚拟 | — |
| kate | kate123 | 虚拟 | — |

## API 接口

### 认证

所有 `/api/` 接口（除注册、登录外）需要在 HTTP Header 中携带 JWT token：

```
Authorization: Bearer <token>
```

### 用户

#### `POST /api/register` — 注册

请求体：
```json
{"username": "alice", "password": "alice123"}
```

响应：
```json
{"token": "eyJ...", "user_id": 1, "username": "alice"}
```

#### `POST /api/login` — 登录

请求体：
```json
{"username": "alice", "password": "alice123"}
```

响应：
```json
{"token": "eyJ...", "user_id": 1, "username": "alice"}
```

#### `GET /api/me` — 当前用户信息

响应：
```json
{"user_id": 1, "username": "alice", "activity_score": 85, "is_online": true, "is_simulated": false}
```

#### `GET /api/users` — 列出所有真实用户

响应：
```json
{"users": [{"user_id": 1, "username": "alice", "is_online": true}, ...]}
```

### 心跳与活跃度

#### `POST /api/heartbeat` — 手机端心跳

手机端应每分钟调用一次。超过 3 分钟无心跳，后台标记离线并将活跃度置 0。

响应：
```json
{"status": "ok", "timestamp": "2026-06-05T09:20:50"}
```

#### `POST /api/activity` — 上报活跃度

每小时间隔上报，或随时主动上报。score 范围 0-100。

请求体：
```json
{"score": 85}
```

响应：
```json
{"status": "ok", "score": 85}
```

### 好友

好友关系为**单向**。A 添加 B 为好友后，A 能查看 B 的活跃度；B 看不到 A，除非 B 也添加 A。

#### `GET /api/friends/activity` — 拉取好友活跃度

响应：
```json
{
  "friends": [
    {"username": "bob", "activity_score": 60, "is_online": true, "is_simulated": false},
    {"username": "carol", "activity_score": 11, "is_online": true, "is_simulated": false}
  ]
}
```

#### `POST /api/friends/add` — 添加好友

请求体：
```json
{"username": "carol"}
```

响应：
```json
{"status": "ok", "friend": "carol"}
```

#### `POST /api/friends/remove` — 删除好友

请求体：
```json
{"username": "carol"}
```

响应：
```json
{"status": "ok", "friend": "carol"}
```

### 管理后台

#### `GET /admin` — 管理页面

返回一个完整的 Web 管理界面。登录后可查看所有用户卡片（在线状态、活跃度进度条、好友数、最后心跳时间），每 15 秒自动刷新数据。

#### `POST /admin/login` — 管理登录

```
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

响应：
```json
{"token": "eyJ...", "username": "admin"}
```

#### `GET /admin/data` — 管理后台 JSON 数据

管理页面通过该接口获取实时数据，也可供外部调用。

响应：
```json
{
  "users": [
    {"id": 1, "username": "admin", "activity_score": 79, "is_online": true, "is_simulated": false, "last_heartbeat": "...", "friend_count": 5}
  ],
  "activity_logs": [
    {"id": 1, "user_id": 2, "score": 85, "timestamp": "..."}
  ]
}
```

#### `GET /health` — 健康检查

```json
{"status": "ok", "time": "2026-06-05T09:20:50"}
```

## 核心机制

### 离线检测

- 手机端每分钟调用 `POST /api/heartbeat`
- 后台每 30 秒扫描一次，检测最后心跳时间
- 超过 3 分钟无心跳 → 标记离线，活跃度置 0
- 再次登录或发心跳可恢复在线状态

### 虚拟用户模拟

- `init_demo.py` 创建 8 个虚拟用户（dave ~ kate）
- 后台每 60 秒为虚拟用户生成随机活跃度（0-100）
- 虚拟用户始终保持在线
- 虚拟用户之间也有好友关系，增加演示丰富度

### 活跃度推送

- 后台每 60 秒扫描所有真实用户的好友关系
- 记录推送事件日志（`activity_logs` 表）
- 手机端可随时主动 `GET /api/friends/activity` 拉取最新数据
- 离线好友的活跃度返回 0

### 数据库

- SQLite 本地文件（`activity.db`），无需安装额外数据库
- 三张表：`users`、`friendships`、`activity_logs`
- 删除 `activity.db` 后重新运行 `init_demo.py` 即可重置

### 后台定时任务

| 任务 | 间隔 | 说明 |
|------|------|------|
| `check_heartbeats` | 30 秒 | 检测心跳超时，标记离线 |
| `simulate_virtual_activities` | 60 秒 | 虚拟用户随机活跃度 |
| `push_activities_to_friends` | 60 秒 | 扫描好友关系，记录推送事件 |

## 技术栈

- **框架**: FastAPI (Python 3.12)
- **数据库**: SQLAlchemy + aiosqlite (异步)
- **认证**: JWT (python-jose) + bcrypt (passlib)
- **调度**: APScheduler
- **模板**: 纯静态 HTML + vanilla JavaScript
- **样式**: 暗色主题，CSS Grid 卡片布局

## 一键重置

```bash
rm activity.db && .venv/bin/python init_demo.py
```
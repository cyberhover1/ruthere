# 安心圈 — 工作日志（WORKLOG）

> 跨会话工作状态记录。下次开机/新会话先读此文件，快速恢复上下文。
> 最后更新：2026-06-18

---

## 1. 项目概况

- **产品**：安心圈（RutThere）——「位置共享」与「完全失联」之间的免打扰轻量状态互通工具
- **技术栈**：前端 Kotlin（Android Jetpack Compose） + 后端 Python（FastAPI）
- **通信模式**：无推送、无轮询；前端上报时后端顺带下发好友状态（PRD §6）
- **仓库**：`git@github.com:cyberhover1/ruthere.git`，主分支 `main`
- **需求文档**：`安心圈需求文档（PRD）.md`（本地，**已 git-ignore，不推送**，含泄露密钥）
- **编程计划**：`安心圈编程计划.md`（本地，**已 git-ignore，不推送**）

## 2. 里程碑进度

| 里程碑 | 状态 | 远程 commit | 说明 |
|--------|------|------------|------|
| M0 项目骨架 | ✅ 完成 | `b5813b5` | Kotlin/Compose 前端 + FastAPI 后端 + Docker |
| M1 用户系统 | ✅ 完成 | `ea7465d` | 邮箱注册/Resend验证码/登录/单设备登录/登出 |
| M2 好友系统 | ✅ 完成 | `ed445ff` | QR加好友/邮箱搜索/好友申请/昵称/删除/数据源权限矩阵/通知 |
| M3 活跃度系统 | ✅ 完成 | `bf6ac8f` | 上报/按好友矩阵计算可见值/衰减/离线判定/置满/脱敏下发 |
| M4 互动功能 | ✅ 完成 | `1495446` | 打卡/戳一戳(限频+发起方置满+通知) |
| **后端合计** | ✅ **M0-M4 全部完成** | | **71 个测试全绿** |
| M5 App 骨架 + 服务器配置 + 登录 | ✅ 完成 | `e4cec89` | Kotlin/Compose 导航/Retrofit+OkHttp+Moshi/无DI(ServiceLocator)/服务器地址配置(默认IP+端口+恢复默认，IP 通过 default_server.properties 配置)/注册→验证→登录/App图标。模拟器验证通过 |
| M6 用户系统(前端) | ✅ 并入 M5 | `e4cec89` | 注册/登录/验证码 UI（随 M5 一并完成） |
| M7 好友系统(前端) | ✅ 完成 | `514024f` | 好友列表/添加(二维码生成+扫码+邮箱搜索)/好友申请(同意拒绝)/详情(改昵称+数据源开关+删除)。zxing库。模拟器联调通过 |
| M8 传感器采集 | ✅ 完成 | `84f77c1` | WorkManager 30分钟周期采集7类数据源+归一化0..1+DataStore存快照基线。SensorCollector/SnapshotStore/SensorWorker/SensorScheduler。模拟器验证采集成功+快照持久化 |
| M9 活跃度计算上报 | ✅ 完成 | `b19abe4` | SensorWorker采集后上报POST /activity/report(7源components)+后端按好友矩阵计算+下发脱敏活跃度+存FriendsActivityStore。ActivityCalc权重常量。curl验证200 |
| M10 好友状态展示 | ✅ 完成 | `80a1981` | 好友列表展示活跃度进度条(0-100)+模糊时间(刚刚/活跃中/X分钟前/今天上午/离线等)+排序切换(活跃度/时间/昵称)。TimeFormat工具。模拟器启动无崩溃 |
| M11 互动(前端) | ✅ 完成 | `949a636` | 打卡页(状态选择+备注+历史，替换"我的"占位)+戳一戳按钮(好友详情页，限频提示，发起方置满)。InteractionDtos/Repository。模拟器启动无崩溃 |
| M12 联调上线 | ✅ 完成 | (本次提交) | 端到端联调19项全通过(注册→登录→加好友→上报→戳一戳→打卡→删除→单设备踢出)+README更新。Debug+Release构建无回归 |

**🎉 全部 12 个里程碑完成。项目开发结束。**

## 3. 版本管理规范（已固化，每个里程碑遵循）

1. 开 `feature/mN-xxx` 分支开发
2. 单个语义完整的提交，`feat(mN): ...` 前缀 + 详细 body
3. `git merge --no-ff` 合并到 `main`（保留分支节点）
4. 推送 feature 分支 + main
5. 提交前安全核查：无泄露密钥、无 `.env`、无本地 md 文档进入暂存区

## 4. 后端架构与关键决策（已定，勿重复纠结）

### 技术栈
- FastAPI + SQLAlchemy 2.0（同步）+ Alembic + PostgreSQL（生产）/ SQLite 内存（测试）
- APScheduler 3.11.2（活跃度衰减+离线扫描）
- bcrypt（密码哈希，直接用 bcrypt 包绕开 passlib 5.0 warning）+ python-jose（JWT）
- Resend（邮件验证码）

### 数据库表（迁移链 0001→0002→0003→0004）
- `users` / `devices`（会话表）/ `email_codes`
- `friendships`（对称双向行）/ `friend_requests` / `qr_tokens` / `friend_data_sources`（权限矩阵）/ `notifications`
- `activity_reports`（每 user×friend 一行可见值）
- `checkins` / `pokes`

### 关键决策记录
| 决策点 | 选择 | 理由 |
|--------|------|------|
| 验证码存储 | 数据库明文 | 用户选定（M1） |
| 单设备登录 | DB 会话表（devices.is_active） | 用户选定（M1）；JWT 带 device_id，get_current_user 查库确认仍 active |
| 测试数据库 | SQLite 内存 | 用户选定（M1）；conftest 覆盖 get_db + 禁用 scheduler + mock Resend |
| 活跃度置满钩子 | M1 留占位，M3 实现 | 用户选定（M1） |
| 按好友可见性 | 后端按矩阵计算 | 用户选定（M3）；前端上报原始分项，后端按 FriendDataSource 计算每好友可见值，原始分项不持久化 |
| 衰减速率 | 可配置 decay_rate_per_hour（默认 100/12，12h 衰到 0） | 用户选定（M3） |
| 前端 DI | 无 DI 框架，手写 ServiceLocator 单例 | 用户选定（M5）；项目中小型，避免 Hilt/Koin 编译开销 |
| 前端网络层 | Retrofit + OkHttp + Moshi | 用户选定（M5） |
| M5 范围 | 骨架+服务器配置+登录（含 M6 用户系统） | 用户选定（M5）；尽早联调后端 |
| 服务器地址 | 默认通过 default_server.properties 配置，用户可改+恢复默认 | 用户指定（M5） |
| 二维码扫描 | zxing-android-embedded Intent 扫码 + zxing-core 生成 | 用户选定（M7）；依赖轻、实现简单 |
| 传感器采集运行方式 | WorkManager 30分钟周期采集 + 本地存快照基线作下次参照 | 用户选定（M8）；免打扰轻量，非持续监听 |
| 删除/戳一戳通知下发 | 仅上报时返回（piggyback） | 用户选定（M2/M4）；严格贴合 PRD §6 |
| 打卡类型 | 固定枚举（起床/休息/运动/吃饭） | PRD §5.1 |
| 戳一戳限频 | poke_cooldown_seconds=3600（每小时1次） | PRD §5.2 |

### API 端点总览
- `/auth`: register, resend-code, verify, login, logout, me
- `/friends`: qrcode, add-by-qrcode, search, request(s), accept/reject, list, nickname, delete, data-sources, notifications
- `/activity`: report（上报+下发脱敏好友活跃度+通知）
- `/checkins`: create, list
- `/pokes/{friendship_id}`: 戳一戳

## 5. 本地特殊文件（不推送）

| 文件 | 状态 | 说明 |
|------|------|------|
| `backend/.env` | git-ignore | **含 Resend API Key**（已泄露的那个），下次务必提醒用户吊销重置 |
| `安心圈需求文档（PRD）.md` | git-ignore | 含明文密钥，不推送 |
| `安心圈编程计划.md` | git-ignore | 本地规划文档 |
| `android/local.properties` | git-ignore | 指向 Windows 侧 Android SDK（WSL 环境） |

## 6. ⚠️ 待办的安全提醒（持续提醒用户）

1. **Resend API Key 已泄露**：原 PRD 文档中明文写入了该密钥（已脱敏，见 `backend/.env`）。仅存于本地 `.env`（未推送），但**强烈建议到 Resend 后台吊销并重新生成**，届时只改 `backend/.env` 一处。
2. **JWT_SECRET 仍为占位值** `change-me-in-production`，生产前必须改强随机值。
3. 本地 `.env`、两份 md 文档已 git-ignore，每次提交前仍需核查暂存区不含它们。

## 7. 环境与工具链（WSL2 Linux）

- Python 3.12.3 + venv（`backend/.venv`）
- Java 17（OpenJDK）
- Docker + Compose
- Android SDK 在 Windows 侧：`/mnt/c/Users/lu/AppData/Local/Android/Sdk`（platforms 31-36, build-tools 35.0.0）
- Gradle 8.10.2（通过 wrapper，首次需联网下载；沙箱受限时可用本地下载的 `/tmp/gradle-8.10.2` 验证）
- Node 24（暂未用）

## 8. 常用验证命令

### 后端
```bash
cd /home/lu/git-projects/ruthere/backend
. .venv/bin/activate
pip install -e ".[dev]"          # 装依赖
pytest -v                         # 跑测试（当前 71 passed）
uvicorn app.main:app --reload     # 启服务，/health 探活
alembic upgrade head --sql        # 离线校验迁移 DDL
alembic heads                     # 查当前 head（应 0004）
```

### 前端（M5 起用）
```bash
cd /home/lu/git-projects/ruthere/android
./gradlew help                    # 校验工程配置
./gradlew compileDebugKotlin      # 编译
./gradlew testDebugUnitTest       # 单元测试
```

### Git 提交（每里程碑）
```bash
git checkout -b feature/mN-xxx
git add -A
# 核查：git diff --cached | grep -cE "re_Exy8"  应为 0（无泄露密钥）
git commit -F - <<'EOF' ... EOF
git push -u origin feature/mN-xxx
git checkout main
git merge --no-ff feature/mN-xxx -m "Merge ..."
git push origin main
```

## 9. 项目已完成

全部 12 个里程碑（M0–M12）完成。后续修复与改进：

| 日期 | 改动 | commit |
|------|------|--------|
| 06-23 | 邮件发送失败返回502；前端HTTP错误友好化；登录页跳设置不显示底部栏 | `c37251e` |
| 06-23 | network_security_config 放行任意IP明文HTTP | `191fb9e` |
| 06-23 | 修复预登录配置页"关于"按钮无反应 | `ea4ab5b` |

**最新 main：`ea4ab5b`**（2026-06-23）

如需后续迭代（30天趋势图、权重设置页、pytest覆盖率等），参考 `安心圈编程计划.md` 的「不做（留后续）」部分。

---

## 变更记录
- 2026-06-18：完成 M0-M4 后端全部功能，71 测试全绿，全部已推送 main。创建此 WORKLOG。
- 2026-06-22：修改前端规划 M5，新增服务器地址配置功能（默认 IP+端口通过 default_server.properties 配置，用户可改 + 一键恢复默认按钮）。
- 2026-06-22：完成 M5（含 M6 用户系统）——前端 App 骨架 + 服务器配置 + 注册/验证/登录 + App 图标；模拟器验证通过；已推送 main `e4cec89`。
- 2026-06-22：后端 Docker 打包到 docker/ 目录（已 git-ignore 不同步）；清华 PyPI 镜像；构建+启动+迁移+/health 全验证通过。
- 2026-06-22：完成 M7 前端好友系统——列表/添加(QR生成+扫码+搜索)/申请/详情(昵称+数据源+删除)；zxing 库；模拟器联调通过；已推送 main `514024f`。
- 2026-06-22：完成 M8 传感器采集——WorkManager 30分钟周期采集7类数据源+归一化+DataStore快照基线；模拟器验证采集成功+快照持久化；已推送 main `84f77c1`。
- 2026-06-23：完成 M9 活跃度计算上报——SensorWorker采集后上报POST /activity/report+存FriendsActivityStore；ActivityCalc权重常量；curl验证200；已推送 main `b19abe4`。
- 2026-06-23：完成 M10 好友状态展示——好友列表活跃度进度条+模糊时间+离线态+排序切换(活跃度/时间/昵称)；TimeFormat工具；模拟器启动无崩溃；已推送 main `80a1981`。
- 2026-06-23：完成 M11 互动UI——打卡页(状态选择+备注+历史)+戳一戳按钮(好友详情页，限频提示，发起方置满)；InteractionDtos/Repository；模拟器启动无崩溃；已推送 main `949a636`。
- 2026-06-23：加 About 页面（武汉三合鼎盛科技股份有限公司 2026 copyright）+ Release 签名配置（keystore git-ignore）；已推送 main `6d0246f`。
- 2026-06-23：完成 M12 联调上线——端到端联调19项全通过(注册→登录→加好友→上报→戳一戳→打卡→删除→单设备踢出)+README更新+Debug/Release构建无回归。**项目全部里程碑完成。**
- 2026-06-23：邮件发送失败返回错误信息(502) + 前端HTTP错误友好化(401→"邮箱或密码错误"等) + 登录页跳服务器设置时不显示底部导航栏。已推送 main `c37251e`。
- 2026-06-23：network_security_config 加 base-config 放行任意IP明文HTTP，用户可自由切换服务器地址。已推送 main `191fb9e`。
- 2026-06-23：修复未登录时从服务器配置页点"关于"按钮无反应的问题。已推送 main `ea4ab5b`。

# 安心圈 (RutThere)

在「位置共享」与「完全失联」之间，提供一种**免入侵、免打扰**的轻量级状态互通工具。
用户通过手机活动数据（非位置）生成「活跃度」数值，仅向好友传递模糊状态。

> 需求与计划见 [`安心圈需求文档（PRD）.md`](./安心圈需求文档（PRD）.md) 与 [`安心圈编程计划.md`](./安心圈编程计划.md)。

## 仓库结构

```
ruthere/
├── backend/          Python (FastAPI) 后端
├── android/          Kotlin (Jetpack Compose) Android App
├── docker-compose.yml
└── README.md
```

## 后端 (backend/)

| 项 | 说明 |
|----|------|
| 框架 | FastAPI + SQLAlchemy 2.0 + Alembic |
| 数据库 | PostgreSQL |
| 调度 | APScheduler（活跃度衰减 / 离线判定） |
| 邮件 | Resend（验证码） |

```bash
cd backend
cp .env.example .env          # 填入密钥（Resend Key 走环境变量，勿提交）
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload      # http://127.0.0.1:8000，/health 探活
pytest                             # 单元测试
alembic upgrade head               # 数据库迁移（需先起 PG）
```

一键起后端 + Postgres：
```bash
docker compose up --build
```

## 前端 (android/)

| 项 | 说明 |
|----|------|
| 语言 | Kotlin |
| UI | Jetpack Compose |
| 架构 | MVVM + Repository |
| 本地存储 | Room（M5+） |
| 网络 | Retrofit（M5+） |
| 后台任务 | WorkManager（M9+） |

```bash
cd android
# 首次：在 local.properties 指定 SDK 路径（已 git-ignore）
#   sdk.dir=/path/to/Android/Sdk
./gradlew help                      # 校验工程配置
./gradlew assembleDebug             # 构建 debug APK
./gradlew testDebugUnitTest         # 单元测试
```

> Gradle Wrapper 已包含（`gradlew` + `gradle/wrapper/gradle-wrapper.jar`）。
> 首次运行会自动下载 Gradle 8.10.2。

## ⚠️ 安全提醒

PRD 中曾明文写入 Resend API Key，该密钥已泄露。请**立即吊销并重新生成**，
新密钥仅通过环境变量注入（`backend/.env`，已 git-ignore），不得写入任何文档或代码。

## 里程碑

M0 项目骨架 ✅ → M1 用户系统 → M2 好友系统 → M3 活跃度 → M4 互动 →
M5–M11 前端各模块 → M12 联调上线。详见 [`安心圈编程计划.md`](./安心圈编程计划.md)。

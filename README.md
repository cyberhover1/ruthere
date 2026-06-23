# 安心圈 (RutThere)

在「位置共享」与「完全失联」之间，提供一种**免入侵、免打扰**的轻量级状态互通工具。
用户通过手机活动数据（非位置）生成「活跃度」数值，仅向好友传递模糊状态。

> 需求与计划见 `安心圈需求文档（PRD）.md` 与 `安心圈编程计划.md`（本地文档，未入库）。
> 工作状态与进度见 [`WORKLOG.md`](./WORKLOG.md)。

## 仓库结构

```
ruthere/
├── backend/          Python (FastAPI) 后端
├── android/          Kotlin (Jetpack Compose) Android App
├── docker-compose.yml
├── WORKLOG.md        跨会话工作日志
└── README.md
```

## 技术栈

| 端 | 技术 |
|----|------|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · APScheduler · Resend |
| 前端 | Kotlin · Jetpack Compose · Retrofit/OkHttp/Moshi · DataStore · WorkManager · ZXing |
| 架构 | 后端 FastAPI + 单设备登录 JWT；前端 MVVM + Repository + ServiceLocator（无 DI 框架） |
| 通信 | 无推送、无轮询；前端 30 分钟周期采集+上报，后端顺带下发好友脱敏活跃度+通知 |

## 后端 (backend/)

### 本地开发
```bash
cd backend
cp .env.example .env          # 填入密钥（Resend Key / JWT_SECRET 走环境变量，勿提交）
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload      # http://127.0.0.1:8000
pytest                             # 单元测试（71 passed）
alembic upgrade head               # 数据库迁移
```

### Docker 部署
```bash
cd docker
cp .env.example .env              # 填入 JWT_SECRET / RESEND_API_KEY
docker compose up --build         # 后端 + Postgres，监听 8000
```
启动时自动执行 `alembic upgrade head`（迁移 0001→0004）。

### API 文档
服务启动后访问 `http://<host>:8000/docs`（FastAPI 自动生成 OpenAPI）。
共 24 个端点：auth(6) + friends(13) + activity(1) + checkins(2) + pokes(1) + health(1)。

## 前端 (android/)

### 构建
```bash
cd android
# 首次：local.properties 指定 SDK 路径（已 git-ignore）
#   sdk.dir=/path/to/Android/Sdk

./gradlew assembleDebug            # debug APK（调试签名）
./gradlew assembleRelease          # release APK（需 keystore.properties，见下）
./gradlew testDebugUnitTest        # 单元测试
```

### Release 签名
Release 构建需 `android/keystore.properties`（已 git-ignore，不入库）：
```properties
storeFile=ruthere.jks
storePassword=<your-password>
keyAlias=ruthere
keyPassword=<your-password>
```
keystore 生成：
```bash
keytool -genkeypair -v -keystore ruthere.jks -keyalg RSA -keysize 2048 -validity 36500 -alias ruthere
```
⚠️ **务必备份 keystore + 密码**——丢失后无法给 App 升级（同签名要求）。

### 服务器地址配置
App 默认连 `http://110.42.251.26:8000`，可在「设置 → 服务器」页修改 IP/端口（含「恢复默认」按钮）。

## ⚠️ 安全提醒

1. **Resend API Key**：PRD 中曾明文写入，已泄露。请到 Resend 后台**吊销并重新生成**，新密钥仅通过 `backend/.env` 注入（已 git-ignore）。
2. **JWT_SECRET**：生产前必须改为强随机值（默认为占位符 `change-me-in-production`）。
3. **keystore**：`ruthere.jks` + `keystore.properties` 已 git-ignore，不入库，务必备份。
4. **脱敏**：上报原始分项仅在内存计算，不持久化；下发给好友的数据仅含 value/time/offline（PRD §4.5）。

## 里程碑

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M0 | 项目骨架 | ✅ |
| M1 | 后端用户系统（注册/验证/登录/单设备） | ✅ |
| M2 | 后端好友系统（QR/搜索/申请/数据源矩阵） | ✅ |
| M3 | 后端活跃度系统（上报/衰减/离线/置满） | ✅ |
| M4 | 后端互动功能（打卡/戳一戳） | ✅ |
| M5 | 前端骨架+服务器配置+登录 | ✅ |
| M7 | 前端好友系统 | ✅ |
| M8 | 前端传感器采集 | ✅ |
| M9 | 前端活跃度计算上报 | ✅ |
| M10 | 前端好友状态展示 | ✅ |
| M11 | 前端互动 UI（打卡/戳一戳） | ✅ |
| M12 | 联调上线 | ✅ |

**全部 12 个里程碑完成。** 后端 71 测试全绿，端到端联调 19 项全通过。

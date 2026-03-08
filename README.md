# Secemumod — 加密贴图资产保护 Demo

[English](README_EN.md)

## 目的

**Secemumod** 面向开源模拟器生态，解决**贴图纹理资产不受保护**的行业痛点。

在开源模拟器中，贴图加载前后状态不一致：加载前为加密资产，加载到游戏中后变为明文，创作者精心制作的贴图纹理可被随意提取、二次分发，缺乏有效保护。Secemumod 通过**鉴权 + 内存解密、不落盘**的方案，让加密贴图仅在授权场景下于内存中解密并挂载，明文**不写入磁盘**，从而保护模拟器游戏作者的贴图资产。

---

## 核心思想

> 加密资产经鉴权后下载，解密在内存中完成，明文仅用于展示/挂载，**不写入磁盘**。

- **加载前**：.aimg1 加密文件，无法直接使用
- **鉴权后**：服务端下发 DEK，客户端内存解密
- **加载后**：明文仅存在于进程内存，用于渲染，**不落盘**

---

## 适用场景

- 开源模拟器（PCSX2、Dolphin、RPCS3 等）的贴图 MOD 托管
- 贴图加载前后状态不一致、资产易被提取的痛点
- 创作者希望保护纹理资产、防止未授权分发的需求

---

## 完成状态

| 组件 | 状态 | 说明 |
|------|------|------|
| **Backend** | ✅ 完成 | Spring Boot：登录、batch-launch-secure、mod 下载 |
| **MVP Client** | ✅ 完成 | Python：登录 → 鉴权 → 下载 → 内存解密 → 窗口显示 |
| **Seed Script** | ✅ 完成 | 预置用户、mod、加密密钥、.aimg1 测试图 |

---

## 项目结构

```
demo/
├── backend/                 # 组件 1：后端
│   ├── Dockerfile
│   ├── src/main/java/
│   └── src/main/resources/
├── mvp-client/
│   └── main.py              # 组件 2：客户端
├── scripts/
│   ├── seed.py              # 种子脚本
│   └── wait-for-mysql.py    # Docker 启动等待
├── docker-compose.yml       # 一键部署
├── Dockerfile.seed          # 种子镜像
├── requirements.txt
├── .env.example
└── README.md
```

---

## 架构

```
┌─────────────┐         ┌──────────────────┐
│   Backend   │◄═══════►│  MVP Client      │
│ (Spring Boot)│         │   (Python)       │
└──────┬──────┘         └────────┬─────────┘
       │                         │
  Auth + DEK              HTTP Auth/Download
  Download URL            In-Memory Decrypt
                          → Display Image
                          (Never touches disk)
```

---

## 快速开始

### 方式一：一键部署（Docker）

**前置条件**：Docker & Docker Compose

> **国内网络**：若拉取镜像超时，请在 Docker Desktop → Settings → Docker Engine 中配置 `registry-mirrors`，例如 `["https://docker.1ms.run"]`

```bash
cd demo
docker compose up -d
```

等待约 1–2 分钟（首次会构建镜像），后端将监听 `http://localhost:8080`。然后运行客户端：

```bash
pip install -r demo/requirements.txt
python demo/mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
```

停止服务：`docker compose down`

---

### 方式二：本地运行

**前置条件**：Java 17+、Maven 3.6+、MySQL 8.0+、Python 3.8+

### 步骤 1：安装 Python 依赖

```bash
pip install -r demo/requirements.txt
```

### 步骤 2：种子数据

创建 `secemumod_demo` 数据库，插入测试用户、mod、加密密钥，并生成 .aimg1 测试图：

```bash
python demo/scripts/seed.py --db-password root
```

脚本会输出 **Mod ID**（通常为 1），后续步骤需要用到。

### 步骤 3：启动后端

```bash
mvn -f demo/backend/pom.xml spring-boot:run
```

后端监听 `http://localhost:8080`。

### 步骤 4：运行客户端

```bash
python demo/mvp-client/main.py --mod-id 1
```

将 `1` 替换为 seed 脚本输出的 Mod ID。窗口将显示**解密后的图片**，全程在内存中完成，不落盘。

### 可选参数

```bash
python demo/mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
python demo/mvp-client/main.py --mod-id 1 --username player1 --password player123
```

---

## 流程说明

1. **登录**：客户端 POST `/api/v1/auth/login`，获取 JWT
2. **鉴权**：POST `/api/v1/mod/batch-launch-secure`，获取 `encryptedDek`、`downloadUrl`
3. **下载**：GET `downloadUrl`，将 .aimg1 读入内存（不写磁盘）
4. **内存解密**：Base64 解码 DEK → 解析 AIMG1 头部 → AES-256-GCM 解密
5. **显示**：PNG 解码后在窗口展示，明文仅存在于进程内存

---

## AIMG1 格式

```
┌───────┬─────────┬──────────┬──────────────┬────────────────────────┐
│ AIMG  │ Version │  Nonce   │ Original Size│  Ciphertext + Tag(16B) │
│ (4B)  │  (1B)   │  (12B)   │   (8B LE)    │                        │
└───────┴─────────┴──────────┴──────────────┴────────────────────────┘
```

- **加密**：AES-256-GCM
- **密钥**：DEK，数据库中由 MasterKey 加密存储
- **Nonce**：12 字节，存于 AIMG1 头部

---

## 配置

见 `.env.example`。主要变量：`DB_PASSWORD`、`JWT_SECRET`、`ENCRYPTION_MASTER_KEY`。

---

## 打包为 exe（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --name secemumod_client demo/mvp-client/main.py
```

---

## 常见问题

| 问题 | 处理 |
|------|------|
| `authorizedMods is empty` | 先执行 seed 脚本，确认 mod 已插入且 status=APPROVED |
| MySQL 连接失败 | 检查 MySQL 已启动，`--db-password` 与本地一致 |
| 图片解码失败 | 确认 seed 生成的 .aimg1 与 backend storage 路径一致 |
| 后端 401 | 检查用户名密码与 seed 中一致（默认 player1/player123） |

---

## License

MIT

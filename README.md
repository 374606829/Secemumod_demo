<div align="center">

# Secemumod — 加密贴图资产保护 Demo

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Spring Boot 3.2+](https://img.shields.io/badge/Spring%20Boot-3.2+-brightgreen)](https://spring.io/projects/spring-boot)
[![Java 17](https://img.shields.io/badge/Java-17-orange)](https://openjdk.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/374606829/Secemumod_demo/pulls)
[![Star on GitHub](https://img.shields.io/github/stars/374606829/Secemumod_demo?style=social)](https://github.com/374606829/Secemumod_demo)

[English](README_EN.md)

</div>

---

## 背景故事

创作者精心制作的贴图 MOD 发布后，往往 24 小时内就被提取、倒卖。Secemumod 用企业级加密技术保护小众创作——鉴权 + 内存解密、不落盘，让资产仅在授权场景下可用。这不是玩具 Demo，而是面向真实社区的可落地方案。

---

## 核心思想

> 加密资产经鉴权后下载，解密在内存中完成，明文仅用于展示/挂载，**不写入磁盘**。

- **加载前**：.aimg1 加密文件，无法直接使用
- **鉴权后**：服务端下发 DEK，客户端内存解密
- **加载后**：明文仅存在于进程内存，用于渲染，**不落盘**

---

## 演示效果

![Demo](./1.gif)

---

## 一键启动

```bash
git clone https://github.com/374606829/Secemumod_demo.git
cd Secemumod_demo
docker compose up -d
pip install -r requirements.txt
python mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
```

> 需要 Docker。首次构建约 1–2 分钟。国内网络可配置 [Docker 镜像加速](https://docs.docker.com/registry/recipes/mirror/)。

---

## 适用场景

- 开源模拟器（PCSX2、Dolphin、RPCS3 等）的贴图 MOD 托管
- 贴图加载前后状态不一致、资产易被提取的痛点
- 创作者希望保护纹理资产、防止未授权分发的需求

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Spring Boot 3.2、Java 17、MySQL 8、JWT |
| 客户端 | Python 3.8+、AES-256-GCM、Pillow |
| 部署 | Docker、Docker Compose |

---

## 项目结构

```
Secemumod_demo/
├── backend/                 # 后端（Spring Boot）
│   ├── Dockerfile
│   └── src/main/
├── mvp-client/
│   └── main.py              # 客户端（登录→鉴权→解密→显示）
├── scripts/
│   ├── seed.py              # 种子脚本
│   └── wait-for-mysql.py
├── docker-compose.yml       # 一键部署
├── Dockerfile.seed
├── requirements.txt
└── .env.example
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

## 快速开始（详细）

### 方式一：Docker 一键部署

```bash
docker compose up -d
# 等待 1–2 分钟后
pip install -r requirements.txt
python mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
```

停止：`docker compose down`

### 方式二：本地运行

**前置**：Java 17+、Maven 3.6+、MySQL 8.0+、Python 3.8+

```bash
# 1. 种子数据
python scripts/seed.py --db-password root

# 2. 启动后端
mvn -f backend/pom.xml spring-boot:run

# 3. 运行客户端（mod-id 以 seed 输出为准）
python mvp-client/main.py --mod-id 1
```

---

## 流程说明

1. **登录** → POST `/api/v1/auth/login`，获取 JWT
2. **鉴权** → POST `/api/v1/mod/batch-launch-secure`，获取 `encryptedDek`、`downloadUrl`
3. **下载** → GET `downloadUrl`，.aimg1 读入内存（不写磁盘）
4. **内存解密** → Base64 解码 DEK → AES-256-GCM 解密 AIMG1
5. **显示** → PNG 解码，窗口展示，明文仅存于进程内存

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

### 打包为 exe（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --name secemumod_client mvp-client/main.py
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

## 未来计划

- [ ] 支持更多模拟器（Dolphin、RPCS3）
- [ ] 提供 Web 管理界面
- [ ] 发布 Rust 安全服务的独立库
- [ ] 集成硬件安全模块（TPM）可选方案

---

## 贡献

欢迎提 Issue 和 PR！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## License

MIT

---

<div align="center">

**如果这个项目对你有帮助，或你觉得它有意思，请给一个 ⭐ Star，让更多创作者看到！**

</div>

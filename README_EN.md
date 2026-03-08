<div align="center">

# Secemumod — Encrypted Texture Asset Protection Demo

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Spring Boot 3.2+](https://img.shields.io/badge/Spring%20Boot-3.2+-brightgreen)](https://spring.io/projects/spring-boot)
[![Java 17](https://img.shields.io/badge/Java-17-orange)](https://openjdk.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/374606829/Secemumod_demo/pulls)
[![Star on GitHub](https://img.shields.io/github/stars/374606829/Secemumod_demo?style=social)](https://github.com/374606829/Secemumod_demo)

[中文](README.md)

</div>

---

## Background

Creators' texture MODs are often extracted and resold within 24 hours of release. Secemumod protects niche creations with enterprise-grade encryption — auth + in-memory decryption, never written to disk. This is not a toy demo; it's a deployable solution for real communities.

---

## Core Concept

> Encrypted assets are downloaded after authentication, decrypted **in memory**, and plaintext is used only for display/mounting — **never written to disk**.

- **Before load**: .aimg1 encrypted file, unusable directly
- **After auth**: Server delivers DEK, client decrypts in memory
- **After load**: Plaintext exists only in process memory for rendering, **never touches disk**

---

## Demo

![Demo](./1.gif)

---

## One-Line Start

```bash
git clone https://github.com/374606829/Secemumod_demo.git
cd Secemumod_demo
docker compose up -d
pip install -r requirements.txt
python mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
```

> Requires Docker. First build takes ~1–2 minutes. Configure [Docker registry mirror](https://docs.docker.com/registry/recipes/mirror/) if needed.

---

## Use Cases

- Texture MOD hosting for open-source emulators (PCSX2, Dolphin, RPCS3, etc.)
- Pain point: inconsistent texture state before/after loading, assets easily extracted
- Creators seeking to protect texture assets and prevent unauthorized redistribution

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Spring Boot 3.2, Java 17, MySQL 8, JWT |
| Client | Python 3.8+, AES-256-GCM, Pillow |
| Deploy | Docker, Docker Compose |

---

## Project Structure

```
Secemumod_demo/
├── backend/                 # Backend (Spring Boot)
│   ├── Dockerfile
│   └── src/main/
├── mvp-client/
│   └── main.py              # Client (login → auth → decrypt → display)
├── scripts/
│   ├── seed.py
│   └── wait-for-mysql.py
├── docker-compose.yml
├── Dockerfile.seed
├── requirements.txt
└── .env.example
```

---

## Architecture

```
┌─────────────┐         ┌──────────────────┐
│   Backend   │◄═══════►│  MVP Client      │
│ (Spring Boot)│         │   (Python)        │
└──────┬──────┘         └────────┬─────────┘
       │                         │
  Auth + DEK              HTTP Auth/Download
  Download URL            In-Memory Decrypt
                          → Display Image
                          (Never touches disk)
```

---

## Quick Start (Detailed)

### Option 1: Docker

```bash
docker compose up -d
# Wait 1–2 minutes, then:
pip install -r requirements.txt
python mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
```

Stop: `docker compose down`

### Option 2: Local Run

**Prerequisites**: Java 17+, Maven 3.6+, MySQL 8.0+, Python 3.8+

```bash
# 1. Seed database
python scripts/seed.py --db-password root

# 2. Start backend
mvn -f backend/pom.xml spring-boot:run

# 3. Run client (use mod-id from seed output)
python mvp-client/main.py --mod-id 1
```

---

## Flow

1. **Login** → POST `/api/v1/auth/login`, receive JWT
2. **Auth** → POST `/api/v1/mod/batch-launch-secure`, receive `encryptedDek`, `downloadUrl`
3. **Download** → GET `downloadUrl`, load .aimg1 into memory (no disk write)
4. **In-memory decrypt** → Base64 decode DEK → AES-256-GCM decrypt AIMG1
5. **Display** → Decode PNG, show in window; plaintext only in process memory

---

## AIMG1 Format

```
┌───────┬─────────┬──────────┬──────────────┬────────────────────────┐
│ AIMG  │ Version │  Nonce   │ Original Size│  Ciphertext + Tag(16B) │
│ (4B)  │  (1B)   │  (12B)   │   (8B LE)    │                        │
└───────┴─────────┴──────────┴──────────────┴────────────────────────┘
```

- **Encryption**: AES-256-GCM
- **Key**: DEK, stored encrypted by MasterKey in database
- **Nonce**: 12 bytes, stored in AIMG1 header

---

## Configuration

See `.env.example`. Main variables: `DB_PASSWORD`, `JWT_SECRET`, `ENCRYPTION_MASTER_KEY`.

### Pack as exe (Optional)

```bash
pip install pyinstaller
pyinstaller --onefile --name secemumod_client mvp-client/main.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `authorizedMods is empty` | Run seed script first; ensure mod has status=APPROVED |
| MySQL connection failed | Ensure MySQL is running; `--db-password` matches local |
| Image decode failed | Ensure seed .aimg1 path matches backend storage |
| Backend 401 | Check username/password match seed (default player1/player123) |

---

## Roadmap

- [ ] Support more emulators (Dolphin, RPCS3)
- [ ] Web management UI
- [ ] Publish Rust security service as standalone library
- [ ] Optional TPM integration

---

## Contributing

Issues and PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT

---

<div align="center">

**If this project helps you or you find it interesting, please give it a ⭐ Star so more creators can discover it!**

</div>

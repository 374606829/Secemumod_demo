# Secemumod — Encrypted Texture Asset Protection Demo

[中文](README.md)

## Purpose

**Secemumod** addresses the industry pain point of **unprotected texture assets** in open-source emulator ecosystems.

In open-source emulators, texture loading exhibits inconsistent state before and after: assets are encrypted before loading, but become plaintext once loaded into the game. Creators' texture assets can be freely extracted and redistributed without effective protection. Secemumod solves this with **auth + in-memory decryption without disk writes**: encrypted textures are decrypted and mounted only in authorized contexts, with plaintext **never written to disk**, protecting emulator game authors' texture assets.

---

## Core Concept

> Encrypted assets are downloaded after authentication, decrypted **in memory**, and plaintext is used only for display/mounting — **never written to disk**.

- **Before load**: .aimg1 encrypted file, unusable directly
- **After auth**: Server delivers DEK, client decrypts in memory
- **After load**: Plaintext exists only in process memory for rendering, **never touches disk**

---

## Use Cases

- Texture MOD hosting for open-source emulators (PCSX2, Dolphin, RPCS3, etc.)
- Pain point: inconsistent texture state before/after loading, assets easily extracted
- Creators seeking to protect texture assets and prevent unauthorized redistribution

---

## Status

| Component | Status | Description |
|-----------|--------|-------------|
| **Backend** | ✅ Done | Spring Boot: login, batch-launch-secure, mod download |
| **MVP Client** | ✅ Done | Python: login → auth → download → in-memory decrypt → display in window |
| **Seed Script** | ✅ Done | Pre-seeds user, mod, encryption key, .aimg1 test image |

---

## Project Structure

```
demo/
├── backend/                 # Component 1: Backend
│   ├── src/main/java/      # AuthController, ModController, MvpService
│   ├── src/main/resources/
│   │   ├── application.yml
│   │   └── db/schema.sql
│   └── storage/mods/        # .aimg1 file storage (created by seed)
├── mvp-client/
│   └── main.py              # Component 2: Client (can be packed as exe via pyinstaller)
├── scripts/
│   └── seed.py              # Seed script
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── README.md
```

---

## Architecture

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

## Quick Start

### Option 1: One-Click Deploy (Docker)

**Prerequisites**: Docker & Docker Compose

```bash
cd demo
docker compose up -d
```

Wait 1–2 minutes (first run builds images). Backend listens on `http://localhost:8080`. Then run the client:

```bash
pip install -r demo/requirements.txt
python demo/mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
```

Stop: `docker compose down`

---

### Option 2: Local Run

**Prerequisites**: Java 17+, Maven 3.6+, MySQL 8.0+, Python 3.8+

### Step 1: Install Python Dependencies

```bash
pip install -r demo/requirements.txt
```

### Step 2: Seed Database

Creates `secemumod_demo` database, inserts test user, mod, encryption key, and generates .aimg1 test image:

```bash
python demo/scripts/seed.py --db-password root
```

The script prints the **Mod ID** (usually 1) — you'll need it for the next steps.

### Step 3: Start Backend

```bash
mvn -f demo/backend/pom.xml spring-boot:run
```

Backend listens on `http://localhost:8080`.

### Step 4: Run Client

```bash
python demo/mvp-client/main.py --mod-id 1
```

Replace `1` with the Mod ID from the seed script. A window will show the **decrypted image** — entirely in memory, never written to disk.

### Optional Arguments

```bash
python demo/mvp-client/main.py --mod-id 1 --base-url http://localhost:8080
python demo/mvp-client/main.py --mod-id 1 --username player1 --password player123
```

---

## Flow

1. **Login**: Client POSTs `/api/v1/auth/login`, receives JWT
2. **Auth**: POST `/api/v1/mod/batch-launch-secure`, receives `encryptedDek`, `downloadUrl`
3. **Download**: GET `downloadUrl`, load .aimg1 into memory (no disk write)
4. **In-memory decrypt**: Base64 decode DEK → parse AIMG1 header → AES-256-GCM decrypt
5. **Display**: Decode PNG and show in window; plaintext exists only in process memory

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

---

## Pack as exe (Optional)

```bash
pip install pyinstaller
pyinstaller --onefile --name secemumod_client demo/mvp-client/main.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `authorizedMods is empty` | Run seed script first; ensure mod is inserted with status=APPROVED |
| MySQL connection failed | Ensure MySQL is running; `--db-password` matches local config |
| Image decode failed | Ensure seed-generated .aimg1 path matches backend storage |
| Backend 401 | Check username/password match seed (default player1/player123) |

---

## License

MIT

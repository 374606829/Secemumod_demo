#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed script: pre-populate test data (user, mod, encryption key, .aimg1 file).

Usage:
  python scripts/seed.py [--db-password root]

Dependencies: pip install pymysql pycryptodome Pillow bcrypt
"""

import argparse
import base64
import io
import os
import struct
import sys

DEMO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STORAGE_DIR = os.path.join(DEMO_DIR, "backend", "storage", "mods")

# Must match mvp.encryption.master-key default in application.yml
DEFAULT_MASTER_KEY_B64 = "cGxlYXNlQ2hhbmdlTWVJbkpKaW9uQXVnVUtWYWx1ZQA="

# Fixed test DEK (32 bytes)
TEST_DEK = b"DEMO_MVP_TEST_DEK_32BYTES_OK!!"[:32].ljust(32, b"\x00")

# Test user
TEST_USER = "player1"
TEST_PASS = "player123"

# Test mod
TEST_MOD_TITLE = "MVP Demo Mod"
TEST_AIMG1_FILENAME = "demo_test.png.aimg1"


def create_test_image_png():
    """Create a small valid PNG image in memory using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (400, 300), color=(30, 30, 60))
    draw = ImageDraw.Draw(img)

    # Draw a gradient-like background
    for y in range(300):
        r = int(30 + (y / 300) * 60)
        g = int(30 + (y / 300) * 180)
        b = int(60 + (y / 300) * 120)
        draw.line([(0, y), (399, y)], fill=(r, g, b))

    # Draw text
    try:
        font = ImageFont.truetype("arial.ttf", 28)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except (OSError, IOError):
        font = ImageFont.load_default()
        small_font = font

    draw.text((60, 80), "Encrypted Asset", fill=(255, 255, 255), font=font)
    draw.text((60, 120), "Demo MVP", fill=(100, 220, 255), font=font)
    draw.text((60, 180), "In-Memory Decrypted", fill=(180, 255, 180), font=small_font)
    draw.text((60, 210), "Never Written to Disk", fill=(255, 180, 180), font=small_font)

    # Draw a lock icon (simple)
    draw.rectangle([(300, 50), (370, 100)], outline=(255, 215, 0), width=2)
    draw.arc([(315, 20), (355, 60)], 0, 180, fill=(255, 215, 0), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def encrypt_aimg1(png_bytes, dek):
    """
    Encrypt PNG into AIMG1 format:
    Header: AIMG(4B) + 0x02(1B) + nonce(12B) + originalSize(8B LE)
    Body: ciphertext + tag(16B)
    """
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes

    nonce = get_random_bytes(12)
    cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(png_bytes)

    header = b"AIMG" + b"\x02" + nonce + struct.pack("<Q", len(png_bytes))
    return header + ciphertext + tag


def encrypt_dek_with_master(dek, master_key):
    """
    Encrypt DEK with MasterKey using AES-256-GCM.
    Returns Base64(iv[12] + ciphertext + tag[16]).
    """
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes

    iv = get_random_bytes(12)
    cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(dek)
    return base64.b64encode(iv + ct + tag).decode("ascii")


def main():
    ap = argparse.ArgumentParser(description="Seed demo database with test data")
    ap.add_argument("--db-host", default=os.environ.get("DB_HOST", "localhost"),
                    help="MySQL host (default: localhost, use 'mysql' in Docker)")
    ap.add_argument("--db-port", type=int, default=int(os.environ.get("DB_PORT", "3306")),
                    help="MySQL port (default: 3306)")
    ap.add_argument("--db-password", default=os.environ.get("DB_PASSWORD", "root"),
                    help="MySQL root password (default: root)")
    ap.add_argument("--db-user", default=os.environ.get("DB_USERNAME", "root"),
                    help="MySQL user (default: root)")
    ap.add_argument("--master-key", default=os.environ.get("ENCRYPTION_MASTER_KEY", DEFAULT_MASTER_KEY_B64),
                    help="MasterKey Base64")
    ap.add_argument("--storage-dir", default=os.environ.get("STORAGE_DIR"),
                    help="Override storage dir for .aimg1 (default: demo/backend/storage/mods)")
    ap.add_argument("--schema-path", default=None,
                    help="Override path to schema.sql (default: demo/backend/src/main/resources/db/schema.sql)")
    args = ap.parse_args()

    try:
        import pymysql
    except ImportError:
        print("[ERROR] pip install pymysql")
        return 1
    try:
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
    except ImportError:
        print("[ERROR] pip install pycryptodome")
        return 1
    try:
        from PIL import Image
    except ImportError:
        print("[ERROR] pip install Pillow")
        return 1

    master_key = base64.b64decode(args.master_key)
    if len(master_key) != 32:
        print("[ERROR] MasterKey must be 32 bytes, got", len(master_key))
        return 1

    # --- Read schema.sql and execute ---
    schema_path = args.schema_path or os.path.join(DEMO_DIR, "backend", "src", "main", "resources", "db", "schema.sql")
    if not os.path.exists(schema_path):
        print("[ERROR] schema.sql not found at", schema_path)
        return 1

    print("[*] Connecting to MySQL...")
    try:
        conn = pymysql.connect(
            host=args.db_host, port=args.db_port,
            user=args.db_user, password=args.db_password,
            charset="utf8mb4",
            autocommit=True,
        )
    except Exception as e:
        print("[ERROR] Cannot connect to MySQL:", e)
        return 1

    cur = conn.cursor()

    print("[*] Creating database and tables...")
    # First create the database and use it
    cur.execute("CREATE DATABASE IF NOT EXISTS secemumod_demo DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci")
    cur.execute("USE secemumod_demo")

    # Then execute table creation statements from schema.sql
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    # Split by semicolons and execute each statement (skip DB creation / USE since we did it above)
    for stmt in sql.split(";"):
        # Remove comment lines
        lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
        clean = "\n".join(lines).strip()
        if not clean:
            continue
        # Skip CREATE DATABASE and USE (already done)
        upper = clean.upper()
        if upper.startswith("CREATE DATABASE") or upper.startswith("USE "):
            continue
        try:
            cur.execute(clean)
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"  [WARN] {e}")

    # --- Insert test user ---
    from bcrypt import hashpw, gensalt
    try:
        hashed = hashpw(TEST_PASS.encode(), gensalt()).decode()
    except ImportError:
        # fallback: use Spring Security compatible BCrypt
        from passlib.hash import bcrypt as bcrypt_hash
        hashed = bcrypt_hash.hash(TEST_PASS)

    cur.execute("DELETE FROM sys_user WHERE username = %s", (TEST_USER,))
    cur.execute(
        "INSERT INTO sys_user (username, password, role) VALUES (%s, %s, 'USER')",
        (TEST_USER, hashed)
    )
    print(f"[OK] User created: {TEST_USER} / {TEST_PASS}")

    # --- Insert test mod ---
    cur.execute("SELECT id FROM sys_user WHERE username = %s", (TEST_USER,))
    user_id = cur.fetchone()[0]

    cur.execute("DELETE FROM mod_info WHERE title = %s", (TEST_MOD_TITLE,))
    cur.execute(
        "INSERT INTO mod_info (title, status, creator_id) VALUES (%s, 'APPROVED', %s)",
        (TEST_MOD_TITLE, user_id)
    )
    mod_id = cur.lastrowid
    print(f"[OK] Mod created: id={mod_id}, title={TEST_MOD_TITLE}")

    # --- Encrypt DEK with MasterKey ---
    file_key_encrypted_b64 = encrypt_dek_with_master(TEST_DEK, master_key)
    cur.execute("DELETE FROM mod_encryption_key WHERE mod_id = %s", (mod_id,))
    cur.execute(
        """INSERT INTO mod_encryption_key
           (mod_id, file_key_encrypted, key_version, encryption_algorithm, creator_id, is_active)
           VALUES (%s, %s, 'v1', 'AES-256', %s, 1)""",
        (mod_id, file_key_encrypted_b64, user_id)
    )
    print(f"[OK] Encryption key inserted for mod {mod_id}")

    # --- Create .aimg1 test file ---
    print("[*] Generating test PNG image...")
    png_bytes = create_test_image_png()
    print(f"[OK] PNG generated: {len(png_bytes)} bytes")

    aimg1_data = encrypt_aimg1(png_bytes, TEST_DEK)
    print(f"[OK] AIMG1 encrypted: {len(aimg1_data)} bytes")

    storage_dir = args.storage_dir or DEFAULT_STORAGE_DIR
    mod_storage = os.path.join(storage_dir, str(mod_id))
    os.makedirs(mod_storage, exist_ok=True)
    aimg1_path = os.path.join(mod_storage, TEST_AIMG1_FILENAME)
    with open(aimg1_path, "wb") as f:
        f.write(aimg1_data)
    abs_path = os.path.abspath(aimg1_path)
    print(f"[OK] AIMG1 file written: {abs_path}")

    # --- Insert mod_file ---
    cur.execute("DELETE FROM mod_file WHERE mod_id = %s", (mod_id,))
    cur.execute(
        """INSERT INTO mod_file
           (mod_id, file_name, file_path, file_size, encryption_format)
           VALUES (%s, %s, %s, %s, 'AIMG1')""",
        (mod_id, TEST_AIMG1_FILENAME, abs_path, len(aimg1_data))
    )
    print(f"[OK] mod_file inserted: {TEST_AIMG1_FILENAME}")

    cur.close()
    conn.close()

    print()
    print("=" * 60)
    print("  Seed completed successfully!")
    print(f"  User: {TEST_USER} / {TEST_PASS}")
    print(f"  Mod ID: {mod_id}")
    print(f"  AIMG1: {abs_path}")
    print()
    print("  Next steps:")
    print("  1. Start backend:  mvn -f backend/pom.xml spring-boot:run")
    print(f"  2. Run client:     python mvp-client/main.py --mod-id {mod_id}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

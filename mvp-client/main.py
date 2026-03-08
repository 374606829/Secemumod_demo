#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小 MVP 客户端：登录 → 鉴权 → 下载 .aimg1 → 内存解密 → 窗口显示图片（不落盘）

核心思想：加密资产经鉴权后下载，解密在内存中完成，明文仅用于展示，不写入磁盘。

用法:
  python demo/mvp-client/main.py --mod-id 1

  # 自定义后端地址
  python demo/mvp-client/main.py --mod-id 1 --base-url http://localhost:8080

  # 指定用户名密码
  python demo/mvp-client/main.py --mod-id 1 --username player1 --password player123

依赖: pip install requests pycryptodome Pillow
"""

import argparse
import base64
import io
import os
import struct
import sys
import time

# ──────────────────── Constants ────────────────────

DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_USERNAME = "player1"
DEFAULT_PASSWORD = "player123"
TIMEOUT = 30


# ──────────────────── Logging ────────────────────

def log(msg, level="INFO"):
    ts = time.strftime("%H:%M:%S")
    icons = {"INFO": "ℹ️ ", "OK": "✅", "FAIL": "❌", "STEP": "🔹"}
    icon = icons.get(level, "  ")
    print(f"[{ts}] {icon} {msg}")


# ──────────────────── HTTP Helpers ────────────────────

def api_login(base_url, username, password):
    """POST /api/v1/auth/login → token"""
    import requests

    url = f"{base_url}/api/v1/auth/login"
    log(f"POST {url}", "STEP")
    r = requests.post(url, json={"username": username, "password": password}, timeout=TIMEOUT)
    if r.status_code != 200:
        log(f"HTTP {r.status_code}", "FAIL")
        return None
    data = r.json()
    if data.get("code") != 200:
        log(f"Login failed: {data.get('msg', 'unknown')}", "FAIL")
        return None
    token = data.get("data", {}).get("token")
    if not token:
        log("No token in response", "FAIL")
        return None
    return token


def api_batch_launch(base_url, mod_id, token):
    """POST /api/v1/mod/batch-launch-secure → (encryptedDek, downloadUrl)"""
    import requests

    url = f"{base_url}/api/v1/mod/batch-launch-secure"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "selectedModIds": [mod_id],
        "deviceCode": "DEV_MVP",
        "clientPublicKey": "",  # MVP: no RSA needed
    }
    log(f"POST {url}", "STEP")
    r = requests.post(url, json=body, headers=headers, timeout=TIMEOUT)
    if r.status_code != 200:
        log(f"HTTP {r.status_code}", "FAIL")
        return None, None
    data = r.json()
    if data.get("code") != 200:
        log(f"batch-launch error: {data.get('msg', 'unknown')}", "FAIL")
        return None, None
    auth_mods = data.get("data", {}).get("authorizedMods", [])
    if not auth_mods:
        log("authorizedMods is empty", "FAIL")
        return None, None
    am = auth_mods[0]
    enc_dek = am.get("encryptedDek")
    files = am.get("files", [])
    if not enc_dek or not files:
        log("Missing encryptedDek or files", "FAIL")
        return None, None
    download_url = files[0].get("downloadUrl", "")
    return enc_dek, download_url


def api_download(base_url, download_url, token):
    """GET downloadUrl → .aimg1 binary in memory"""
    import requests

    if download_url.startswith("http"):
        url = download_url
    else:
        url = f"{base_url}{download_url}"
    headers = {"Authorization": f"Bearer {token}"}
    log(f"GET {url}", "STEP")
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    if r.status_code != 200:
        log(f"Download HTTP {r.status_code}", "FAIL")
        return None
    return r.content


# ──────────────────── Crypto ────────────────────

def decrypt_dek(encrypted_dek_b64):
    """
    MVP simplification: backend returns plaintext DEK as Base64.
    Simply decode it.
    """
    dek = base64.b64decode(encrypted_dek_b64)
    if len(dek) != 32:
        log(f"WARNING: DEK is {len(dek)} bytes, expected 32", "INFO")
    return dek


def decrypt_aimg1(aimg1_data, dek):
    """
    Decrypt AIMG1 format:
    Header: AIMG(4B) + version(1B) + nonce(12B) + originalSize(8B LE)
    Body: ciphertext + tag(16B)
    Decrypts using AES-256-GCM with DEK and nonce from header.
    """
    from Crypto.Cipher import AES

    # Parse header
    if len(aimg1_data) < 25:  # 4+1+12+8 = 25 bytes minimum header
        raise ValueError(f"AIMG1 data too short: {len(aimg1_data)} bytes")

    magic = aimg1_data[:4]
    if magic != b"AIMG":
        raise ValueError(f"Invalid magic: {magic!r}, expected b'AIMG'")

    version = aimg1_data[4]
    if version != 0x02:
        log(f"WARNING: AIMG version {version}, expected 2", "INFO")

    nonce = aimg1_data[5:17]  # 12 bytes
    original_size = struct.unpack("<Q", aimg1_data[17:25])[0]

    # Ciphertext + tag (the remaining data)
    ciphertext_and_tag = aimg1_data[25:]

    log(f"AIMG1: nonce={nonce.hex()[:16]}..., originalSize={original_size}, "
        f"cipherLen={len(ciphertext_and_tag)}", "INFO")

    # Decrypt with AES-256-GCM
    cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(
        ciphertext_and_tag[:-16],  # ciphertext (without tag)
        ciphertext_and_tag[-16:]   # tag (last 16 bytes)
    )

    if len(plaintext) != original_size:
        log(f"WARNING: Decrypted size {len(plaintext)} != originalSize {original_size}", "INFO")

    return plaintext


# ──────────────────── Display ────────────────────

def show_image_in_window(png_data, title="MVP - In-Memory Decrypted Image"):
    """Display decrypted image in a tkinter window (NOT saved to disk)."""
    from PIL import Image

    img = Image.open(io.BytesIO(png_data))
    log(f"Image decoded: {img.size[0]}x{img.size[1]}, format={img.format}", "OK")

    try:
        import tkinter as tk
        from PIL import ImageTk
    except ImportError:
        log("tkinter not available. Image was successfully decoded in memory.", "OK")
        log("Core concept proven: in-memory decryption works, no data written to disk.", "OK")
        return True

    root = tk.Tk()
    root.title(title)
    root.configure(bg="#1e1e3c")

    # Add info label
    info_text = "🔒 This image was decrypted IN MEMORY — never written to disk"
    info_label = tk.Label(root, text=info_text, fg="#7af5ca", bg="#1e1e3c",
                          font=("Segoe UI", 11))
    info_label.pack(pady=(10, 5))

    # Resize if needed
    max_w, max_h = 800, 600
    w, h = img.size
    if w > max_w or h > max_h:
        ratio = min(max_w / w, max_h / h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    photo = ImageTk.PhotoImage(img)

    canvas = tk.Canvas(root, width=img.size[0], height=img.size[1],
                       bg="#1e1e3c", highlightthickness=0)
    canvas.pack(padx=20, pady=10)
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)

    # Status bar
    status = tk.Label(
        root,
        text=f"✅ Decrypted {len(png_data)} bytes | {img.size[0]}x{img.size[1]} | In-Memory Only",
        fg="#aaaacc", bg="#1e1e3c", font=("Segoe UI", 9)
    )
    status.pack(pady=(0, 10))

    root.geometry(f"{img.size[0] + 40}x{img.size[1] + 80}")
    root.resizable(True, True)

    log("Image window opened. Close window to exit.", "OK")
    root.mainloop()
    return True


# ──────────────────── Main ────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Minimal MVP Client: Login → Auth → Download → In-Memory Decrypt → Display"
    )
    parser.add_argument("--base-url", default=os.environ.get("MVP_BASE_URL", DEFAULT_BASE_URL),
                        help="Backend base URL")
    parser.add_argument("--mod-id", type=int, required=True, help="Mod ID to load")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="Login username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Login password")
    parser.add_argument("--token", default=None, help="Skip login, use this JWT directly")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    print()
    print("=" * 60)
    print("  🔐 Secemumod Demo — Minimal MVP Client")
    print("  Core: In-Memory Decryption, Never Write to Disk")
    print("=" * 60)
    print()

    # Step 1: Login
    token = args.token
    if not token:
        log("Step 1/5: Login...", "STEP")
        token = api_login(base_url, args.username, args.password)
        if not token:
            log("Login failed!", "FAIL")
            return 1
        log(f"Login successful. Token: {token[:20]}...", "OK")
    else:
        log("Step 1/5: Using provided token", "STEP")

    # Step 2: Batch Launch Secure (get encryptedDek + downloadUrl)
    log("Step 2/5: Requesting authorization (batch-launch-secure)...", "STEP")
    enc_dek, download_url = api_batch_launch(base_url, args.mod_id, token)
    if not enc_dek or not download_url:
        log("Authorization failed!", "FAIL")
        return 1
    log(f"Authorized. DEK received, downloadUrl={download_url}", "OK")

    # Step 3: Download .aimg1 to memory (NOT to disk)
    log("Step 3/5: Downloading .aimg1 to memory (not disk!)...", "STEP")
    aimg1_data = api_download(base_url, download_url, token)
    if not aimg1_data:
        log("Download failed!", "FAIL")
        return 1
    log(f"Downloaded {len(aimg1_data)} bytes to memory", "OK")

    # Step 4: In-memory decryption (DEK → AES-GCM → plaintext)
    log("Step 4/5: In-memory decryption...", "STEP")
    try:
        dek = decrypt_dek(enc_dek)
        log(f"DEK decoded: {len(dek)} bytes", "OK")

        plaintext = decrypt_aimg1(aimg1_data, dek)
        log(f"Decrypted! Plaintext: {len(plaintext)} bytes", "OK")
    except Exception as e:
        log(f"Decryption failed: {e}", "FAIL")
        return 1

    # Step 5: Display in window (in-memory, no disk write)
    log("Step 5/5: Displaying decrypted image in window...", "STEP")
    log("⚠️  NO FILE IS WRITTEN TO DISK — plaintext exists only in process memory", "INFO")

    if not show_image_in_window(plaintext, title=f"MVP Demo - Mod {args.mod_id} (In-Memory)"):
        return 1

    print()
    print("=" * 60)
    print("  ✅ MVP Demo Complete!")
    print("  The image was decrypted in memory and displayed.")
    print("  No plaintext file was ever written to disk.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

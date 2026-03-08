#!/usr/bin/env python3
"""Wait for MySQL to accept connections."""
import os
import socket
import sys
import time

host = os.environ.get("DB_HOST", "mysql")
port = int(os.environ.get("DB_PORT", "3306"))
timeout = int(os.environ.get("WAIT_TIMEOUT", "60"))

print(f"Waiting for MySQL at {host}:{port}...")
start = time.time()
while time.time() - start < timeout:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print("MySQL is ready.")
            sys.exit(0)
    except Exception:
        pass
    time.sleep(1)

print("Timeout waiting for MySQL.", file=sys.stderr)
sys.exit(1)

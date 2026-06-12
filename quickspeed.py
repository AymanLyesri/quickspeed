#!/usr/bin/env python3
import datetime
import os
import socket
import subprocess
import time
import urllib.request

# Colors & Config
GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"
TARGET = "google.com"

# Standard browser header to bypass basic Cloudflare bot blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
}


def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def mbps(bytes_per_sec):
    return f"{(bytes_per_sec * 8) / 1000000:.2f} Mbps"


def get_default_gateway():
    try:
        result = subprocess.run(
            ["ip", "route"], capture_output=True, text=True, check=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("default"):
                parts = line.split()
                if "via" in parts:
                    return parts[parts.index("via") + 1]
    except Exception:
        return None
    return None


# ==========================================
# 1. Network Baselines
# ==========================================
gateway = get_default_gateway()

if gateway:
    ping_res = subprocess.run(
        ["ping", "-c", "1", "-W", "1", gateway],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ping_res.returncode == 0:
        log(f"Gateway ({gateway}): {GREEN}OK{NC}")
    else:
        log(f"Gateway ({gateway}): {RED}FAILED{NC}")
else:
    log(f"Gateway: {RED}NOT FOUND{NC}")

try:
    socket.gethostbyname(TARGET)
    log(f"DNS Resolution: {GREEN}OK{NC}")
except socket.gaierror:
    log(f"DNS Resolution: {RED}FAILED{NC}")


# ==========================================
# 2. Speed Test via Cloudflare Edge
# ==========================================
log("Testing real-world bandwidth via Cloudflare...")

# Download 5MB of un-cacheable edge data
url_dl = "https://speed.cloudflare.com/__down?bytes=5000000"
try:
    # Build request with custom User-Agent
    req_dl = urllib.request.Request(url_dl, headers=HEADERS)

    start_time = time.perf_counter()
    with urllib.request.urlopen(req_dl) as response:
        raw_data = response.read()
    end_time = time.perf_counter()

    duration_dl = end_time - start_time
    bytes_dl = len(raw_data)
    sp_dl = bytes_dl / duration_dl if duration_dl > 0 else 0
    log(f"Sustained Download : {GREEN}{mbps(sp_dl)}{NC}")
except Exception as e:
    log(f"Sustained Download : {RED}FAILED ({e}){NC}")

# Upload 1MB of random data
url_ul = "https://speed.cloudflare.com/__up"
upload_data = os.urandom(1 * 1024 * 1024)

try:
    # Build POST request with custom User-Agent and content type
    req_ul = urllib.request.Request(
        url_ul, data=upload_data, method="POST", headers=HEADERS
    )
    req_ul.add_header("Content-Type", "application/octet-stream")

    start_time = time.perf_counter()
    with urllib.request.urlopen(req_ul) as response:
        response.read()
    end_time = time.perf_counter()

    duration_ul = end_time - start_time
    bytes_ul = len(upload_data)
    sp_ul = bytes_ul / duration_ul if duration_ul > 0 else 0
    log(f"Sustained Upload   : {GREEN}{mbps(sp_ul)}{NC}")
except Exception as e:
    log(f"Sustained Upload   : {RED}FAILED ({e}){NC}")

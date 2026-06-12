#!/usr/bin/env python3
import datetime
import io
import os
import socket
import subprocess
import time
import urllib.request

# Colors & Config (Restored original working brackets)
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"  # No Color
TARGET = "google.com"
MAX_TEST_DURATION = 5.0  # Max testing time per phase in seconds

# Standard browser header to bypass basic Cloudflare bot blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
}


def log(message, end="\n"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)


def speed_str(bytes_per_sec):
    """Formats raw bytes per second into both MB/s and Mbps."""
    mbytes_per_sec = bytes_per_sec / (1024 * 1024)
    mbits_per_sec = (bytes_per_sec * 8) / 1000000
    return f"{mbytes_per_sec:.2f} MB/s ({mbits_per_sec:.2f} Mbps)"


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


def show_progress(current_bytes, total_bytes, start_time, prefix="Progress"):
    """Renders a dynamic live-updating progress bar with true speed metrics."""
    elapsed = time.perf_counter() - start_time
    bytes_per_sec = current_bytes / elapsed if elapsed > 0 else 0
    percent = (current_bytes / total_bytes) * 100 if total_bytes > 0 else 0

    # Progress bar layout
    bar_length = 20
    filled_length = (
        int(bar_length * current_bytes // total_bytes) if total_bytes > 0 else 0
    )
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    color = GREEN if current_bytes >= total_bytes else YELLOW
    speed_display = (
        speed_str(bytes_per_sec) if current_bytes > 0 else "0.00 MB/s (0.00 Mbps)"
    )

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"\r[{timestamp}] {prefix:<18}: {color}|{bar}| {percent:3.0f}% ({speed_display}){NC}",
        end="",
        flush=True,
    )


class ProgressUploadWrapper:
    """A file-like object wrapper that updates the progress bar during reads."""

    def __init__(self, data, total_size, start_time, prefix):
        self.data = data
        self.total_size = total_size
        self.start_time = start_time
        self.prefix = prefix
        self.bytes_read = 0

    def read(self, amt=-1):
        # Enforce absolute maximum execution time during upload streaming
        if time.perf_counter() - self.start_time >= MAX_TEST_DURATION:
            raise TimeoutError("Upload time limit reached")

        chunk = self.data.read(amt)
        if chunk:
            self.bytes_read += len(chunk)
            show_progress(
                self.bytes_read, self.total_size, self.start_time, self.prefix
            )
        return chunk

    def __len__(self):
        return self.total_size


# Clear terminal and print header
subprocess.run("clear")

# Credits:
print(f"{BOLD}Quickspeed - Ayman Lyesri (Timed Modification){NC}")

# Initialize results storage
sp_dl = 0
sp_ul = 0

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
print(f"Testing real-world bandwidth via Cloudflare -- {MAX_TEST_DURATION} seconds max")

# Download up to 25MB of un-cacheable edge data
total_dl_bytes = 25000000
url_dl = f"https://speed.cloudflare.com/__down?bytes={total_dl_bytes}"

try:
    req_dl = urllib.request.Request(url_dl, headers=HEADERS)
    raw_data = bytearray()
    chunk_size = 32 * 1024  # 32 KB chunks

    start_time = time.perf_counter()
    with urllib.request.urlopen(req_dl) as response:
        while True:
            # Enforce absolute maximum execution time during download loop
            if time.perf_counter() - start_time >= MAX_TEST_DURATION:
                break

            chunk = response.read(chunk_size)
            if not chunk:
                break
            raw_data.extend(chunk)
            show_progress(
                len(raw_data), total_dl_bytes, start_time, "Sustained Download"
            )

    end_time = time.perf_counter()
    duration_dl = end_time - start_time
    sp_dl = len(raw_data) / duration_dl if duration_dl > 0 else 0

    # Redraw progress bar to perfectly match final chunk length read
    show_progress(len(raw_data), total_dl_bytes, start_time, "Sustained Download")
    print()  # Move to next line

except Exception as e:
    print()
    log(f"Sustained Download : {RED}FAILED ({e}){NC}")

# Upload up to 15MB of random data
total_ul_bytes = 15 * 1024 * 1024
url_ul = "https://speed.cloudflare.com/__up"
upload_raw_bytes = os.urandom(total_ul_bytes)

try:
    bytes_stream = io.BytesIO(upload_raw_bytes)
    start_time = time.perf_counter()
    progress_stream = ProgressUploadWrapper(
        bytes_stream, total_ul_bytes, start_time, "Sustained Upload"
    )

    req_ul = urllib.request.Request(
        url_ul, data=progress_stream, method="POST", headers=HEADERS
    )
    req_ul.add_header("Content-Type", "application/octet-stream")
    req_ul.add_header("Content-Length", str(total_ul_bytes))

    with urllib.request.urlopen(req_ul) as response:
        response.read()

    end_time = time.perf_counter()
    duration_ul = end_time - start_time
    sp_ul = total_ul_bytes / duration_ul if duration_ul > 0 else 0

    show_progress(total_ul_bytes, total_ul_bytes, start_time, "Sustained Upload")
    print()

except Exception as e:
    # Check if the error was our custom stream timeout wrapped by urllib
    if "Upload time limit reached" in str(e):
        end_time = time.perf_counter()
        duration_ul = end_time - start_time
        uploaded_bytes = progress_stream.bytes_read
        sp_ul = uploaded_bytes / duration_ul if duration_ul > 0 else 0

        show_progress(uploaded_bytes, total_ul_bytes, start_time, "Sustained Upload")
        print()
    else:
        print()
        log(f"Sustained Upload   : {RED}FAILED ({e}){NC}")


# ==========================================
# 3. Visual Results Scorecard
# ==========================================
print("\n" + "=" * 54)
print(f"                {BOLD}🚀 NETWORK SPEEDTEST REPORT{NC}               ")
print("=" * 54)

if sp_dl > 0:
    print(f"  📥 {BOLD}Download Speed{NC} : {YELLOW}{speed_str(sp_dl)}{NC}")
else:
    print(f"  📥 {BOLD}Download Speed{NC} : {RED}FAILED TO MEASURE{NC}")

if sp_ul > 0:
    print(f"  📤 {BOLD}Upload Speed{NC}   : {YELLOW}{speed_str(sp_ul)}{NC}")
else:
    print(f"  📤 {BOLD}Upload Speed{NC}   : {RED}FAILED TO MEASURE{NC}")

if sp_dl > 0 and sp_ul > 0:
    # Prompt for adding a star to github project
    github_url = "https://github.com/AymanLyesri/quickspeed"
    print(f"\n  If you found this tool useful, consider giving it a ⭐ on GitHub!")
    print(f"  {YELLOW}👉 {github_url}{NC}")

print("=" * 54)

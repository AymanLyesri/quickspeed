# ⚡ quickspeed

A lightweight, **zero-dependency** network baseline and speed test utility written in pure Python.

Unlike bloated speed test CLI tools, `quickspeed` requires absolutely no package managers, `pip install` commands, or external dependencies. It leverages your system's native tools and Cloudflare's edge network to give you rapid, accurate network diagnostics on any Linux distribution.

---

## ✨ Features

- **Universal Compatibility:** Runs flawlessly on any Linux distribution right out of the box.
- **Zero Dependencies:** Built entirely on Python's standard library (`urllib`, `subprocess`). No `requests` library needed.
- **Smart Diagnostics:** Automatically detects your default gateway, tests local ping latency, and verifies DNS resolution before running the speed test.
- **Real-World Metrics:** Pulls un-cacheable data directly from Cloudflare edge nodes to measure real-world download and upload bandwidth.

---

## 🚀 Quick Start (Run Instantly)

No installation or cloning required.

### Linux / macOS (Bash or Zsh)

```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/AymanLyesri/quickspeed/refs/heads/master/quickspeed.py)
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/AymanLyesri/quickspeed/refs/heads/master/quickspeed.py | python -
```

---

## 💾 Permanent Setup (ZSH Alias)

If you use `zsh` and want to run `quickspeed` anytime without memorizing the URL, you can add it as a permanent shortcut.

1. Open your `.zshrc` file:

```bash
nano ~/.zshrc

```

2. Add the following line at the bottom of the file:

```bash
alias quickspeed="python3 <(curl -fsSL https://raw.githubusercontent.com/AymanLyesri/quickspeed/refs/heads/master/quickspeed.py)"

```

3. Reload your configuration:

```bash
source ~/.zshrc

```

Now, you can test your network anytime by simply typing:

```bash
quickspeed

```

---

## 📊 Sample Output

```text
[2026-06-12 12:44:32] Gateway (192.168.1.1): OK
[2026-06-12 12:44:32] DNS Resolution: OK
[2026-06-12 12:44:32] Testing real-world bandwidth via Cloudflare...
[2026-06-12 12:44:35] Sustained Download : 94.50 Mbps
[2026-06-12 12:44:38] Sustained Upload   : 42.15 Mbps

```

---

## 🛠️ How It Works Under the Hood

1. **Gateway Check:** Parses `ip route` to find your active router and runs a 1-packet ping check.
2. **DNS Check:** Uses Python's native `socket` layer to resolve `google.com`.
3. **Cloudflare Speed Test:** Measures the millisecond transfer time of a 10MB chunk (download) and a 5MB random byte array stream (upload) directly against `speed.cloudflare.com`. It includes custom browser headers to bypass edge firewall blocks smoothly.

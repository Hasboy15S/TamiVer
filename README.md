# Minecraft Server Manager — Complete Setup & Deployment Guide

A production-ready web dashboard that turns any PC/laptop into a one-click Minecraft server with:
- **FastAPI** backend (REST + WebSocket)
- **PaperMC** auto-download
- **Real-time console** via WebSocket
- **Live system metrics** (host + Java process)
- **Glassmorphism dark-mode** frontend (Tailwind CSS)
- **API-key security** on every endpoint

---

## Project Structure

```
my-mc-manager/
├── main.py                  # FastAPI app, routes, WebSocket handlers
├── requirements.txt
├── .env.example             # Template — copy to .env
├── core/
│   ├── __init__.py
│   ├── config.py            # Settings + Java validation
│   ├── server_manager.py    # Subprocess lifecycle, PaperMC download, crash detection
│   ├── system_monitor.py    # psutil host + process metrics
│   └── security.py          # API-key FastAPI dependencies
├── data/
│   └── server/              # Minecraft files (auto-created)
│       └── logs/            # Rotating console logs
└── templates/
    └── index.html           # Dashboard SPA
```

---

## Quick Start (5 minutes)

### 1. Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Java (JDK/JRE) | **Java 21** for MC 1.21+ | [Adoptium](https://adoptium.net/) |
| pip | Any | Comes with Python |

> **Windows**: Add Java to PATH. Run `java -version` in PowerShell to confirm.

### 2. Create a Virtual Environment & Install Dependencies

```bash
# Navigate to the project
cd my-mc-manager

# Create venv
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Activate (Linux/macOS)
source .venv/bin/activate

# Install
pip install -r requirements.txt
```

### 3. Configure Your .env File

```bash
# Windows
copy .env.example .env
# Linux/macOS
cp .env.example .env
```

Open `.env` and set **at minimum** these values:

```dotenv
# Generate a strong key:
# python -c "import secrets; print(secrets.token_hex(32))"
API_KEY=your_64_char_random_hex_here

MC_RAM_MIN=1G
MC_RAM_MAX=4G
```

> **Never start the app without setting API_KEY** — the app refuses to boot with the placeholder value.

### 4. Run the Dashboard

```bash
python main.py
```

Open your browser: **http://localhost:8000**

### 5. First Use

1. **Enter your API key** in the top-right field, click **Save**.
2. Click **Start** — the dashboard will:
   - Check Java installation and version compatibility
   - Download the latest PaperMC jar (if `server.jar` is absent)
   - Write `eula.txt` automatically
   - Create `server.properties` with sensible defaults
   - Spawn the Minecraft process
3. Watch the **Live Console** for the `Done! For help, type "help"` message.
4. Your server is live on **port 25565**.

---

## API Reference

All endpoints require `X-API-Key: <your_key>` header OR `?api_key=<key>` query param.

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Dashboard UI |
| `POST` | `/api/server/start` | Start the server |
| `POST` | `/api/server/stop` | Stop the server gracefully |
| `GET` | `/api/server/status` | Status, PID, uptime |
| `GET` | `/api/server/properties` | Read server.properties |
| `POST` | `/api/server/properties` | Update server.properties |
| `WS` | `/ws/console?api_key=` | Bidirectional console stream |
| `WS` | `/ws/metrics?api_key=` | System metrics every 2s |

---

## LAN Access

To accept connections from other devices on your network, change `.env`:

```dotenv
HOST=0.0.0.0
ALLOWED_ORIGINS=http://192.168.1.X:8000,http://localhost:8000
```

Replace `192.168.1.X` with your machine's LAN IP (`ipconfig` on Windows, `ip addr` on Linux).

### Security implications of `HOST=0.0.0.0`

| Risk | Mitigation |
|---|---|
| Dashboard exposed to all LAN devices | API key required for every request |
| API key leaked = full console access | Use 64-char hex key; never share it |
| Port 8000 visible on LAN | Firewall: allow only trusted IP ranges |

**Never expose port 8000 directly to the public internet** without a reverse proxy (nginx/Caddy) and TLS/HTTPS.

---

## Online Play (Beyond LAN)

### Option A — Ngrok (easiest)

```bash
# Install from https://ngrok.com/download, then:

# Tunnel Minecraft game port
ngrok tcp 25565

# Optionally tunnel the dashboard (separate terminal)
ngrok http 8000
```

Give players the `tcp://X.tcp.ngrok.io:XXXXX` address shown by Ngrok.

> Ngrok free tier rotates URLs on restart. Use Ngrok paid or a static domain for persistence.

### Option B — playit.gg (persistent, free)

1. Download the playit.gg agent from [playit.gg](https://playit.gg).
2. Follow the setup wizard — it assigns a permanent `XXX.joinmc.link` hostname.
3. No router port-forwarding required.

### Updating CORS for remote dashboard access

If you also tunnel the dashboard, add the tunnel URL to `.env`:

```dotenv
ALLOWED_ORIGINS=https://abc123.ngrok.io,http://localhost:8000
```

---

## Running as a Persistent Background Service

The Minecraft process is child of the dashboard. Both survive terminal close when run as a service:

### Windows — NSSM

Download [nssm](https://nssm.cc/):

```powershell
nssm install MCManager "C:\path\to\my-mc-manager\.venv\Scripts\python.exe" "C:\path\to\my-mc-manager\main.py"
nssm set MCManager AppDirectory "C:\path\to\my-mc-manager"
nssm start MCManager
```

### Linux — systemd

```ini
# /etc/systemd/system/mc-manager.service
[Unit]
Description=Minecraft Server Manager
After=network.target

[Service]
Type=simple
User=mcuser
WorkingDirectory=/opt/my-mc-manager
ExecStart=/opt/my-mc-manager/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mc-manager
sudo journalctl -fu mc-manager
```

### Cross-platform — pm2 (Node.js)

```bash
npm install -g pm2
pm2 start "python main.py" --name mc-manager --cwd /path/to/my-mc-manager
pm2 save && pm2 startup
```

---

## Lifecycle Safety

### On Dashboard Shutdown

When the dashboard receives SIGINT/SIGTERM, it **gracefully stops the Minecraft process**:

1. Sends `stop` to the Minecraft STDIN.
2. Waits up to **30 seconds** for the process to exit cleanly.
3. If still alive: escalates to `terminate()` then `kill()`.

**Rationale**: A graceful stop lets Minecraft flush chunk data and player progress to disk, preventing world corruption. The 30s timeout is generous for most worlds. If you prefer to *detach* (keep Minecraft running after the dashboard stops), replace `await server_manager.graceful_shutdown()` in `main.py`'s lifespan with a detach call — but the server then becomes unmanageable from the dashboard until it restarts.

### Preventing Duplicate Processes

A `threading.Lock` is acquired at start with `blocking=False`. Any concurrent `start()` call immediately raises `RuntimeError` → HTTP 409. The status state machine also gates on `Offline`/`Crashed` before proceeding.

---

## Security Notes

### Console Command Authority

The Minecraft console runs with the OS-user permissions of the dashboard process. **Anyone holding the API key can execute any Minecraft command** (op, ban, give, etc.) — this is inherent to the design.

Built-in protections:
- Maximum command length: **256 characters** (reject oversized payloads)
- Empty strings rejected before reaching STDIN
- API key required to open the WebSocket

**Keep your API key private.** Rotate it immediately if compromised (update `.env`, restart service).

### CORS Policy

CORS is explicitly configured to `ALLOWED_ORIGINS` — wildcard is never permitted and will cause an assertion error on startup. Always include your exact browser origin (scheme + host + port).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Java is not found on PATH` | Install JDK 21+ from [Adoptium](https://adoptium.net/); add to PATH |
| `Java X detected, requires Java Y` | Upgrade JDK; verify with `java -version` |
| `API_KEY is not set` | Set a real value in `.env` and restart |
| HTTP 409 on start | Server is already starting/running |
| Jar download fails | Check internet; set `MC_VERSION=1.20.6` in `.env` to try an older version |
| Console shows nothing | Confirm API key is entered in UI; check WS badge |
| Port 25565 already in use | Change `server-port` in the Properties panel then restart |
| CORS error in browser | Add your exact origin to `ALLOWED_ORIGINS` in `.env` |
| Dashboard crashes on startup | Read the terminal output — usually Java or API_KEY misconfiguration |

---

## Rotating Console Logs

Console output streams to `data/server/logs/console.log` with automatic rotation:
- **Max per file**: 10 MB
- **Backup count**: 5 files (`console.log.1` … `console.log.5`)
- **Max total**: ~60 MB

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Dashboard bind address (`0.0.0.0` for LAN) |
| `PORT` | `8000` | Dashboard HTTP/WS port |
| `API_KEY` | *(required)* | Shared secret — all API calls authenticated against this |
| `MC_RAM_MIN` | `1G` | Java `-Xms` (initial heap) |
| `MC_RAM_MAX` | `4G` | Java `-Xmx` (max heap) |
| `MC_SERVER_DIR` | `./data/server` | Directory for all Minecraft files |
| `MC_VERSION` | *(empty = latest)* | Pin a specific MC version e.g. `1.21.1` |
| `ALLOWED_ORIGINS` | `http://localhost:8000` | Comma-separated CORS allowlist |

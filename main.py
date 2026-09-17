"""
main.py
=======
FastAPI application entry-point.

Endpoints
---------
GET  /                          — Serve dashboard UI
POST /api/server/start          — Start Minecraft server
POST /api/server/stop           — Stop Minecraft server
GET  /api/server/status         — Server status + uptime
GET  /api/server/properties     — Read server.properties
POST /api/server/properties     — Update server.properties
WS   /ws/console                — Real-time console I/O
WS   /ws/metrics                — Live system metrics (2s interval)

All /api/* routes and WebSocket connections require a valid API key.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from core.security import require_api_key, verify_ws_key
from core.server_manager import ServerStatus, server_manager
from core.system_monitor import get_snapshot

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: wire the running event loop into ServerManager.
    Shutdown: gracefully stop the Minecraft process before uvicorn exits.

    Decision: we STOP Minecraft on dashboard shutdown to prevent world corruption.
    If you prefer to keep the server running after the dashboard exits, replace
    `graceful_shutdown()` with `server_manager.detach()` and document the PID.
    """
    loop = asyncio.get_running_loop()
    server_manager.set_event_loop(loop)
    logger.info("MC Manager dashboard started.")
    yield
    logger.info("MC Manager shutting down — stopping Minecraft if running…")
    await server_manager.graceful_shutdown()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title="Minecraft Server Manager",
    version="2.0.0",
    description="Web dashboard to manage a Minecraft server",
    lifespan=lifespan,
)

# CORS — never wildcard for LAN/internet deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# UI route
# ---------------------------------------------------------------------------
TEMPLATES_DIR = Path(__file__).parent / "templates"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    html_file = TEMPLATES_DIR / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Server control routes
# ---------------------------------------------------------------------------

@app.post("/api/server/start", dependencies=[Depends(require_api_key)])
async def api_start():
    """Start the Minecraft server. Returns 409 if already running."""
    try:
        await server_manager.start()
        return {"message": "Server start initiated.", "status": server_manager.status}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error starting server: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to start server: {exc}")


@app.post("/api/server/stop", dependencies=[Depends(require_api_key)])
async def api_stop():
    """Stop the Minecraft server gracefully. Returns 409 if already offline."""
    try:
        await server_manager.stop()
        return {"message": "Server stop initiated.", "status": server_manager.status}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error stopping server: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {exc}")


@app.get("/api/server/status", dependencies=[Depends(require_api_key)])
async def api_status():
    """Return current server status, PID, and uptime in seconds."""
    return {
        "status": server_manager.status.value,
        "pid": server_manager.pid,
        "uptime_seconds": server_manager.uptime_seconds,
    }


@app.get("/api/server/properties", dependencies=[Depends(require_api_key)])
async def api_get_properties():
    """Read current server.properties as a key-value dict."""
    return server_manager.read_properties()


@app.post("/api/server/properties", dependencies=[Depends(require_api_key)])
async def api_set_properties(request: Request):
    """
    Update one or more server.properties values.
    The server should be offline; if running, changes will take effect on next restart.
    Body: JSON dict of { "key": "value", ... }
    """
    try:
        updates: dict[str, str] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON.")

    if not isinstance(updates, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object.")

    # Sanitize: values must be strings
    clean: dict[str, str] = {}
    for k, v in updates.items():
        if not isinstance(k, str) or not isinstance(v, (str, int, bool, float)):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid key/value types for '{k}'.",
            )
        clean[str(k)] = str(v)

    running = server_manager.status == ServerStatus.RUNNING
    server_manager.write_properties(clean)

    return {
        "message": "Properties updated."
        + (" Restart the server for changes to take effect." if running else ""),
        "requires_restart": running,
        "updated_keys": list(clean.keys()),
    }


# ---------------------------------------------------------------------------
# WebSocket: console
# ---------------------------------------------------------------------------

@app.websocket("/ws/console")
async def ws_console(
    websocket: WebSocket,
    api_key: str = Query(..., alias="api_key"),
):
    """
    Bidirectional console WebSocket.
    • Server → Client: streamed STDOUT/STDERR lines.
    • Client → Server: commands forwarded to Minecraft STDIN.

    Security: api_key must be passed as a query parameter.
    Command input is validated (max length, non-empty).
    """
    if not await verify_ws_key(websocket, api_key):
        return

    await server_manager.console_manager.connect(websocket)
    await websocket.send_text(
        "[MC Manager] Console connected. Commands are forwarded to the server."
    )

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send a ping-style keepalive
                await websocket.send_text("[MC Manager] keepalive")
                continue

            command = data.strip()
            try:
                await server_manager.send_command(command)
            except ValueError as exc:
                await websocket.send_text(f"[MC Manager] Input error: {exc}")
            except RuntimeError as exc:
                await websocket.send_text(f"[MC Manager] Error: {exc}")

    except Exception:  # noqa: BLE001 – covers disconnect
        pass
    finally:
        await server_manager.console_manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# WebSocket: metrics
# ---------------------------------------------------------------------------

@app.websocket("/ws/metrics")
async def ws_metrics(
    websocket: WebSocket,
    api_key: str = Query(..., alias="api_key"),
):
    """
    Push system metrics every 2 seconds:
    { host: { cpu_percent, ram_used_mb, ram_total_mb, ram_percent },
      java_process: { pid, cpu_percent, rss_mb, status } | null }
    """
    if not await verify_ws_key(websocket, api_key):
        return

    await websocket.accept()

    try:
        while True:
            snapshot = get_snapshot(server_manager.pid)

            payload = {
                "host": dataclasses.asdict(snapshot.host),
                "java_process": (
                    dataclasses.asdict(snapshot.java_process)
                    if snapshot.java_process
                    else None
                ),
                "server_status": server_manager.status.value,
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )

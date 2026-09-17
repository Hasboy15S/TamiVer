"""
core/security.py
================
FastAPI dependencies that enforce API-key authentication for both
REST endpoints and WebSocket connections.

Usage:
    # REST (header or query-param)
    @app.get("/api/...", dependencies=[Depends(require_api_key)])

    # WebSocket (query-param)
    @app.websocket("/ws/...")
    async def ws_endpoint(websocket: WebSocket, key: str = Query(...)):
        await verify_ws_key(websocket, key)
"""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Query, Security, WebSocket, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from core.config import get_settings

logger = logging.getLogger(__name__)

# FastAPI built-in extractors
_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
_query_scheme = APIKeyQuery(name="api_key", auto_error=False)


async def require_api_key(
    header_key: str | None = Security(_header_scheme),
    query_key: str | None = Security(_query_scheme),
) -> str:
    """
    REST dependency: accept the API key from either
      • X-API-Key  header, or
      • ?api_key=  query parameter.
    Returns the validated key on success; raises 401 on failure.
    """
    settings = get_settings()
    provided = header_key or query_key
    if not provided or provided != settings.api_key:
        logger.warning("Rejected request with invalid/missing API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return provided


async def verify_ws_key(websocket: WebSocket, api_key: str) -> bool:
    """
    WebSocket helper: call early in any WS handler.
    Closes the socket with 1008 Policy Violation if the key is wrong.
    Returns True on success so the caller can proceed.
    """
    settings = get_settings()
    if not api_key or api_key != settings.api_key:
        logger.warning("WebSocket connection rejected: invalid API key.")
        await websocket.close(code=1008, reason="Invalid API key.")
        return False
    return True

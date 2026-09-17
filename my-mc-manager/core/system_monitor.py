"""
core/system_monitor.py
======================
Lightweight wrapper around psutil that provides:
  • Host-level CPU and RAM metrics
  • Per-process (Java child) CPU and RSS memory
  • A clean snapshot dataclass
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class HostMetrics:
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    ram_percent: float = 0.0


@dataclass
class ProcessMetrics:
    pid: int = 0
    cpu_percent: float = 0.0
    rss_mb: float = 0.0
    status: str = "unknown"


@dataclass
class SystemSnapshot:
    host: HostMetrics = field(default_factory=HostMetrics)
    java_process: Optional[ProcessMetrics] = None


# ---------------------------------------------------------------------------
# Internal: psutil process cache
# ---------------------------------------------------------------------------
_cached_proc: Optional[psutil.Process] = None
_cached_pid: int = -1


def _get_proc(pid: int) -> Optional[psutil.Process]:
    """Return a cached psutil.Process for the given PID, refreshing if changed."""
    global _cached_proc, _cached_pid
    if pid != _cached_pid or _cached_proc is None:
        try:
            _cached_proc = psutil.Process(pid)
            # Warm up the CPU counter (first call always returns 0.0)
            _cached_proc.cpu_percent(interval=None)
            _cached_pid = pid
        except psutil.NoSuchProcess:
            _cached_proc = None
            _cached_pid = -1
    return _cached_proc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_host_metrics() -> HostMetrics:
    """Return current host CPU and RAM snapshot (non-blocking)."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        return HostMetrics(
            cpu_percent=round(cpu, 1),
            ram_used_mb=round(vm.used / 1024 / 1024, 1),
            ram_total_mb=round(vm.total / 1024 / 1024, 1),
            ram_percent=round(vm.percent, 1),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read host metrics: %s", exc)
        return HostMetrics()


def get_process_metrics(pid: int) -> Optional[ProcessMetrics]:
    """
    Return CPU and RSS for the process with the given PID.
    Returns None if the process no longer exists.
    """
    proc = _get_proc(pid)
    if proc is None:
        return None
    try:
        with proc.oneshot():
            cpu = proc.cpu_percent(interval=None)
            mem_info = proc.memory_info()
            status = proc.status()
        return ProcessMetrics(
            pid=pid,
            cpu_percent=round(cpu, 1),
            rss_mb=round(mem_info.rss / 1024 / 1024, 1),
            status=status,
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        logger.warning("Cannot read metrics for PID %d: %s", pid, exc)
        return None


def get_snapshot(java_pid: Optional[int] = None) -> SystemSnapshot:
    """Return a full system snapshot including optional Java process metrics."""
    host = get_host_metrics()
    java = get_process_metrics(java_pid) if java_pid else None
    return SystemSnapshot(host=host, java_process=java)

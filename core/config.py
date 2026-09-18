"""
core/config.py
==============
Loads configuration from .env, validates Java installation and version,
and exposes a single `settings` object used across the entire app.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Minimum Java versions per Minecraft series
# ---------------------------------------------------------------------------
_MC_JAVA_REQUIREMENTS: dict[str, int] = {
    "1.21": 21,
    "1.20": 17,
    "1.19": 17,
    "1.18": 17,
    "1.17": 16,
}


def _min_java_for_mc(mc_version: str) -> int:
    """Return the minimum Java major version required for a given MC release."""
    # Explicitly support 26.x format (or any non "1.x" format) requiring Java 21
    if mc_version.startswith("26.") or not mc_version.startswith("1."):
        return 21

    for prefix, java_min in _MC_JAVA_REQUIREMENTS.items():
        if mc_version.startswith(prefix):
            # Minecraft 1.20.5 and above requires Java 21
            if prefix == "1.20":
                try:
                    parts = mc_version.split(".")
                    if len(parts) >= 3 and int(parts[2]) >= 5:
                        return 21
                except ValueError:
                    pass
            return java_min
            
    # Default: assume Java 21 for anything newer
    return 21


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class Settings:
    """Single source of truth for all runtime configuration."""

    def __init__(self) -> None:
        self.host: str = os.getenv("HOST", "127.0.0.1")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.api_key: str = os.getenv("API_KEY", "")
        self.mc_ram_min: str = os.getenv("MC_RAM_MIN", "1G")
        self.mc_ram_max: str = os.getenv("MC_RAM_MAX", "4G")
        self.mc_server_dir: Path = Path(os.getenv("MC_SERVER_DIR", "./data/server")).resolve()
        self.mc_version: str = os.getenv("MC_VERSION", "").strip()
        raw_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000")
        self.allowed_origins: list[str] = [o.strip() for o in raw_origins.split(",") if o.strip()]

        # Derived paths
        self.server_jar: Path = self.mc_server_dir / "server.jar"
        self.eula_file: Path = self.mc_server_dir / "eula.txt"
        self.properties_file: Path = self.mc_server_dir / "server.properties"
        self.log_dir: Path = self.mc_server_dir / "logs"

        # Validated at startup
        self.java_executable: str = "java"
        self.java_major_version: int = 0

        self._validate()

    # ------------------------------------------------------------------
    def _validate(self) -> None:
        if not self.api_key or self.api_key == "change_me_to_a_strong_random_secret":
            raise RuntimeError(
                "API_KEY is not set or is still the default placeholder. "
                "Set a strong secret in your .env file."
            )

        # Ensure server directory exists
        self.mc_server_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._validate_java()

    # ------------------------------------------------------------------
    def _validate_java(self) -> None:
        """Detect java, parse its version, and warn if incompatible."""
        java_path = shutil.which("java")
        if not java_path:
            raise RuntimeError(
                "Java is not found on PATH. Install a JDK/JRE and make sure "
                "'java' is accessible from your shell."
            )
        self.java_executable = java_path

        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # java -version writes to stderr
            output = result.stderr or result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timed out trying to run 'java -version'.")
        except OSError as exc:
            raise RuntimeError(f"Failed to execute java: {exc}") from exc

        # Parse major version from strings like:
        #   openjdk version "17.0.12" 2024-07-16
        #   java version "1.8.0_411"
        match = re.search(r'"([\d._]+)"', output)
        if not match:
            raise RuntimeError(f"Could not parse Java version from output:\n{output}")

        version_str = match.group(1)
        parts = version_str.split(".")
        try:
            major = int(parts[1]) if parts[0] == "1" else int(parts[0])
        except (IndexError, ValueError):
            major = 0

        self.java_major_version = major
        logger.info("Detected Java major version: %d (from %s)", major, java_path)

        # Version compatibility check
        target_mc = self.mc_version or "1.21"
        min_java = _min_java_for_mc(target_mc)
        if major < min_java:
            raise RuntimeError(
                f"Java {major} detected, but Minecraft {target_mc} requires "
                f"at minimum Java {min_java}. Please upgrade your JDK/JRE."
            )
        if major < min_java:
            logger.warning(
                "Java %d may be incompatible with Minecraft %s (requires Java >= %d).",
                major,
                target_mc,
                min_java,
            )


def save_env_var(key: str, value: str) -> None:
    """
    Persist a single environment variable to the .env file.

    If the key already exists in the file, its value is updated in-place.
    Otherwise, the key=value pair is appended.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    lines: list[str] = []
    found = False

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped == key:
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Also update the current process environment
    os.environ[key] = value
    logger.info("Persisted %s=%s to .env", key, value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton."""
    return Settings()


def reload_settings() -> Settings:
    """Clear the settings cache, reload .env, and return fresh Settings."""
    load_dotenv(override=True)
    get_settings.cache_clear()
    return get_settings()

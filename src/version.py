"""
Single source of truth for the application version.

Every version surface (FastAPI app, /health, /api, /api/v1/version, data
exports) reads from the canonical VERSION file at the repo root via
``get_app_version()`` — eliminating the hardcoded-literal drift class (WOF-14).
"""

import os
from functools import lru_cache
from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Return the canonical app version, or "unknown" if the VERSION file is absent.

    The version is static for a process lifetime, so the file is read once and
    cached. Tests that patch ``_VERSION_FILE`` must call ``get_app_version.cache_clear()``.
    """
    try:
        return _VERSION_FILE.read_text().strip()
    except FileNotFoundError:
        return "unknown"


def get_app_environment() -> str:
    """Return the deployment environment from ``APP_ENV``, normalized; defaults to "prod".

    The hosted dev stack sets ``APP_ENV=dev`` (WOF-42). It drives the DEV badge in
    the UI and the fail-closed SMS allowlist in ``SMSService``. Not cached, so tests
    can set it per case.
    """
    return os.getenv("APP_ENV", "").strip().lower() or "prod"
